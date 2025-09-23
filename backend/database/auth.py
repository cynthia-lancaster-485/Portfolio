from sqlmodel import Session, select
from typing import Annotated
from backend.database import bcrypt as db_bcrypt
from backend.database import accounts as db_accounts
from backend.dependencies import DBSession, get_session
from backend.database.schema import DBAccount
from backend.models import Registration, AccessToken, Claims, Login
from backend.exceptions import DuplicateEntityValue, ExpiredAccessToken, InvalidAccessToken, InvalidCredentials, AuthenticationRequired
from fastapi import Form, Depends
from jose import jwt
from jose.exceptions import ExpiredSignatureError
from datetime import datetime, timezone
from fastapi.security import APIKeyCookie, HTTPBearer, HTTPAuthorizationCredentials

from dotenv import load_dotenv
import os

load_dotenv()
JWT_KEY = os.getenv("JWT_SECRET_KEY")

JWT_ALG = "HS256"
JWT_ISS = "http://127.0.0.1"
JWT_OPTS = {"require_sub": True, "require_iss": True, "require_exp": True}
DURATION = 3600
JWT_COOKIE_KEY = "pony_express_token"

    
cookie_scheme = APIKeyCookie(name=JWT_COOKIE_KEY, auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


def create_user(session: Session, form: Annotated[Registration, Form()]) -> dict:
    """Creates a user in the database

    Args:
        session (Session): The database session
        form (Form): The registration form 

    Returns:
        dict: id, username, and email of the new account

    Raises:
       Duplicate Entity Value: If the username matches the username of an existing account
       Duplicate Entity Value: If email matches the email of an existing account
    """

    "Check to see if username already exists"
    astmt = select(DBAccount).filter(DBAccount.username == form.username).order_by(DBAccount.id)
    account_exists = session.exec(astmt).one_or_none()
    estmt = select(DBAccount).filter(DBAccount.email == form.email).order_by(DBAccount.id)
    email_exists = session.exec(estmt).one_or_none()

    if account_exists:
        raise DuplicateEntityValue(account_exists.username, "username", "account")
    
    if email_exists:
        raise DuplicateEntityValue(email_exists.email, "email", "account")

    if not (account_exists and email_exists):
        new_user = db_bcrypt.register_user(session, form)
    
    return new_user

def generate_token(session: Session, form: Login) -> str:
    """Creates a login token

    Args:
        session (Session): The database session
        form (Form): The registration form 

    Returns:
        str: cookie string

    Raises:
       Invalid Credentials: If username does not correspond to an account in the database
       Invalid Credentials: If password does not match the account's hashed password
    """
    stmt = select(DBAccount).where(DBAccount.username == form.username)
    account = session.exec(stmt).one_or_none()
    if not account:
        raise InvalidCredentials()
    
    user = db_bcrypt.validate_credentials(account, form.password)
    if not user:
        raise InvalidCredentials()

    claims = generate_claims(user)
    return jwt.encode(
        claims.model_dump(),
        JWT_KEY,
        algorithm=JWT_ALG
    )

def generate_claims(user: DBAccount) -> Claims:
    iat = int(datetime.now(timezone.utc).timestamp())
    exp = iat + DURATION
    return Claims(
        sub=str(user.id),
        iss=JWT_ISS,
        iat=iat,
        exp=exp
    )

def encode(claims: Claims) -> str:
    return jwt.encode(claims.model_dump(), JWT_KEY, JWT_ALG)

def decode(token: str) -> Claims:
    return jwt.decode(
        token,
        JWT_KEY, 
        algorithms=[JWT_ALG], 
        issuer=JWT_ISS, 
        options=JWT_OPTS,
    )

def extract_user(session: Session, token: str) -> DBAccount:
    try:
        payload = jwt.decode(
            token,
            JWT_KEY,
            algorithms=[JWT_ALG],
            options=JWT_OPTS
        )
        claims = Claims(**payload)
        return db_accounts.get_account_by_id(session, int(claims.sub))
    
    except ExpiredSignatureError:
        raise ExpiredAccessToken()
    
    except Exception:
        raise InvalidAccessToken()


def get_access_token(
        cookie_token: str | None = Depends(cookie_scheme),
        bearer_token: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)
    ) -> str:
    if cookie_token is not None: 
        return cookie_token
    elif bearer_token is not None:
        return bearer_token.credentials
    else: 
        raise AuthenticationRequired()
    

def get_current_user(
        session: Session = Depends(get_session),
        token: str = Depends(get_access_token),
    ) -> DBAccount:
    return extract_user(session, token)
