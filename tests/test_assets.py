from back.models import Asset, AssetQRCode, db

def test_add_asset_and_generate_qr(signed_in, asset_payload, app):
    response = signed_in.post("/assets/new", data=asset_payload, follow_redirects=True)
    assert response.status_code == 200
    assert b"AST-0001" in response.data
    with app.app_context():
        asset = Asset.query.filter_by(asset_id="AST-0001").one()
        qr = AssetQRCode.query.filter_by(asset_pk=asset.id).one()
        assert qr.mime_type == "image/png"
        assert qr.qr_image.startswith(b"\x89PNG\r\n\x1a\n")

def test_duplicate_serial_rejected(signed_in, asset_payload):
    signed_in.post("/assets/new", data=asset_payload)
    duplicate = dict(asset_payload, name="Second item")
    response = signed_in.post("/assets/new", data=duplicate)
    assert b"already assigned" in response.data

def test_edit_delete_asset(signed_in, asset_payload):
    signed_in.post("/assets/new", data=asset_payload)
    updated = dict(asset_payload, name="Updated laptop")
    response = signed_in.post("/assets/AST-0001/edit", data=updated, follow_redirects=True)
    assert b"Updated laptop" in response.data
    signed_in.post("/assets/AST-0001/delete")
    assert b"AST-0001" not in signed_in.get("/assets").data

def test_search_and_pagination(signed_in, asset_payload):
    signed_in.post("/assets/new", data=asset_payload)
    assert b"Dell Latitude" in signed_in.get("/assets?q=Latitude").data
    assert b"No matching assets" in signed_in.get("/assets?q=not-a-match").data

def test_invalid_asset_form_does_not_save(signed_in, asset_payload, app):
    payload = dict(asset_payload, purchase_date="tomorrow")
    response = signed_in.post("/assets/new", data=payload)
    assert b"valid purchase date" in response.data
    with app.app_context(): assert Asset.query.count() == 0

def test_deleted_asset_id_is_not_reused(signed_in, asset_payload):
    signed_in.post("/assets/new", data=asset_payload)
    signed_in.post("/assets/AST-0001/delete")
    next_item = dict(asset_payload, serial_number="TEST-0002")
    response = signed_in.post("/assets/new", data=next_item, follow_redirects=True)
    assert b"AST-0002" in response.data
