from datetime import datetime
from app import db

class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.String(24), unique=True, nullable=False, index=True)
    name = db.Column(db.String(140), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    serial_number = db.Column(db.String(100), unique=True, nullable=False, index=True)
    department = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(140), nullable=False)
    assigned_to = db.Column(db.String(120), nullable=False)
    purchase_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(40), nullable=False, default="Active", index=True)
    description = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    verifications = db.relationship("Verification", back_populates="asset", cascade="all, delete-orphan", lazy="dynamic")
    qr_code = db.relationship("AssetQRCode", back_populates="asset", cascade="all, delete-orphan", uselist=False)

    @property
    def qr_filename(self):
        return f"{self.asset_id}.png"

class AssetSequence(db.Model):
    """Persistent ID counter so deleting an asset never recycles its label."""
    id = db.Column(db.Integer, primary_key=True)
    next_value = db.Column(db.Integer, nullable=False, default=1)


class AssetQRCode(db.Model):
    """PNG QR image stored in MySQL and linked one-to-one to an asset."""
    __tablename__ = "asset_qr_codes"

    id = db.Column(db.Integer, primary_key=True)
    asset_pk = db.Column(db.Integer, db.ForeignKey("asset.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    qr_image = db.Column(db.LargeBinary, nullable=False)
    mime_type = db.Column(db.String(40), nullable=False, default="image/png")
    generated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    asset = db.relationship("Asset", back_populates="qr_code")
