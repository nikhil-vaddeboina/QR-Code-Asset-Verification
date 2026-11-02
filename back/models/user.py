from flask_login import UserMixin
from werkzeug.security import check_password_hash
from app import db, login_manager

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(40), nullable=False, default="staff")
    # A nullable JSON column keeps legacy technicians on the safe default access set.
    permissions = db.Column(db.JSON, nullable=True)
    mfa_enabled = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
    mfa_secret_encrypted = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_permission(self, permission):
        from back.features.access.permissions import has_permission
        return has_permission(self, permission)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
