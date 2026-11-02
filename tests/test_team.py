from werkzeug.security import generate_password_hash

from back.models import Asset, User
from app import db


def test_admin_can_open_team_page_and_sees_navigation(signed_in):
    dashboard = signed_in.get("/dashboard")
    team_page = signed_in.get("/team")

    assert dashboard.status_code == 200
    assert b"Technicians" in dashboard.data
    assert team_page.status_code == 200
    assert b"Add a technician" in team_page.data


def test_admin_can_create_and_delete_technician(signed_in, app):
    response = signed_in.post(
        "/team",
        data={"username": "field.tech", "password": "a-long-test-password", "permissions": ["view_assets", "scan_verify", "view_history", "download_qr"]},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"field.tech" in response.data

    with app.app_context():
        technician = User.query.filter_by(username="field.tech").one()
        technician_id = technician.id
        assert technician.role == "technician"
        assert set(technician.permissions) == {"view_assets", "scan_verify", "view_history", "download_qr"}
        assert technician.check_password("a-long-test-password")
        assert technician.password_hash != "a-long-test-password"

    response = signed_in.post(f"/team/{technician_id}/delete", follow_redirects=True)
    assert response.status_code == 200
    assert b"No technician accounts yet" in response.data
    with app.app_context():
        assert db.session.get(User, technician_id) is None


def test_admin_rejects_invalid_technician_credentials(signed_in, app):
    response = signed_in.post(
        "/team",
        data={"username": "bad name", "password": "short"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Use a username" in response.data
    with app.app_context():
        assert User.query.filter_by(username="bad name").first() is None


def test_admin_can_assign_and_update_technician_permissions(signed_in, app):
    response = signed_in.post(
        "/team",
        data={"username": "limited.tech", "password": "a-long-test-password", "permissions": ["view_assets", "scan_verify"]},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"limited.tech" in response.data

    with app.app_context():
        technician = User.query.filter_by(username="limited.tech").one()
        technician_id = technician.id
        assert set(technician.permissions) == {"view_assets", "scan_verify"}

    response = signed_in.post(
        f"/team/{technician_id}/permissions",
        data={"permissions": ["view_assets", "view_history"]},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Access updated" in response.data
    with app.app_context():
        technician = db.session.get(User, technician_id)
        assert set(technician.permissions) == {"view_assets", "view_history"}


def test_technician_has_limited_access(client, app):
    with app.app_context():
        technician = User(
            username="field.tech",
            password_hash=generate_password_hash("a-long-test-password"),
            role="technician",
        )
        db.session.add(technician)
        db.session.commit()

    response = client.post(
        "/login",
        data={"username": "field.tech", "password": "a-long-test-password"},
    )
    assert response.status_code == 302

    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200
    assert b"Technicians" not in dashboard.data
    assert client.get("/assets").status_code == 200
    assert client.get("/scan").status_code == 200
    assert client.get("/history").status_code == 200

    assert client.get("/team").status_code == 403
    assert client.post(
        "/team",
        data={"username": "another.tech", "password": "a-long-test-password"},
    ).status_code == 403
    assert client.post("/team/1/delete").status_code == 403
    assert client.get("/assets/new").status_code == 403
    assert client.get("/assets/bulk-upload").status_code == 403
    assert client.get("/assets/template.csv").status_code == 403
    assert client.post("/assets/AST-0001/delete").status_code == 403

    with app.app_context():
        assert User.query.filter_by(username="another.tech").first() is None
        assert Asset.query.count() == 0


def test_technician_permissions_are_enforced_for_pages_and_actions(client, app):
    with app.app_context():
        technician = User(
            username="view-only.tech",
            password_hash=generate_password_hash("a-long-test-password"),
            role="technician",
            permissions=["view_assets"],
        )
        db.session.add(technician)
        db.session.commit()

    client.post("/login", data={"username": "view-only.tech", "password": "a-long-test-password"})
    assert client.get("/dashboard").status_code == 200
    dashboard = client.get("/dashboard")
    assert b"Assets" in dashboard.data
    assert b"Scan &amp; verify" not in dashboard.data
    assert client.get("/assets").status_code == 200
    assert client.get("/scan").status_code == 403
    assert client.get("/history").status_code == 403
    assert client.get("/assets/new").status_code == 403
    assert client.get("/assets/bulk-upload").status_code == 403
    assert client.get("/assets/template.csv").status_code == 403
    assert client.post("/team").status_code == 403
