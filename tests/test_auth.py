def test_protected_pages_redirect_to_login(client):
    for path in ("/dashboard", "/assets", "/assets/new", "/scan", "/history"):
        response = client.get(path)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

def test_login_and_logout(client):
    response = client.post("/login", data={"username": "admin", "password": "admin123"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Asset overview" in response.data
    response = client.post("/logout", follow_redirects=True)
    assert b"TEAM SIGN IN" in response.data
    assert client.get("/dashboard").status_code == 302

def test_invalid_login(client):
    response = client.post("/login", data={"username": "admin", "password": "wrong"})
    assert response.status_code == 200
    assert b"incorrect" in response.data

def test_dashboard_uses_database_counts(signed_in):
    response = signed_in.get("/dashboard")
    assert response.status_code == 200
    assert b"Total assets" in response.data
    assert b"0" in response.data
