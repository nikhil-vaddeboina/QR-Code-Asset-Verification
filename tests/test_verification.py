from back.models import Asset, Verification

def test_qr_lookup_and_unknown_asset(signed_in, asset_payload):
    signed_in.post("/assets/new", data=asset_payload)
    response = signed_in.get("/lookup/AST-0001")
    assert response.status_code == 200
    assert response.json["serial_number"] == "TEST-0001"
    assert signed_in.get("/lookup/AST-9999").status_code == 404

def test_verification_updates_status_and_history(signed_in, asset_payload, app):
    signed_in.post("/assets/new", data=asset_payload)
    response = signed_in.post("/verify/AST-0001", data={"result": "Damaged", "remarks": "Screen cracked"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Verification saved" in response.data
    with app.app_context():
        asset = Asset.query.filter_by(asset_id="AST-0001").one()
        assert asset.status == "Damaged"
        row = Verification.query.one()
        assert row.remarks == "Screen cracked"
    assert b"Screen cracked" in signed_in.get("/history").data

def test_invalid_verification_result_rejected(signed_in, asset_payload, app):
    signed_in.post("/assets/new", data=asset_payload)
    response = signed_in.post("/verify/AST-0001", data={"result": "Invented", "remarks": ""})
    assert b"valid verification result" in response.data
    with app.app_context(): assert Verification.query.count() == 0
