import csv
import io
from flask import Blueprint, current_app, flash, redirect, render_template, request, send_file, url_for
from sqlalchemy.exc import IntegrityError
from app import CATEGORIES, STATUSES, db
from back.models import Asset, AssetRequest, Verification
from back.features.assets.service import allocate_asset_id, next_asset_id, save_asset, search_assets, validate_asset_form
from back.features.assets.qr import create_qr, get_qr
from back.features.access.permissions import permission_required
from back.features.access.permissions import is_administrator
from back.features.team.email_service import send_asset_request_notification
from flask_login import current_user

assets_bp = Blueprint("assets", __name__)

@assets_bp.route("/assets")
@permission_required("view_assets")
def list_assets():
    page = request.args.get("page", 1, type=int)
    items = search_assets(request.args.get("q", ""), request.args.get("status", ""), request.args.get("category", ""), request.args.get("department", "")).paginate(page=page, per_page=10, error_out=False)
    return render_template("assets/list.html", assets=items, q=request.args.get("q", ""), status=request.args.get("status", ""), category=request.args.get("category", ""), department=request.args.get("department", ""))

@assets_bp.route("/assets/new", methods=["GET", "POST"])
@permission_required("add_asset")
def add_asset():
    if request.method == "POST":
        fields, errors = validate_asset_form(request.form)
        if errors:
            for error in errors: flash(error, "error")
            return render_template("assets/add.html", form=request.form, asset_id=next_asset_id())
        if not is_administrator(current_user):
            asset_data = dict(fields)
            asset_data["purchase_date"] = fields["purchase_date"].isoformat()
            pending = AssetRequest(requested_by_id=current_user.id, asset_data=asset_data)
            db.session.add(pending)
            db.session.commit()
            if send_asset_request_notification(pending):
                flash("Your asset request was sent to the administrator for approval.", "success")
            else:
                flash("Your request was saved, but its email notification could not be sent. The administrator can still review it in Asset requests; SMTP settings may need to be configured.", "info")
            return redirect(url_for("dashboard.index"))
        asset = Asset(asset_id=allocate_asset_id())
        try:
            save_asset(asset, fields); create_qr(asset)
        except IntegrityError:
            db.session.rollback(); flash("That serial number is already in use.", "error")
            return render_template("assets/add.html", form=request.form, asset_id=next_asset_id())
        flash(f"{asset.asset_id} added and its QR label is ready.", "success")
        return redirect(url_for("assets.detail", asset_id=asset.asset_id))
    return render_template("assets/add.html", form={}, asset_id=next_asset_id())

@assets_bp.route("/assets/bulk-upload", methods=["GET", "POST"])
@permission_required("bulk_upload")
def bulk_upload():
    if request.method == "GET":
        return render_template("assets/bulk_upload.html")

    upload = request.files.get("file")
    if not upload or not upload.filename:
        flash("Choose a CSV file to upload.", "error")
        return redirect(url_for("assets.bulk_upload"))
    if not upload.filename.lower().endswith(".csv"):
        flash("Upload a .csv file. Use the template on this page to get the right columns.", "error")
        return redirect(url_for("assets.bulk_upload"))

    raw = upload.stream.read(5 * 1024 * 1024 + 1)
    if len(raw) > 5 * 1024 * 1024:
        flash("The CSV is larger than 5 MB. Split it into smaller files and try again.", "error")
        return redirect(url_for("assets.bulk_upload"))
    required_headers = {"name", "category", "serial_number", "department", "location", "assigned_to", "purchase_date", "status", "description"}
    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
        headers = {header.strip() for header in (reader.fieldnames or []) if header}
        if not required_headers.issubset(headers):
            missing = ", ".join(sorted(required_headers - headers))
            flash(f"The CSV is missing required columns: {missing}. Download a fresh template and try again.", "error")
            return redirect(url_for("assets.bulk_upload"))
        reader.fieldnames = [header.strip() if header else header for header in reader.fieldnames]

        prepared, errors, serials, row_count = [], [], set(), 0
        for line_number, row in enumerate(reader, start=2):
            if not row or not any((value or "").strip() for value in row.values() if isinstance(value, str)):
                continue
            row_count += 1
            if row_count > 1000:
                errors.append("The file has more than 1,000 rows. Split it into smaller uploads.")
                break
            cleaned = {key: (row.get(key) or "").strip() for key in required_headers}
            fields, row_errors = validate_asset_form(cleaned)
            serial_key = cleaned["serial_number"].casefold()
            if serial_key and serial_key in serials:
                row_errors.append("Serial number is repeated in this file.")
            if serial_key:
                serials.add(serial_key)
            if row_errors:
                errors.extend([f"Row {line_number}: {message}" for message in row_errors])
            else:
                prepared.append(fields)
        if not prepared and not errors:
            errors.append("The CSV has no asset rows to import.")
        if errors:
            display_errors = errors[:12]
            if len(errors) > len(display_errors):
                display_errors.append(f"And {len(errors) - len(display_errors)} more issue(s). No rows were imported.")
            for message in display_errors:
                flash(message, "error")
            return redirect(url_for("assets.bulk_upload"))
    except (UnicodeDecodeError, csv.Error):
        flash("The file could not be read as a UTF-8 CSV. Save it as CSV UTF-8 and try again.", "error")
        return redirect(url_for("assets.bulk_upload"))

    imported = []
    try:
        for fields in prepared:
            asset = Asset(asset_id=allocate_asset_id())
            for key, value in fields.items():
                setattr(asset, key, value)
            db.session.add(asset)
            imported.append(asset)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("Import stopped because a serial number already exists. No rows were imported; review the file and try again.", "error")
        return redirect(url_for("assets.bulk_upload"))

    qr_failures = 0
    for asset in imported:
        try:
            create_qr(asset)
        except Exception:
            current_app.logger.exception("QR generation failed for bulk-imported asset %s", asset.asset_id)
            qr_failures += 1
    message = f"Imported {len(imported)} assets. Each received an Asset Verify ID."
    if qr_failures:
        message += f" QR labels could not be generated for {qr_failures}; open those assets to retry."
    flash(message, "success" if not qr_failures else "info")
    return redirect(url_for("assets.list_assets"))

@assets_bp.route("/assets/template.csv")
@permission_required("bulk_upload")
def csv_template():
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["name", "category", "serial_number", "department", "location", "assigned_to", "purchase_date", "status", "description"])
    data = io.BytesIO(output.getvalue().encode("utf-8-sig"))
    return send_file(data, mimetype="text/csv", as_attachment=True, download_name="asset-verify-upload-template.csv")

@assets_bp.route("/assets/<asset_id>")
@permission_required("view_assets")
def detail(asset_id):
    asset = Asset.query.filter_by(asset_id=asset_id).first_or_404()
    return render_template("assets/details.html", asset=asset, verifications=asset.verifications.order_by(Verification.verified_at.desc()).limit(10).all())

@assets_bp.route("/assets/<asset_id>/edit", methods=["GET", "POST"])
@permission_required("edit_asset")
def edit(asset_id):
    asset = Asset.query.filter_by(asset_id=asset_id).first_or_404()
    if request.method == "POST":
        fields, errors = validate_asset_form(request.form, asset)
        if errors:
            for error in errors: flash(error, "error")
        else:
            try: save_asset(asset, fields)
            except IntegrityError:
                db.session.rollback(); flash("That serial number is already in use.", "error")
            else:
                flash("Asset details updated.", "success"); return redirect(url_for("assets.detail", asset_id=asset.asset_id))
    return render_template("assets/edit.html", asset=asset)

@assets_bp.route("/assets/<asset_id>/qr")
@permission_required("download_qr")
def qr_download(asset_id):
    asset = Asset.query.filter_by(asset_id=asset_id).first_or_404()
    qr = get_qr(asset)
    return send_file(io.BytesIO(qr.qr_image), mimetype=qr.mime_type, as_attachment=True, download_name=f"{asset.asset_id}-QR.png")

@assets_bp.route("/assets/<asset_id>/qr/image")
@permission_required("view_assets")
def qr_image(asset_id):
    asset = Asset.query.filter_by(asset_id=asset_id).first_or_404()
    qr = get_qr(asset)
    return send_file(io.BytesIO(qr.qr_image), mimetype=qr.mime_type)

@assets_bp.route("/assets/<asset_id>/qr/print")
@permission_required("print_qr")
def qr_print(asset_id):
    asset = Asset.query.filter_by(asset_id=asset_id).first_or_404()
    create_qr(asset)
    return render_template("assets/qr_print.html", asset=asset)
