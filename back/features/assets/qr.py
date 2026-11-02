from datetime import datetime
from io import BytesIO
from flask import url_for
import qrcode
from app import db
from back.models import AssetQRCode

def render_qr_png(asset, base_url=None):
    target = base_url or url_for("verification.lookup", asset_id=asset.asset_id, _external=True)
    image = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4)
    image.add_data(target)
    image.make(fit=True)
    output = BytesIO()
    image.make_image(fill_color="#111827", back_color="white").save(output, format="PNG")
    return output.getvalue()

def create_qr(asset, base_url=None):
    """Create and persist an asset's QR PNG in the database."""
    if asset.id is None:
        db.session.flush()
    record = AssetQRCode.query.filter_by(asset_pk=asset.id).first()
    image_bytes = render_qr_png(asset, base_url)
    if record is None:
        record = AssetQRCode(asset_pk=asset.id, qr_image=image_bytes, mime_type="image/png")
        db.session.add(record)
    else:
        record.qr_image = image_bytes
        record.mime_type = "image/png"
        record.generated_at = datetime.utcnow()
    db.session.commit()
    return record

def get_qr(asset):
    """Return the stored QR image, generating it if this asset has none yet."""
    record = AssetQRCode.query.filter_by(asset_pk=asset.id).first()
    return record or create_qr(asset)
