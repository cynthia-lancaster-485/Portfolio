import bcrypt
from fastapi import Depends, FastAPI, Form
from sqlmodel import Session, select
from backend.database.schema import DBAccount
from backend.dependencies import DBSession
from backend.exceptions import InvalidCredentials
from backend.models import Registration, User, Claims
from jose import jwt

app = FastAPI()



def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
          bcrypt.gensalt()
          ).decode("utf-8")

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )

def get_verified_user(session: Session, username: str, password: str) -> DBAccount:
    stmt = select(DBAccount).where(DBAccount.username == username)
    user = session.exec(stmt).one_or_none()
    if user is not None and verify_password(password, user.hashed_password):
        return user
    raise InvalidCredentials()

def register_user(session: DBSession, registration: Registration) -> User:
    hashed_password = hash_password(registration.password)
    user = DBAccount(**registration.model_dump(), hashed_password=hashed_password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return User(id=user.id, username=user.username, email=user.email)

def validate_credentials(user: DBAccount | None, password: str) -> DBAccount:
    if user is None or not verify_password(password, user.hashed_password):
        raise InvalidCredentials()
    return user



