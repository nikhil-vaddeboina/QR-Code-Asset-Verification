import base64
from io import BytesIO

import pyotp
import qrcode
from cryptography.fernet import Fernet, InvalidToken
from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import generate_password_hash
from back.models import User
from app import db

auth_bp = Blueprint("auth", __name__)


def _mfa_fernet():
    key = current_app.config.get("MFA_ENCRYPTION_KEY")
    if not key:
        raise RuntimeError("MFA_ENCRYPTION_KEY is missing from the project .env file.")
    try:
        return Fernet(key.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as exc:
        raise RuntimeError("MFA_ENCRYPTION_KEY is not a valid Fernet key.") from exc


def _user_totp_secret(user):
    if not user.mfa_secret_encrypted:
        return None
    try:
        return _mfa_fernet().decrypt(user.mfa_secret_encrypted.encode("ascii")).decode("ascii")
    except (InvalidToken, UnicodeEncodeError):
        current_app.logger.exception("Could not decrypt MFA secret for user %s", user.id)
        return None


def _valid_next_url(candidate):
    return candidate.startswith("/") and not candidate.startswith("//")


def _password_is_valid(password):
    return len(password) >= 12


@auth_bp.route("/account/password", methods=["GET", "POST"])
@login_required
def change_password():
    if not current_user.mfa_enabled:
        flash("Set up multi-factor authentication before changing your password.", "info")
        return redirect(url_for("auth.mfa_setup"))

    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        code = "".join(request.form.get("code", "").split())
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")
        secret = _user_totp_secret(current_user)

        if not current_user.check_password(current_password):
            flash("Your current password was not accepted.", "error")
        elif not _password_is_valid(new_password):
            flash("Choose a password with at least 12 characters.", "error")
        elif new_password != confirm_password:
            flash("The new password and confirmation do not match.", "error")
        elif not (len(code) == 6 and code.isdigit() and secret and pyotp.TOTP(secret).verify(code)):
            flash("After confirming your new password, enter the current six-digit code from your authenticator app.", "error")
        else:
            current_user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            logout_user()
            session.clear()
            flash("Your password was changed. Sign in again with your new password and authenticator code.", "success")
            return redirect(url_for("auth.login"))

    return render_template("authentication/change_password.html")


@auth_bp.route("/password-reset", methods=["GET", "POST"])
def password_reset():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        code = "".join(request.form.get("code", "").split())
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")
        user = User.query.filter_by(username=username).first() if username else None
        secret = _user_totp_secret(user) if user and user.mfa_enabled else None

        # Keep the response generic so the page does not disclose whether a username exists.
        if (user and secret and len(code) == 6 and code.isdigit()
                and pyotp.TOTP(secret).verify(code)
                and _password_is_valid(new_password)
                and new_password == confirm_password):
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            flash("If the account details were valid, the password has been reset. Sign in with your new password and authenticator code.", "success")
        else:
            flash("If the account has MFA enabled and the details were valid, the password has been reset. Otherwise contact your administrator.", "info")
        return redirect(url_for("auth.login"))

    return render_template("authentication/password_reset.html")

@auth_bp.route("/", methods=["GET"])
def index():
    return redirect(url_for("dashboard.index" if current_user.is_authenticated else "auth.login"))

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated: return redirect(url_for("dashboard.index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(request.form.get("password", "")):
            if user.mfa_enabled:
                session.clear()
                session["pending_mfa_user_id"] = user.id
                session["pending_mfa_remember"] = request.form.get("remember") == "on"
                next_url = request.args.get("next", "")
                if _valid_next_url(next_url):
                    session["pending_mfa_next"] = next_url
                return redirect(url_for("auth.mfa_verify"))
            login_user(user, remember=request.form.get("remember") == "on")
            next_url = request.args.get("next", "")
            if _valid_next_url(next_url): return redirect(next_url)
            return redirect(url_for("dashboard.index"))
        flash("The username or password you entered is incorrect.", "error")
    return render_template("authentication/login.html")


@auth_bp.route("/mfa/setup", methods=["GET", "POST"])
@login_required
def mfa_setup():
    if current_user.mfa_enabled:
        flash("Multi-factor authentication is already enabled for your account.", "info")
        return redirect(url_for("dashboard.index"))

    try:
        cipher = _mfa_fernet()
    except RuntimeError as exc:
        current_app.logger.error("MFA setup is unavailable: %s", exc)
        flash("MFA setup is unavailable. Check the MFA key in the project .env file, then restart the app.", "error")
        return redirect(url_for("dashboard.index"))

    secret = _user_totp_secret(current_user)
    if not secret:
        secret = pyotp.random_base32()
        current_user.mfa_secret_encrypted = cipher.encrypt(secret.encode("ascii")).decode("ascii")
        db.session.commit()

    if request.method == "POST":
        code = "".join(request.form.get("code", "").split())
        if pyotp.TOTP(secret).verify(code):
            current_user.mfa_enabled = True
            db.session.commit()
            flash("MFA is enabled. You will need an authenticator code the next time you sign in.", "success")
            return redirect(url_for("dashboard.index"))
        flash("That code was not accepted. Check the authenticator app and try the current six-digit code.", "error")

    provisioning_uri = pyotp.TOTP(secret).provisioning_uri(name=current_user.username, issuer_name="Asset Verify")
    qr = qrcode.make(provisioning_uri)
    image_buffer = BytesIO()
    qr.save(image_buffer, format="PNG")
    qr_data = base64.b64encode(image_buffer.getvalue()).decode("ascii")
    return render_template("authentication/mfa_setup.html", qr_data=qr_data, secret=secret)


@auth_bp.route("/mfa/verify", methods=["GET", "POST"])
def mfa_verify():
    user_id = session.get("pending_mfa_user_id")
    user = db.session.get(User, user_id) if user_id else None
    if not user or not user.mfa_enabled:
        session.pop("pending_mfa_user_id", None)
        session.pop("pending_mfa_remember", None)
        session.pop("pending_mfa_next", None)
        flash("Sign in with your username and password first.", "info")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        code = "".join(request.form.get("code", "").split())
        secret = _user_totp_secret(user)
        if secret and pyotp.TOTP(secret).verify(code):
            remember = session.pop("pending_mfa_remember", False)
            next_url = session.pop("pending_mfa_next", "")
            session.pop("pending_mfa_user_id", None)
            login_user(user, remember=remember)
            return redirect(next_url if _valid_next_url(next_url) else url_for("dashboard.index"))
        flash("That code was not accepted. Check your authenticator app and try again.", "error")

    return render_template("authentication/mfa_verify.html")

@auth_bp.route("/logout", methods=["POST"])
def logout():
    logout_user()
    flash("You have been signed out.", "success")
    return redirect(url_for("auth.login"))
