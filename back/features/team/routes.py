import re
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from app import db
from back.models import Asset, AssetRequest, User
from back.features.assets.qr import create_qr
from back.features.assets.service import allocate_asset_id, validate_asset_form
from back.features.team.email_service import send_asset_request_notification
from back.features.access.permissions import (
    DEFAULT_TECHNICIAN_PERMISSIONS,
    PERMISSION_LABELS,
    admin_required,
    normalize_permissions,
    permissions_for,
)

team_bp = Blueprint("team", __name__)
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9._-]{3,80}$")
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


@team_bp.route("/team", methods=["GET", "POST"])
@admin_required
def index():
    selected_permissions = set(DEFAULT_TECHNICIAN_PERMISSIONS)
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        selected_permissions = set(request.form.getlist("permissions"))
        invalid_permissions = selected_permissions - set(PERMISSION_LABELS)

        if not USERNAME_PATTERN.fullmatch(username):
            flash("Use a username of 3–80 characters: letters, numbers, dots, underscores, or hyphens.", "error")
        elif not EMAIL_PATTERN.fullmatch(email):
            flash("Enter a valid technician email address.", "error")
        elif len(password) < 12:
            flash("Set an initial password with at least 12 characters.", "error")
        elif invalid_permissions:
            flash("One or more selected access options are not valid.", "error")
        elif User.query.filter(db.func.lower(User.username) == username.lower()).first():
            flash("That username is already in use.", "error")
        elif User.query.filter(db.func.lower(User.email) == email).first():
            flash("That email address is already assigned to an account.", "error")
        else:
            technician = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                role="technician",
                permissions=sorted(normalize_permissions(selected_permissions)),
            )
            db.session.add(technician)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash("That username or email address is already in use.", "error")
            else:
                flash(f"Technician account '{username}' was created. Share the initial password privately.", "success")
                return redirect(url_for("team.index"))

    technicians = User.query.filter(db.func.lower(User.role) == "technician").order_by(User.username.asc()).all()
    technician_permissions = {technician.id: permissions_for(technician) for technician in technicians}
    return render_template(
        "team/index.html",
        technicians=technicians,
        permission_options=PERMISSION_LABELS,
        default_permissions=DEFAULT_TECHNICIAN_PERMISSIONS,
        selected_permissions=selected_permissions,
        technician_permissions=technician_permissions,
    )


@team_bp.route("/team/asset-requests")
@admin_required
def asset_requests():
    requests = AssetRequest.query.order_by(AssetRequest.created_at.desc()).all()
    return render_template("team/asset_requests.html", asset_requests=requests)


@team_bp.route("/team/asset-requests/<int:request_id>/approve", methods=["POST"])
@admin_required
def approve_asset_request(request_id):
    item = db.session.get(AssetRequest, request_id)
    if not item or item.status != "Pending":
        flash("That pending asset request could not be found.", "error")
        return redirect(url_for("team.asset_requests"))

    fields, errors = validate_asset_form(item.asset_data)
    if errors:
        flash("This request can’t be approved until it is corrected: " + " ".join(errors), "error")
        return redirect(url_for("team.asset_requests"))
    asset = Asset(asset_id=allocate_asset_id())
    for key, value in fields.items():
        setattr(asset, key, value)
    item.status = "Approved"
    item.admin_note = request.form.get("admin_note", "").strip()[:500]
    item.reviewed_at = datetime.utcnow()
    db.session.add(asset)
    try:
        db.session.commit()
        create_qr(asset)
    except IntegrityError:
        db.session.rollback()
        flash("The asset was not created because its serial number already exists. Review the request first.", "error")
        return redirect(url_for("team.asset_requests"))
    flash(f"Request approved. Asset {asset.asset_id} was created with its QR code.", "success")
    return redirect(url_for("team.asset_requests"))


@team_bp.route("/team/asset-requests/<int:request_id>/reject", methods=["POST"])
@admin_required
def reject_asset_request(request_id):
    item = db.session.get(AssetRequest, request_id)
    if not item or item.status != "Pending":
        flash("That pending asset request could not be found.", "error")
        return redirect(url_for("team.asset_requests"))
    item.status = "Rejected"
    item.admin_note = request.form.get("admin_note", "").strip()[:500]
    item.reviewed_at = datetime.utcnow()
    db.session.commit()
    flash("Asset request rejected.", "success")
    return redirect(url_for("team.asset_requests"))


@team_bp.route("/team/<int:user_id>/permissions", methods=["POST"])
@admin_required
def update_technician_permissions(user_id):
    technician = db.session.get(User, user_id)
    if not technician or (technician.role or "").strip().lower() != "technician":
        flash("That technician account could not be found.", "error")
        return redirect(url_for("team.index"))

    selected = set(request.form.getlist("permissions"))
    if selected - set(PERMISSION_LABELS):
        flash("One or more selected access options are not valid.", "error")
    else:
        technician.permissions = sorted(normalize_permissions(selected))
        db.session.commit()
        flash(f"Access updated for technician '{technician.username}'.", "success")
    return redirect(url_for("team.index"))


@team_bp.route("/team/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_technician(user_id):
    technician = db.session.get(User, user_id)
    if not technician or (technician.role or "").strip().lower() != "technician":
        flash("That technician account could not be found.", "error")
        return redirect(url_for("team.index"))

    username = technician.username
    db.session.delete(technician)
    db.session.commit()
    flash(f"Technician account '{username}' was deleted.", "success")
    return redirect(url_for("team.index"))
