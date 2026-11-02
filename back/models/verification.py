from datetime import datetime
from app import db

class Verification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey("asset.id", ondelete="CASCADE"), nullable=False, index=True)
    result = db.Column(db.String(40), nullable=False, index=True)
    remarks = db.Column(db.String(500), default="")
    evidence_image = db.Column(db.LargeBinary, nullable=True)
    evidence_mime_type = db.Column(db.String(40), nullable=True)
    verified_by = db.Column(db.String(80), nullable=False)
    verified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    asset = db.relationship("Asset", back_populates="verifications")
