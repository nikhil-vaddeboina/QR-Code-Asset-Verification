import io

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user
from PIL import Image, UnidentifiedImageError
from app import RESULTS
from back.models import Asset
from back.features.verification.service import record_verification
from back.features.access.permissions import permission_required

verification_bp = Blueprint("verification", __name__)

@verification_bp.route("/scan")
@permission_required("scan_verify")
def scan():
    return render_template("verification/scan.html")

@verification_bp.route("/verify/<asset_id>", methods=["GET", "POST"])
@permission_required("scan_verify")
def verify(asset_id):
    asset = Asset.query.filter_by(asset_id=asset_id).first_or_404()
    if request.method == "POST":
        result = request.form.get("result", "")
        remarks = request.form.get("remarks", "").strip()
        evidence_file = request.files.get("evidence")
        evidence_bytes = None
        evidence_mime = None
        errors = []
        if result not in RESULTS: errors.append("Choose a valid verification result.")
        if len(remarks) > 500: errors.append("Remarks must be 500 characters or fewer.")
        requires_evidence = result in {"Damaged", "Under Repair"}
        if requires_evidence and (not evidence_file or not evidence_file.filename):
            errors.append("Attach a photo when marking an asset damaged or under repair.")
        elif evidence_file and evidence_file.filename:
            raw = evidence_file.stream.read(5 * 1024 * 1024 + 1)
            if len(raw) > 5 * 1024 * 1024:
                errors.append("The evidence image must be 5 MB or smaller.")
            else:
                try:
                    image = Image.open(io.BytesIO(raw))
                    image_format = (image.format or "").upper()
                    if image_format not in {"JPEG", "PNG", "WEBP"}:
                        errors.append("Use a JPEG, PNG, or WebP image for evidence.")
                    elif image.width * image.height > 40_000_000:
                        errors.append("The evidence image dimensions are too large. Choose a smaller photo.")
                    else:
                        image.verify()
                        evidence_bytes = raw
                        evidence_mime = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}[image_format]
                except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
                    errors.append("The selected evidence file is not a valid image.")
        if errors:
            for error in errors: flash(error, "error")
        else:
            record = record_verification(asset, result, remarks, current_user.username, evidence_bytes, evidence_mime)
            flash("Verification recorded successfully.", "success")
            return render_template("verification/result.html", asset=asset, record=record)
    return render_template("verification/verify.html", asset=asset, results=RESULTS, selected_result=request.form.get("result", "Verified"))

@verification_bp.route("/lookup/<asset_id>")
@permission_required("scan_verify")
def lookup(asset_id):
    asset = Asset.query.filter_by(asset_id=asset_id).first()
    if not asset: return jsonify({"error": "No asset matches this QR code."}), 404
    return jsonify({"asset_id": asset.asset_id, "name": asset.name, "category": asset.category, "serial_number": asset.serial_number, "department": asset.department, "location": asset.location, "assigned_to": asset.assigned_to, "status": asset.status, "url": url_for("verification.verify", asset_id=asset.asset_id)})
