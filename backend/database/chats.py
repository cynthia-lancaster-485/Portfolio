from sqlmodel import Session, select

from backend.database.schema import DBChat, DBMessage, DBAccount, DBChatMembership
from backend.models import ChatCreate, ChatUpdate, MessageCreate, MessageUpdate, Membership, Message
from backend.exceptions import EntityNotFound, DuplicateEntityValue, ChatMembershipRequired, ChatOwnerRemoval, AccessDenied
from backend.database import accounts as db_accounts
from datetime import datetime
from fastapi.responses import Response
from fastapi import Depends
from backend.database import auth as auth_db


def get_all_chats(session: Session) -> list[DBChat]:
    """Retrieve all chats from database

    Args:
        session (Session): The database session

    Returns:
        list[DBChat]: The list of chats
    """

    stmt = select(DBChat).order_by(DBChat.id)
    results = session.exec(stmt).all()
    return {
        "metadata": {"count": len(results)},
        "chats": results
    }


def get_chat_by_id(session: Session, chat_id: int) -> DBChat:
    """Retrieve specific chat from database.

    Args:
        session (Session): The database session
        chat_id (int): The id of the chat to retrieve

    Returns:
        DBChat: The chat

    Raises:
        EntityNotFound: If no chat with given id exists
    """

    chat = session.get(DBChat, chat_id)
    if chat is None:
        raise EntityNotFound("chat", chat_id)
    return chat

def get_messages_by_chat_id(session: Session, chat_id: int) -> dict:
    """Retrieve specific messages for a chat from database.

    Args:
        session (Session): The database session
        chat_id (int): The id of the chat to retrieve messages from

    Returns:
        DBChat: The chat

    Raises:
        EntityNotFound: If no chat with given id exists
    """

    retrieve = select(DBMessage).where(DBMessage.chat_id == chat_id).order_by(DBMessage.id)
    messages = session.exec(retrieve).all()
    if not messages: 
        raise EntityNotFound("chat", chat_id)
    return {
        "metadata": {"count": len(messages)},
        "messages": messages
    }

def get_accounts_by_chat_id(session: Session, chat_id: int) -> dict:
    """Retrieve accounts for a chat from database.

    Args:
        session (Session): The database session
        chat_id (int): The id of the chat to retrieve accounts from

    Returns:
        DBChat: The chat

    Raises:
        EntityNotFound: If no chat with given id exists
    """

    stmt = (select(DBAccount).join(DBChatMembership, DBAccount.id == DBChatMembership.account_id)
        .where(DBChatMembership.chat_id == chat_id)
        .order_by(DBAccount.id)
    )
    accounts = session.exec(stmt).all()
    if not accounts:
        raise EntityNotFound("chat", chat_id)
    return {
        "metadata": {"count": len(accounts)},
        "accounts": accounts
    }

def create_chat(session: Session, chat: ChatCreate, current_user: dict = Depends(auth_db.get_current_user)) -> DBChat:
    """Creates a chat in the database

    Args:
        session (Session): The database session
        chat (Chat): 

    Returns:
        DBChat: The chat

    Raises:
        EntityNotFound: If no account with the given id exists
        DuplicateEntityValue: If an chat with the same name exists
    """
    "Check to see if owner exists"
    owner = db_accounts.get_account_by_id(session, chat.owner_id)
    if not owner:
        raise EntityNotFound("chat", owner.id)
    
    if owner.id != current_user.id:
        raise AccessDenied("chat")
    
    "Check to see if chat already exists "
    exists = session.query(DBChat).filter(DBChat.name == chat.name).first()
    if exists:
        raise DuplicateEntityValue(chat.name, "name", "chat")
    
    name = chat.name
    db_chat = DBChat(
        name = name,
        owner_id = owner.id
    )
    session.add(db_chat)
    session.commit()
    return db_chat

def update_chat(session: Session, chat: ChatUpdate, chat_id: int) -> DBChat:
    """Updates a chat in the database

    Args:
        session (Session): The database session
        chat (Chat): 

    Returns:
        DBChat: The updated chat

    Raises:
        EntityNotFound: If no chat with given id exists
        DuplicateEntityValue: If chat name already exists in database
        ChatMembershipRequired: If no account with given id exists or account
             with given id is not a member of the chat 
    """

    "Check to see if chat exists"
    chat_exists = session.query(DBChat).filter(DBChat.id == chat_id).first()
    if not chat_exists:
        raise EntityNotFound("chat", chat_id)
    

    "Check to see if chat with that name already exists"
    if chat.name:
        exists = session.query(DBChat).filter(DBChat.name == chat.name).first()
        if exists:
            raise DuplicateEntityValue(chat.name, "name", "chat")
        
    "Check if owner exists"
    if chat.owner_id:
        accounts = get_accounts_by_chat_id(session, chat_id)
        account_ids = [account.id for account in accounts["accounts"]]
        if chat.owner_id not in account_ids:
            raise ChatMembershipRequired(chat_id, chat.owner_id)
    
    if chat.name:
        chat_exists.name = chat.name
    if chat.owner_id:
        chat_exists.owner_id = chat.owner_id
    
    session.commit()
    return chat_exists
    
def delete_chat(session: Session, chat_id: int) -> None:
    """Deletes a chat in the database

    Args:
        session (Session): The database session
        chat_id (Chat): chat_id of chat to delete

    """
    chat = get_chat_by_id(session, chat_id)
    if not chat:
        raise EntityNotFound("chat", chat_id.id)
    session.delete(chat)
    session.commit()

def add_message(session: Session, chat: MessageCreate, chat_id: int, current_user: dict = Depends(auth_db.get_current_user)) -> Message:
    """Adds a message to the database.

    Args:
        session (Session): The database session
        chat_id (int): The id of the chat to add messages to
        chat (MessageCreate): 

    Returns:
        DBChat: The chat

    Raises:
        EntityNotFound: If no chat with given id exists
    """

    chat_exists = session.query(DBChat).filter(DBChat.id == chat_id).first()
    if not chat_exists:
        raise EntityNotFound("chat", chat_id)
    
    account = session.query(DBAccount).filter(DBAccount.id == chat.account_id).first()
    if not account:
        raise ChatMembershipRequired(chat_id, chat.account_id)
    
    is_member = session.query(DBChatMembership).filter(DBChatMembership.chat_id == chat_id, 
        DBChatMembership.account_id == chat.account_id).first()
    
    if not is_member:
        raise ChatMembershipRequired(chat_id, chat.account_id)
    
    if chat.account_id != current_user.id:
        raise AccessDenied("message")
    
    message = DBMessage(
        text = chat.text,
        account_id = chat.account_id,
        chat_id = chat_id,
        created_at=datetime.now()
    )
    session.add(message)
    session.commit()
    
    return message

def update_message_text(session: Session, chat_id: int, message_id: int, message: MessageUpdate ) -> Message:
    """Updates the test of an existing message in the give chat

    Args:
        session (Session): The database session
        chat_id (int): The id of the chat to add messages to
        message (MessageUpdate): The test for the message

    Returns:
        DBChat: The updated message

    Raises:
        EntityNotFound: If no chat or message with given id exists 
    """

    chat_exists = get_chat_by_id(session, chat_id)
    if not chat_exists:
        raise EntityNotFound("chat", chat_id)
    
    message_exists = session.query(DBMessage).filter(DBMessage.id == message_id, DBMessage.chat_id == chat_id).first()
    if not message_exists:
        raise EntityNotFound("message", message_id)
    
    message_exists.text = message.text
    session.commit()
    
    return message_exists

def delete_message(session, chat_id, message_id) -> None:
    """Deletes a message from the chat

    Args:
        session (Session): The database session
        chat_id (Chat): id of chat to remove message from 
        message_id (Message): id of message to delete

    """
    chat = get_chat_by_id(session, chat_id)
    if not chat:
        raise EntityNotFound("chat", chat_id)
    
    message = session.query(DBMessage).filter(DBMessage.id == message_id, DBMessage.chat_id == chat_id).first()
    if not message:
        raise EntityNotFound("message", message_id)
    session.delete(message)
    session.commit()
    
def add_membership(session: Session, chat_id: int, account_id: int, response: Response) -> Membership:
    """Adds an account to the chat 
    Args:
        session (Session): The database session
        chat_id (int): The id of the chat to add the account to
        account_id (int): the id of the account to add to the chat

    Returns:
        dict: JSOn with membership details

    Raises:
        EntityNotFound: If no chat or account with given id exists
    """

    chat = session.query(DBChat).filter(DBChat.id == chat_id).first()
    if not chat:
        raise EntityNotFound("chat", chat_id)
    
    account = session.query(DBAccount).filter(DBAccount.id == account_id).first()
    if not account:
        raise EntityNotFound("account", account_id)
    
    is_member = session.query(DBChatMembership).filter(DBChatMembership.chat_id == chat_id, 
                DBChatMembership.account_id == account_id).first()
    
    if is_member:
        response.status_code = 200
        return {
            "chat_id": chat_id,
            "account_id": account_id,
        }
    
    membership = DBChatMembership(
        account_id = account_id,
        chat_id = chat_id
    )
    session.add(membership)
    session.commit()
    
    response.status_code = 201
    return {
        "chat_id": chat_id,
        "account_id": account_id
    }

def delete_membership(session, chat_id, account_id) -> None:
    """Deletes a membership from the chat

    Args:
        session (Session): The database session
        chat_id (Chat): id of chat to remove membership from 
        account_id (Account): id of Account to delete membership from

    """
    chat = session.query(DBChat).filter(DBChat.id == chat_id).first()
    if not chat:
        raise EntityNotFound("chat", chat_id)
    
    account = session.query(DBAccount).filter(DBAccount.id == account_id).first()
    if not account:
       raise ChatMembershipRequired(chat_id, account_id)
    
    is_member = session.query(DBChatMembership).filter(DBChatMembership.chat_id == chat_id, 
                DBChatMembership.account_id == account_id).first()
    if not is_member:
        raise ChatMembershipRequired(chat_id, account_id)
    
    if chat.owner_id == account_id:
        raise ChatOwnerRemoval()
    
    session.query(DBMessage).filter(DBMessage.chat_id == chat_id, DBMessage.account_id == account_id).update(
        {DBMessage.account_id: None}, synchronize_session=False)

    session.delete(is_member)
    session.commit()