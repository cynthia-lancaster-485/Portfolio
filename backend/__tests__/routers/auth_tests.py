from backend.database.schema import DBAccount
from backend.database import bcrypt as db_bcrypt
import os
from datetime import datetime, timezone
from jose import jwt

JWT_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALG = "HS256"
JWT_ISS = "http://127.0.0.1"
JWT_OPTS = {"require_sub": True, "require_iss": True, "require_exp": True}
DURATION = 3600
JWT_COOKIE_KEY = "pony_express_token"


def test_register_new_user(session, client):
    user_data = {
        "username": "aaronw",
        "email": "aaron@mail.com",
        "password": "aaronpass"
    }

    response = client.post("/auth/registration", data=user_data)

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "username": "aaronw",
        "email": "aaron@mail.com"
    }

def test_create_token(session, client):
    password = "hashpass"
    hashed_password = db_bcrypt.hash_password(password)
    aaron = DBAccount(username="aaronw", email="aaron@mail.com", hashed_password=hashed_password)
    session.add(aaron)
    session.commit()

    login_data = {
        "username": "aaronw",
        "password": password
    }

    response = client.post("/auth/token", data=login_data)
    assert response.status_code == 200
    "We could check for a little more here. if we have time"

def test_web_login(session, client):
    password = "hashpass"
    hashed_password = db_bcrypt.hash_password(password)
    aaron = DBAccount(username="aaronw", email="aaron@mail.com", hashed_password=hashed_password)
    session.add(aaron)
    session.commit()

    login_data = {
        "username": "aaronw",
        "password": password
    }

    response = client.post("/auth/web/login", data=login_data)
    assert response.status_code == 204
    "We could check for a little more here. if we have time"

def test_web_logout(session, client):
    password = "hashpass"
    hashed_password = db_bcrypt.hash_password(password)
    aaron = DBAccount(username="aaronw", email="aaron@mail.com", hashed_password=hashed_password)
    session.add(aaron)
    session.commit()

    login_data = {
        "username": "aaronw",
        "password": password
    }

    response1 = client.post("/auth/web/login", data=login_data)
    assert response1.status_code == 204
    response = client.post("/auth/web/logout")
    assert response.status_code == 204

def test_auth_req(session, client):
    password = "hashpass"
    hashed_password = db_bcrypt.hash_password(password)
    aaron = DBAccount(username="aaronw", email="aaron@mail.com", hashed_password=hashed_password)
    session.add(aaron)
    session.commit()

    login_data = {
        "username": "aaronw",
        "password": password
    }

    response1 = client.post("/auth/web/login", data=login_data)
    assert response1.status_code == 204

    response = client.post("/auth/web/logout")
    assert response.status_code == 204
    assert response.cookies.get(JWT_COOKIE_KEY) is None

    response2 = client.get("/accounts/me")
    assert response2.status_code == 403
    assert response.json() == {
        "error": "authentication_required",
        'message': 'Not authenticated'
    }
