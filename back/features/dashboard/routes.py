from datetime import datetime, timedelta
from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import func
from app import db, STATUSES
from back.models import Asset, AssetRequest, Verification
from back.features.access.permissions import has_permission, is_administrator
from flask_login import current_user

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
@login_required
def index():
    can_view_assets = has_permission(current_user, "view_assets")
    can_view_history = has_permission(current_user, "view_history")
    counts = {s: Asset.query.filter_by(status=s).count() for s in STATUSES} if can_view_assets else {s: 0 for s in STATUSES}
    total = Asset.query.count() if can_view_assets else 0
    start = datetime.utcnow() - timedelta(days=6)
    daily = db.session.query(func.date(Verification.verified_at), func.count(Verification.id)).filter(Verification.verified_at >= start).group_by(func.date(Verification.verified_at)).all() if can_view_history else []
    daily_map = {str(d): c for d, c in daily}
    labels = [(datetime.utcnow().date() - timedelta(days=i)).strftime("%a") for i in range(6, -1, -1)]
    keys = [str(datetime.utcnow().date() - timedelta(days=i)) for i in range(6, -1, -1)]
    recent_assets = Asset.query.order_by(Asset.created_at.desc()).limit(6).all() if can_view_assets else []
    recent_verifications = Verification.query.order_by(Verification.verified_at.desc()).limit(6).all() if can_view_history else []
    pending_asset_requests = AssetRequest.query.filter_by(status="Pending").count() if is_administrator(current_user) else 0
    return render_template("dashboard/index.html", counts=counts, total=total, recent_assets=recent_assets, recent_verifications=recent_verifications, status_labels=STATUSES, status_values=[counts[s] for s in STATUSES], activity_labels=labels, activity_values=[daily_map.get(k, 0) for k in keys], pending_asset_requests=pending_asset_requests)
