import pyotp
from cryptography.fernet import Fernet
from werkzeug.security import generate_password_hash

from app import db
from back.models import User


def add_mfa_user(app, username="tech"):
    secret = pyotp.random_base32()
    with app.app_context():
        encrypted = Fernet(app.config["MFA_ENCRYPTION_KEY"].encode("ascii")).encrypt(secret.encode("ascii")).decode("ascii")
        user = User(username=username, password_hash=generate_password_hash("old-password-123"), role="technician", mfa_enabled=True, mfa_secret_encrypted=encrypted)
        db.session.add(user)
        db.session.commit()
    return secret


def sign_in_with_mfa(client, username, password, secret):
    response = client.post("/login", data={"username": username, "password": password})
    assert response.status_code == 302
    response = client.post("/mfa/verify", data={"code": pyotp.TOTP(secret).now()})
    assert response.status_code == 302


def test_technician_can_change_password_with_password_and_totp(app, client):
    secret = add_mfa_user(app)
    sign_in_with_mfa(client, "tech", "old-password-123", secret)

    response = client.post("/account/password", data={
        "current_password": "old-password-123",
        "code": pyotp.TOTP(secret).now(),
        "new_password": "new-password-456",
        "confirm_password": "new-password-456",
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"password was changed" in response.data
    assert b"TEAM SIGN IN" in response.data
    with app.app_context():
        user = User.query.filter_by(username="tech").one()
        assert user.check_password("new-password-456")


def test_password_change_rejects_invalid_otp(app, client):
    secret = add_mfa_user(app)
    sign_in_with_mfa(client, "tech", "old-password-123", secret)

    response = client.post("/account/password", data={
        "current_password": "old-password-123",
        "code": "000000",
        "new_password": "new-password-456",
        "confirm_password": "new-password-456",
    })

    assert response.status_code == 200
    with app.app_context():
        assert User.query.filter_by(username="tech").one().check_password("old-password-123")


def test_forgotten_password_reset_requires_totp(app, client):
    secret = add_mfa_user(app)

    response = client.post("/password-reset", data={
        "username": "tech",
        "code": pyotp.TOTP(secret).now(),
        "new_password": "reset-password-789",
        "confirm_password": "reset-password-789",
    }, follow_redirects=True)

    assert response.status_code == 200
    with app.app_context():
        assert User.query.filter_by(username="tech").one().check_password("reset-password-789")


def test_forgotten_password_reset_rejects_bad_code(app, client):
    add_mfa_user(app)

    client.post("/password-reset", data={
        "username": "tech",
        "code": "000000",
        "new_password": "reset-password-789",
        "confirm_password": "reset-password-789",
    })

    with app.app_context():
        assert User.query.filter_by(username="tech").one().check_password("old-password-123")


def test_password_reset_for_account_without_mfa_does_not_change_password(app, client):
    with app.app_context():
        db.session.add(User(username="no-mfa", password_hash=generate_password_hash("old-password-123"), role="technician"))
        db.session.commit()

    client.post("/password-reset", data={
        "username": "no-mfa",
        "code": "123456",
        "new_password": "reset-password-789",
        "confirm_password": "reset-password-789",
    })

    with app.app_context():
        assert User.query.filter_by(username="no-mfa").one().check_password("old-password-123")


def test_legacy_password_hash_command_hashes_plaintext_and_keeps_hashes(app):
    with app.app_context():
        db.session.add_all([
            User(username="legacy-user", password_hash="legacy-plain-password", role="technician"),
            User(username="hashed-user", password_hash=generate_password_hash("already-hashed-password"), role="administrator"),
        ])
        db.session.commit()

    result = app.test_cli_runner().invoke(args=["hash-legacy-passwords"])

    assert result.exit_code == 0, result.output
    assert "Hashed 1 legacy password(s)" in result.output
    assert "2 were already hashed" in result.output
    with app.app_context():
        legacy = User.query.filter_by(username="legacy-user").one()
        existing = User.query.filter_by(username="hashed-user").one()
        assert legacy.password_hash != "legacy-plain-password"
        assert legacy.check_password("legacy-plain-password")
        assert existing.check_password("already-hashed-password")
