import csv
import io
from datetime import date, datetime, timedelta

from flask import Blueprint, abort, flash, render_template, request, send_file, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from app import RESULTS
from back.features.access.permissions import has_permission, permission_required
from back.models import Asset, Verification

history_bp = Blueprint("history", __name__)
PAGE_SIZES = (10, 15, 25, 50, 100)


def report_dates(period, start_value, end_value):
    today = date.today()
    start_date = end_date = None
    if period == "weekly":
        start_date, end_date = today - timedelta(days=6), today
    elif period == "monthly":
        start_date, end_date = today.replace(day=1), today
    elif period == "yearly":
        start_date, end_date = today.replace(month=1, day=1), today
    elif period == "custom":
        try:
            start_date = date.fromisoformat(start_value) if start_value else None
            end_date = date.fromisoformat(end_value) if end_value else None
        except ValueError:
            return None, None, "Enter valid dates for the report range."
        if start_date and end_date and start_date > end_date:
            return None, None, "The start date must be before the end date."
    else:
        period = "all"
    return start_date, end_date, None


def filtered_history_query(q, result, start_date, end_date):
    query = Verification.query.join(Asset)
    if q:
        term = f"%{q}%"
        query = query.filter(or_(Asset.asset_id.ilike(term), Asset.name.ilike(term), Verification.verified_by.ilike(term), Verification.remarks.ilike(term)))
    if result:
        query = query.filter(Verification.result == result)
    if start_date:
        query = query.filter(Verification.verified_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(Verification.verified_at < datetime.combine(end_date + timedelta(days=1), datetime.min.time()))
    return query


@history_bp.route("/history")
@permission_required("view_history")
def index():
    q = request.args.get("q", "").strip()
    result = request.args.get("result", "")
    period = request.args.get("period", "all")
    if period not in {"all", "weekly", "monthly", "yearly", "custom"}:
        period = "all"
    start_date, end_date, date_error = report_dates(period, request.args.get("start_date", ""), request.args.get("end_date", ""))
    if date_error:
        flash(date_error, "error")
        period, start_date, end_date = "all", None, None
    if result and result not in RESULTS:
        result = ""
    page_size = request.args.get("per_page", 15, type=int)
    if page_size not in PAGE_SIZES:
        page_size = 15
    query = filtered_history_query(q, result, start_date, end_date)

    if request.args.get("export") == "csv":
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(["Asset ID", "Asset name", "Result", "Remarks", "Verified by", "Verified at", "Evidence image"])
        for row in query.order_by(Verification.verified_at.desc()).all():
            writer.writerow([row.asset.asset_id, row.asset.name, row.result, row.remarks or "", row.verified_by, row.verified_at.isoformat(sep=" "), "Yes" if row.evidence_image else "No"])
        filename = f"asset-verification-{period}-{date.today().isoformat()}.csv"
        return send_file(io.BytesIO(output.getvalue().encode("utf-8-sig")), mimetype="text/csv; charset=utf-8", as_attachment=True, download_name=filename)

    items = query.order_by(Verification.verified_at.desc()).paginate(page=request.args.get("page", 1, type=int), per_page=page_size, error_out=False)
    return render_template(
        "history/index.html", records=items, q=q, selected_result=result, results=RESULTS,
        period=period, start_date=start_date.isoformat() if start_date else "",
        end_date=end_date.isoformat() if end_date else "", page_sizes=PAGE_SIZES, per_page=page_size,
    )


@history_bp.route("/history/<int:verification_id>/evidence")
@login_required
def evidence(verification_id):
    if not has_permission(current_user, "view_history") and not has_permission(current_user, "scan_verify"):
        abort(403)
    row = Verification.query.get_or_404(verification_id)
    if not row.evidence_image:
        abort(404)
    return send_file(io.BytesIO(row.evidence_image), mimetype=row.evidence_mime_type or "image/jpeg", download_name=f"{row.asset.asset_id}-verification-evidence.jpg")
