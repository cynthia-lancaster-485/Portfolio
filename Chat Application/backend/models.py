from pydantic import BaseModel
from datetime import datetime


class Account(BaseModel):
    id: int 
    username: str

class Chat(BaseModel):
    id: int
    name: str
    owner_id: int

class ChatCreate(BaseModel):
    name: str
    owner_id: int

class ChatUpdate(BaseModel):
    name: str | None = None
    owner_id: int | None = None

class Message(BaseModel):
    id: int 
    text: str
    account_id: int
    chat_id: int
    created_at: datetime = datetime.utcnow()

class MessageCreate(BaseModel):
    text: str
    account_id: int

class Metadata(BaseModel):
    count: int

class ChatList(BaseModel):
    metadata: Metadata
    chats: list[Chat]

class AccountList(BaseModel):
    metadata: Metadata
    accounts: list[Account]

class MessageList(BaseModel):
    metadata: Metadata
    messages: list[Message]

class AddMessage(BaseModel):
    text: str
    account_id: int

class MessageUpdate(BaseModel):
    text: str

class AddAccount(BaseModel):
    account_id: int

class Membership(BaseModel):
    account_id: int
    chat_id: int

class User(BaseModel):
    id: int
    username: str
    email: str

class Registration(BaseModel):
    username: str
    email: str
    phone: str | None = None 
    password: str

class NewToken(BaseModel):
    username: str
    password: str

class AccessToken(BaseModel):
    access_token: str
    token_type: str

class Claims(BaseModel):
    sub: str
    iss: str
    iat: int
    exp: int

class Login(BaseModel):
    username: str
    password: str

class OptionalLogin(BaseModel):
    username: str | None = None
    email: str | None = None

class UpdatePassword(BaseModel):
    old_password: str
    new_password: str
