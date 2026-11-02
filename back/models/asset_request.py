from datetime import datetime
from app import db


class AssetRequest(db.Model):
    """Asset submitted by a technician and awaiting administrator approval."""
    id = db.Column(db.Integer, primary_key=True)
    requested_by_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    requested_by = db.relationship("User")
    asset_data = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Pending", index=True)
    admin_note = db.Column(db.String(500), nullable=False, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
