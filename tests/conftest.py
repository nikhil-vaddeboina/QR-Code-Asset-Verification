import pytest
from cryptography.fernet import Fernet
from werkzeug.security import generate_password_hash
from app import create_app, db
from back.models import User

@pytest.fixture
def app(tmp_path):
    application = create_app({"TESTING": True, "SECRET_KEY": "test-secret", "MFA_ENCRYPTION_KEY": Fernet.generate_key().decode("ascii"), "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}", "QR_FOLDER": str(tmp_path / "qr")})
    with application.app_context():
        db.create_all()
        db.session.add(User(username="admin", password_hash=generate_password_hash("admin123"), role="administrator"))
        db.session.commit()
        yield application
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def signed_in(client):
    client.post("/login", data={"username": "admin", "password": "admin123"})
    return client

@pytest.fixture
def asset_payload():
    return {"name": "Dell Latitude 5440", "category": "Computers", "serial_number": "TEST-0001", "department": "Computer Science", "location": "Block A · 101", "assigned_to": "Aarav Mehta", "purchase_date": "2024-03-10", "status": "Active", "description": "Test laptop"}
