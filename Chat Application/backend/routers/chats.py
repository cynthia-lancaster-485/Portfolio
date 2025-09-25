from fastapi import APIRouter

from backend.database import chats as chats_db
from backend.database import auth as auth_db
from backend.database.schema import DBChat
from backend.dependencies import DBSession
from backend.models import Chat, ChatList, MessageList, AccountList, ChatCreate, ChatUpdate, AddMessage, MessageCreate, MessageUpdate, Membership, AddAccount, Message
from fastapi import status, Response, Depends

router = APIRouter(prefix="/chats", tags=["Chats"])

@router.get("", response_model=ChatList)
def get_chats(session: DBSession):
    return chats_db.get_all_chats(session)

@router.get("/{chat_id}", response_model=Chat)
def get_chat_by_id(session: DBSession, chat_id: int):
    return chats_db.get_chat_by_id(session, chat_id)

@router.get("/{chat_id}/messages", response_model=MessageList)
def get_chat_by_id(session: DBSession, chat_id: int):
    return chats_db.get_messages_by_chat_id(session, chat_id)

@router.get("/{chat_id}/accounts", response_model=AccountList)
def get_chat_by_id(session: DBSession, chat_id: int):
    return chats_db.get_accounts_by_chat_id(session, chat_id)

@router.post("", response_model=Chat, status_code=status.HTTP_201_CREATED)
def create_chat(chat: ChatCreate, session: DBSession, current_user: dict = Depends(auth_db.get_current_user)) -> DBChat:
    return chats_db.create_chat(session, chat, current_user)

@router.put("/{chat_id}", response_model=Chat, status_code=status.HTTP_200_OK)
def update_chat(chat_id: int, chat: ChatUpdate, session: DBSession) -> DBChat:
    return chats_db.update_chat(session, chat, chat_id)

@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat(chat_id: int, session: DBSession) -> None:
    return chats_db.delete_chat(session, chat_id)

@router.post("/{chat_id}/messages", status_code=status.HTTP_201_CREATED, response_model=Message)
def add_message(chat: MessageCreate, session: DBSession, chat_id: int, current_user: dict = Depends(auth_db.get_current_user)):
    return chats_db.add_message(session, chat, chat_id, current_user)

@router.put("/{chat_id}/messages/{message_id}", status_code=status.HTTP_200_OK, response_model=Message)
def update_message_text(session: DBSession, chat_id: int, message_id: int, message: MessageUpdate):
    return chats_db.update_message_text(session, chat_id, message_id, message)

@router.delete("/{chat_id}/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(session: DBSession, chat_id: int, message_id: int):
    return chats_db.delete_message(session, chat_id, message_id)

@router.post("/{chat_id}/accounts", response_model=Membership)
def add_membership(session: DBSession, chat_id: int, account: AddAccount, response: Response):
    return chats_db.add_membership(session, chat_id, account.account_id, response)

@router.delete("/{chat_id}/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_membership(session: DBSession, chat_id: int, account_id: int):
    return chats_db.delete_membership(session, chat_id, account_id)