from backend.database.schema import DBChat, DBAccount
from backend.database import auth as db_auth
from backend.database import bcrypt as db_bcrypt

def hash_password_stub(password: str) -> str:
    return f"hashed_{password}"

def verify_password_stub(password: str, hashed_password: str) -> bool:
    return hash_password_stub(password) == hashed_password


def test_get_accounts(session, client):
    aaron = DBAccount(username='aaron', email='aaron@example.com', hashed_password='aaronpass')
    ted = DBAccount(username='ted', email='ted@example.com', hashed_password='tedpass')

    session.add_all([aaron, ted])
    session.commit()

    response = client.get("/accounts")
    assert response.status_code == 200
    assert response.json()["metadata"]["count"] == 2
    assert response.json()["accounts"] == [
        {"id": 1, "username": "aaron"},
        {"id": 2, "username": "ted"},
    ]

def test_get_account_1(session, client):
    account = DBAccount(username='aaron', email='aaron@example.com', hashed_password='aaronpass')
    session.add(account)
    session.commit()

    response = client.get(f"/accounts/{account.id}")
    assert response.status_code == 200
    assert response.json() == {"id": account.id, "username": "aaron"}

def test_get_nonexsistent_account(session, client):
    response = client.get(f"/accounts/100")
    assert response.status_code == 404
    assert response.json() == {
        "error": "entity_not_found",
        "message": "Unable to find account with id=100"
    }

def test_get_me_expired_bearer_token(client, monkeypatch, session):
    monkeypatch.setattr(db_auth, "DURATION", -600)

    password = "hashpass"
    hashed_password = db_bcrypt.hash_password(password)
    aaron = DBAccount(username="aaronw", email="aaron@mail.com", hashed_password=hashed_password)
    session.add(aaron)
    session.commit()

    login_data = {
        "username": "aaronw",
        "password": password
    }

    token_resp = client.post("/auth/token", data=login_data)
    assert token_resp.status_code == 200
    token = token_resp.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"

    response = client.get("/accounts/me")
    assert response.status_code == 403
    assert response.json() == {
        "error": "expired_access_token",
        'message': 'Authentication failed: expired access token'
    }

def test_get_me_invlaid_bearer_token(client, monkeypatch, session):
    monkeypatch.setattr(db_auth, "DURATION", -600)

    password = "hashpass"
    hashed_password = db_bcrypt.hash_password(password)
    aaron = DBAccount(username="aaronw", email="aaron@mail.com", hashed_password=hashed_password)
    session.add(aaron)
    session.commit()

    login_data = {
        "username": "aaronw",
        "password": password
    }

    token_resp = client.post("/auth/token", data=login_data)
    assert token_resp.status_code == 200
    token = token_resp.json()["access_token"]
    bad_token = token + "garbage"
    client.headers["Authorization"] = f"Bearer {bad_token}"

    response = client.get("/accounts/me")
    assert response.status_code == 403
    assert response.json() == {
        "error": "invalid_access_token",
        'message': 'Authentication failed: invalid access token'
    }

def test_get_account_me(client, session):
    password = "hashpass"
    hashed_password = db_bcrypt.hash_password(password)
    aaron = DBAccount(username="aaronw", email="aaron@mail.com", hashed_password=hashed_password)
    session.add(aaron)
    session.commit()

    login_data = {
        "username": "aaronw",
        "password": password
    }

    token_resp = client.post("/auth/token", data=login_data)
    assert token_resp.status_code == 200
    token = token_resp.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"

    response = client.get("/accounts/me")
    assert response.status_code == 200

def test_put_account_me(client, session):
    password = "hashpass"
    hashed_password = db_bcrypt.hash_password(password)
    aaron = DBAccount(username="aaronw", email="aaron@mail.com", hashed_password=hashed_password)
    session.add(aaron)
    session.commit()

    login_data = {
        "username": "aaronw",
        "password": password
    }

    token_resp = client.post("/auth/token", data=login_data)
    assert token_resp.status_code == 200
    token = token_resp.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"

    update_data = {
        "username": "newusername",
        "email": "newemail@mail.com"
    }

    response = client.put("/accounts/me", json=update_data)
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "username": "newusername",
        "email": "newemail@mail.com"
    }

    updated_user = session.query(DBAccount).filter(DBAccount.id == 1).first()
    assert updated_user.username == "newusername"
    assert updated_user.email == "newemail@mail.com"


def test_put_account_me_pass(client, session):
    password = "hashpass"
    hashed_password = db_bcrypt.hash_password(password)
    aaron = DBAccount(username="aaronw", email="aaron@mail.com", hashed_password=hashed_password)
    session.add(aaron)
    session.commit()

    login_data = {
        "username": "aaronw",
        "password": password
    }

    token_resp = client.post("/auth/token", data=login_data)
    assert token_resp.status_code == 200
    token = token_resp.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"

    update_data = {
        "old_password": "hashpass",
        "new_password": "newpass"
    }

    response = client.put("/accounts/me/password", data=update_data)
    assert response.status_code == 204

    updated_user = session.query(DBAccount).filter(DBAccount.id == 1).first()
    assert db_bcrypt.verify_password("newpass", updated_user.hashed_password)

def test_delete_account_me(client, session):
    password = "hashpass"
    hashed_password = db_bcrypt.hash_password(password)
    aaron = DBAccount(username="aaronw", email="aaron@mail.com", hashed_password=hashed_password)
    session.add(aaron)
    session.commit()

    login_data = {
        "username": "aaronw",
        "password": password
    }

    token_resp = client.post("/auth/token", data=login_data)
    assert token_resp.status_code == 200
    token = token_resp.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"

    response = client.delete("/accounts/me")
    assert response.status_code == 204

    deleted_user = session.query(DBAccount).filter(DBAccount.username == "aaronw").first()
    assert deleted_user is None