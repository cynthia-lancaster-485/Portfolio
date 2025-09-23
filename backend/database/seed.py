import json
from datetime import datetime

from sqlmodel import Session, SQLModel, create_engine, select

from backend.database.schema import *


def get_engine(filename):
    engine = create_engine(
        f"sqlite:///{filename}",
        connect_args={"check_same_thread": False},
        echo=True,
    )
    SQLModel.metadata.create_all(engine)
    return engine


def seed_accounts(session, data):
    existing_ids = set(session.exec(select(DBAccount.id)).all())
    for account in data["accounts"]:
        if account["id"] not in existing_ids:
            session.add(DBAccount(**account))
    session.commit()


def seed_chats(session, data):
    existing_ids = set(session.exec(select(DBChat.id)).all())
    for chat in data["chats"]:
        if chat["id"] not in existing_ids:
            session.add(DBChat(**chat))
    session.commit()


def seed_messages(session, data):
    existing_ids = set(session.exec(select(DBMessage.id)).all())
    for message in data["messages"]:
        if message["id"] not in existing_ids:
            message["created_at"] = datetime.fromisoformat(message["created_at"])
            session.add(DBMessage(**message))
    session.commit()


def seed_memberships(session, data):
    existing_ids = set(
        session.exec(
            select(DBChatMembership.chat_id, DBChatMembership.account_id)
        ).all()
    )
    for membership in data["memberships"]:
        if (membership["chat_id"], membership["account_id"]) not in existing_ids:
            session.add(DBChatMembership(**membership))
    session.commit()


if __name__ == "__main__":
    import sys

    filename = sys.argv[1]
    engine = get_engine(filename)

    with open("backend/database/initial.json") as file:
        data = json.load(file)

    with Session(engine) as session:
        seed_accounts(session, data)
        seed_chats(session, data)
        seed_messages(session, data)
        seed_memberships(session, data)
