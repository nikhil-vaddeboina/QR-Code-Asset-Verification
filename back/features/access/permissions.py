from functools import wraps

from flask import abort
from flask_login import current_user, login_required

PERMISSION_LABELS = {
    "view_assets": "View asset register and details",
    "add_asset": "Add assets",
    "edit_asset": "Edit asset details",
    "bulk_upload": "Bulk upload assets",
    "scan_verify": "Scan QR codes and record verifications",
    "view_history": "View verification history",
    "download_qr": "Download QR labels",
    "print_qr": "Print QR labels",
}
DEFAULT_TECHNICIAN_PERMISSIONS = frozenset({
    "view_assets", "scan_verify", "view_history", "download_qr",
})
ASSET_CONTEXT_PERMISSIONS = frozenset({
    "add_asset", "edit_asset", "bulk_upload",
    "scan_verify", "download_qr", "print_qr",
})


def is_administrator(user):
    return bool(user.is_authenticated and (user.role or "").strip().lower() in {"admin", "administrator"})


def permissions_for(user):
    if not user or not getattr(user, "is_authenticated", False):
        return set()
    if is_administrator(user):
        return set(PERMISSION_LABELS)
    stored = getattr(user, "permissions", None)
    if stored is None:
        return set(DEFAULT_TECHNICIAN_PERMISSIONS)
    return {permission for permission in stored if permission in PERMISSION_LABELS}


def has_permission(user, permission):
    return is_administrator(user) or permission in permissions_for(user)


def normalize_permissions(permissions):
    selected = {permission for permission in permissions if permission in PERMISSION_LABELS}
    if selected & ASSET_CONTEXT_PERMISSIONS:
        selected.add("view_assets")
    return selected


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not is_administrator(current_user):
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def permission_required(permission):
    def decorate(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if not has_permission(current_user, permission):
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorate
