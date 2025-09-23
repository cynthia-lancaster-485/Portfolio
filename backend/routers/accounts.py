from fastapi import APIRouter

from backend.database import accounts as accounts_db
from backend.database import auth as auth_db
from backend.dependencies import DBSession
from backend.models import Account, AccountList, OptionalLogin, User, UpdatePassword
from fastapi import Depends, Form, status, Body
from typing import Annotated

router = APIRouter(prefix="/accounts", tags=["Accounts"])

JWT_COOKIE_KEY = "pony_express_token"

@router.get("", response_model=AccountList)
def get_accounts(session: DBSession):
    return accounts_db.get_all_accounts(session)

@router.put("/me", response_model=User, status_code=status.HTTP_200_OK)
def update_auth_user(session: DBSession, form: OptionalLogin = Body(...) , current_user: dict = Depends(auth_db.get_current_user)) -> User:
   return accounts_db.update_auth_user(session, form, current_user)

@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def update_pass(session: DBSession, form: Annotated[UpdatePassword, Form()], current_user: dict = Depends(auth_db.get_current_user)):
    return accounts_db.update_password(session, form, current_user.id)

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_curr_user(session: DBSession, current_user: dict = Depends(auth_db.get_current_user)):
    return accounts_db.delete_current_user(session, current_user.id)

@router.get("/me", response_model=User, status_code=status.HTTP_200_OK)
def get_auth_user(session: DBSession, current_user: dict = Depends(auth_db.get_current_user)):
    return accounts_db.get_account_by_id(session, current_user.id)

@router.get("/{account_id}", response_model=Account)
def get_account_by_id(session: DBSession, account_id: int):
    return accounts_db.get_account_by_id(session, account_id)



