from datetime import date, datetime, timedelta
import random
from app import db
from back.models import Asset, Verification
from back.features.assets.qr import create_qr

NAMES = ["Latitude 5440 Laptop", "ThinkCentre M70 Desktop", "Epson EB-E01 Projector", "Cisco Catalyst Switch", "OptiPlex 7010 Workstation", "Ergonomic Office Chair", "Dell P2422H Monitor", "Fluke Digital Multimeter", "Canon ImageRunner Printer", "HP ProBook 450 Laptop"]
PEOPLE = ["Aarav Mehta", "Diya Nair", "Kabir Shah", "Mira Iyer", "Rohan Das", "Ananya Rao", "Ishaan Gupta", "Sara Khan", "Dev Patel", "Nisha Menon", "Arjun Bose", "Tara Sen"]
RESULT_CYCLE = ["Verified", "Verified", "Verified", "Damaged", "Under Repair", "Missing", "Transferred"]

def seed_demo_data(app):
    from app import CATEGORIES, DEPARTMENTS, LOCATIONS
    if Asset.query.count() >= 100 and Verification.query.count() >= 180:
        for asset in Asset.query.all():
            if asset.qr_code is None:
                with app.test_request_context(): create_qr(asset)
        return
    random.seed(71)
    made = []
    statuses = ["Active", "Active", "Active", "Verified", "Damaged", "Missing", "Under Repair", "Transferred", "Retired"]
    for n in range(1, 101):
        asset = Asset(asset_id=f"AST-{n:04d}", name=f"{NAMES[(n-1) % len(NAMES)]}{' · ' + str((n-1)//10+1) if n > 10 else ''}", category=CATEGORIES[(n-1) % len(CATEGORIES)], serial_number=f"COL-{2022 + n % 5}-{n:05d}", department=DEPARTMENTS[(n-1) % len(DEPARTMENTS)], location=LOCATIONS[(n-1) % len(LOCATIONS)], assigned_to=PEOPLE[(n-1) % len(PEOPLE)], purchase_date=date(2021 + n % 5, (n % 12) + 1, min((n % 27) + 1, 28)), status=statuses[(n-1) % len(statuses)], description="College-owned equipment maintained by the campus facilities team.", created_at=datetime.utcnow() - timedelta(days=100-n))
        db.session.add(asset); made.append(asset)
    db.session.commit()
    for idx in range(180):
        asset = made[(idx * 17 + idx // 7) % len(made)]
        result = RESULT_CYCLE[(idx * 3 + idx // 11) % len(RESULT_CYCLE)]
        db.session.add(Verification(asset=asset, result=result, remarks=["Physical label and serial number matched.", "Checked during scheduled department audit.", "Condition recorded by facilities staff.", "Location confirmed with department coordinator."][idx % 4], verified_by=PEOPLE[idx % len(PEOPLE)], verified_at=datetime.utcnow() - timedelta(days=(idx * 2) % 180, hours=idx % 24)))
    db.session.commit()
    with app.test_request_context():
        for asset in made: create_qr(asset)
