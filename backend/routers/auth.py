from fastapi import APIRouter
import bcrypt
from fastapi import Depends, Form, status, Response
from fastapi.responses import JSONResponse
from typing import Annotated
from backend.database import auth as auth_db
from backend.database.schema import DBChat
from backend.dependencies import DBSession
from backend.models import User, Registration, NewToken, AccessToken, Login
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/auth", tags=["Auth"])

JWT_COOKIE_KEY = "pony_express_token"

@router.post("/registration", status_code=status.HTTP_201_CREATED, response_model=User)
def register_new_user(session: DBSession, form: Annotated[Registration, Form()]) -> User:
    return auth_db.create_user(session, form)

@router.post("/token", status_code=status.HTTP_200_OK, response_model=AccessToken)
def create_access_token(session: DBSession, form: Annotated[Login, Form()]) -> AccessToken:
    token = auth_db.generate_token(session, form)
    return AccessToken(access_token=token, token_type="bearer")

@router.post("/web/login", status_code=status.HTTP_204_NO_CONTENT)
def login(session: DBSession, response: Response, form: Annotated[Login, Form()]):
    token = auth_db.generate_token(session, form)
    response.set_cookie(JWT_COOKIE_KEY, token, httponly=True)

@router.post("/web/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response, current_user: dict = Depends(auth_db.get_current_user)):
    response.delete_cookie(JWT_COOKIE_KEY)
