from app import db
from back.models import Verification

def record_verification(asset, result, remarks, username, evidence_image=None, evidence_mime_type=None):
    record = Verification(asset=asset, result=result, remarks=remarks.strip(), verified_by=username, evidence_image=evidence_image, evidence_mime_type=evidence_mime_type)
    asset.status = result
    db.session.add(record)
    db.session.commit()
    return record
