from datetime import date
from sqlalchemy import or_
from app import db
from back.models import Asset, AssetSequence

def next_asset_id():
    existing = db.session.query(Asset.asset_id).all()
    sequence = [int(value[0][4:]) for value in existing if value[0].startswith("AST-") and value[0][4:].isdigit()]
    counter = db.session.get(AssetSequence, 1)
    next_value = max(max(sequence, default=0) + 1, counter.next_value if counter else 1)
    return f"AST-{next_value:04d}"

def allocate_asset_id():
    existing = db.session.query(Asset.asset_id).all()
    sequence = [int(value[0][4:]) for value in existing if value[0].startswith("AST-") and value[0][4:].isdigit()]
    counter = db.session.get(AssetSequence, 1)
    if counter is None:
        counter = AssetSequence(id=1, next_value=max(sequence, default=0) + 1)
        db.session.add(counter)
        db.session.flush()
    value = max(max(sequence, default=0) + 1, counter.next_value)
    counter.next_value = value + 1
    db.session.flush()
    return f"AST-{value:04d}"

def search_assets(search="", status="", category="", department=""):
    query = Asset.query
    if search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(or_(Asset.asset_id.ilike(term), Asset.name.ilike(term), Asset.serial_number.ilike(term), Asset.location.ilike(term), Asset.department.ilike(term)))
    if status:
        query = query.filter_by(status=status)
    if category:
        query = query.filter_by(category=category)
    if department:
        query = query.filter_by(department=department)
    return query.order_by(Asset.created_at.desc(), Asset.id.desc())

def validate_asset_form(form, asset=None):
    fields = {key: (form.get(key) or "").strip() for key in ("name", "category", "serial_number", "department", "location", "assigned_to", "purchase_date", "status", "description")}
    errors = []
    for key, label in (("name", "Asset name"), ("category", "Category"), ("serial_number", "Serial number"), ("department", "Department"), ("location", "Location"), ("purchase_date", "Purchase date"), ("status", "Status")):
        if not fields[key]: errors.append(f"{label} is required.")
    if fields["status"] == "Retired":
        if fields["assigned_to"] and fields["assigned_to"].casefold() != "unassigned":
            errors.append("Retired assets cannot be assigned to a person or team. Set the assignee to Unassigned.")
        fields["assigned_to"] = "Unassigned"
    elif not fields["assigned_to"]:
        errors.append("Assigned to is required for an asset that is not retired.")
    if fields["category"] and fields["category"] not in ["Computers", "Furniture", "Laboratory", "Networking", "Audio Visual", "Vehicles", "Office Equipment"]: errors.append("Select a valid category.")
    if fields["status"] and fields["status"] not in ["Active", "Verified", "Damaged", "Missing", "Under Repair", "Transferred", "Retired"]: errors.append("Select a valid status.")
    try:
        fields["purchase_date"] = date.fromisoformat(fields["purchase_date"])
        if fields["purchase_date"] > date.today(): errors.append("Purchase date cannot be in the future.")
    except ValueError:
        if fields["purchase_date"]: errors.append("Enter a valid purchase date.")
    duplicate = Asset.query.filter_by(serial_number=fields["serial_number"])
    if asset: duplicate = duplicate.filter(Asset.id != asset.id)
    if fields["serial_number"] and duplicate.first(): errors.append("That serial number is already assigned to another asset.")
    return fields, errors

def save_asset(asset, fields):
    for key, value in fields.items(): setattr(asset, key, value)
    db.session.add(asset)
    db.session.commit()
    return asset
