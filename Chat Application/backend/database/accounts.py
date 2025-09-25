from sqlmodel import Session, select

from backend.database.schema import DBAccount
from backend.exceptions import EntityNotFound, DuplicateEntityValue, InvalidCredentials
from backend.models import OptionalLogin, User, UpdatePassword
from fastapi import Form
from typing import Annotated
from backend.database import bcrypt as db_bcrypt


def get_all_accounts(session: Session) -> list[DBAccount]:
    """Retrieve all accounts from database

    Args:
        session (Session): The database session

    Returns:
        list[DBAccount]: The list of accounts
    """

    stmt = select(DBAccount).order_by(DBAccount.id)
    results = session.exec(stmt).all()
    return {
        "metadata": {"count": len(results)},
        "accounts": results
    }


def get_account_by_id(session: Session, account_id: int) -> DBAccount:
    """Retrieve specific account from database.

    Args:
        session (Session): The database session
        account_id (int): The id of the account to retrieve

    Returns:
        DBAccount: The account

    Raises:
        EntityNotFound: If no account with given id exists
    """

    account = session.get(DBAccount, account_id)
    if account is None:
        raise EntityNotFound("account", account_id)
    return account

def get_account_by_username(session: Session, username: str) -> DBAccount:
    """Retrieve specific account from database.

    Args:
        session (Session): The database session
        username (str): The username of the account to retrieve

    Returns:
        DBAccount: The account

    Raises:
        EntityNotFound: If no account with given username exists
    """

    stmt = select(DBAccount).where(DBAccount.username == username)
    account = session.exec(stmt).one_or_none()
    if account is None:
        raise EntityNotFound("account", username)
    return account

def get_account_by_email(session: Session, email: str) -> DBAccount:
    """Retrieve specific account from database.

    Args:
        session (Session): The database session
        email (str): The email of the account to retrieve

    Returns:
        DBAccount: The account

    Raises:
        EntityNotFound: If no account with given email exists
    """

    stmt = select(DBAccount).where(DBAccount.email == email)
    account = session.exec(stmt).one_or_none()
    if account is None:
        raise EntityNotFound("email", email)
    return account

def update_auth_user(session: Session, form: OptionalLogin, current_user: dict) -> User:
    """Update logged in account

    Args:
        session (Session): The database session
        form (Annotated[OptionalLogin, Form()]): The login form (username and pass)
        current_user (dict): the current user

    Returns:
        DBAccount: The updated account

    Raises:
       DuplicateEntity: If username matches the username of a different existing account
       DuplicateEntity: If email matches the email of a different existing account
    """

    account = get_account_by_id(session, current_user.id)
    if form.username and form.username != account.username:
        stmt = select(DBAccount).where(DBAccount.username == form.username)
        account_exists = session.exec(stmt).one_or_none()
        if account_exists:
            raise DuplicateEntityValue(form.username, "username", "account")
        account.username = form.username

    if form.email and form.email != account.email:
        stmt = select(DBAccount).where(DBAccount.email == form.email)
        account_exists = session.exec(stmt).one_or_none()
        if account_exists:
            raise DuplicateEntityValue(form.email, "email", "account")
        account.email = form.email

    session.add(account)
    session.commit()
    session.refresh(account)

    db_account = User(
        id = account.id,
        username = account.username,
        email = account.email
    )

    return db_account

def update_password(session: Session, form: Annotated[UpdatePassword, Form()], id: int):
    """Update password

    Args:
        session (Session): The database session
        form (Annotated[UpdatePassword, Form()]): The login form (old and new password)
        id (int): the current user id

    Raises:
        InvalidCredentials: If old_password does not match the account's hashed password
    """

    account = get_account_by_id(session, id)

    if not db_bcrypt.verify_password(form.old_password, account.hashed_password):
        raise InvalidCredentials()
    
    new_hashed_password = db_bcrypt.hash_password(form.new_password)
    account.hashed_password = new_hashed_password

    session.add(account)
    session.commit()
    session.refresh(account)

def delete_current_user(session: Session, id: int):
    """Delete the current logged in user

    Args:
        session (Session): The database session
        id (int): the current user id

    """

    account = get_account_by_id(session, id)

    session.delete(account)
    session.commit()

