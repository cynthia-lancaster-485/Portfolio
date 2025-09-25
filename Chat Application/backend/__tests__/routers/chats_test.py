from backend.database.schema import DBChat, DBMessage, DBAccount, DBChatMembership
from backend.database import bcrypt as db_bcrypt

def test_get_chats(session, client):
    aaron = DBAccount(username='aaron', email='aaron@example.com', hashed_password='aaronpass')
    ted = DBAccount(username='ted', email='ted@example.com', hashed_password='tedpass')
    session.add_all([aaron, ted])
    session.commit()

    hi = DBChat(name='hi', owner_id=aaron.id)
    bye = DBChat(name='bye', owner_id=ted.id)
    session.add_all([hi, bye])
    session.commit()

    response = client.get("/chats")
    assert response.status_code == 200
    assert response.json()["metadata"]["count"] == 2
    assert response.json()["chats"] == [
        {"id": 1, "name": "hi", "owner_id": 1},
        {"id": 2, "name": "bye", "owner_id": 2},
    ]

def test_get_chat_1(session, client):
    aaron = DBAccount(username='aaron', email='aaron@example.com', hashed_password='aaronpass')
    session.add(aaron)
    session.commit()

    chat = DBChat(name="one", owner_id=aaron.id)
    session.add(chat)
    session.commit()

    response = client.get(f"/chats/{chat.id}")
    assert response.status_code == 200
    assert response.json() == {"id": chat.id, "name": "one", "owner_id": 1}

def test_get_nonexsistent_chat(session, client):
    response = client.get(f"/chats/100")
    assert response.status_code == 404
    assert response.json() == {
        "error": "entity_not_found",
        "message": "Unable to find chat with id=100"
    }

def test_get_messages(session, client):
    aaron = DBAccount(username='aaron', email='aaron@example.com', hashed_password='aaronpass')
    ted = DBAccount(username='ted', email='ted@example.com', hashed_password='tedpass')
    session.add_all([aaron, ted])
    session.commit()

    chat = DBChat(name="Message Chat", owner_id=aaron.id)
    session.add(chat)
    session.commit()

    m1 = DBMessage(chat_id=chat.id, account_id=aaron.id, text="hi")
    m2 = DBMessage(chat_id=chat.id, account_id=aaron.id, text="bye")

    session.add_all([m1, m2])
    session.commit()

    response = client.get(f"/chats/{chat.id}/messages")
    assert response.status_code == 200
    assert response.json()["metadata"]["count"] == 2
    assert response.json()["messages"] == [
        {"id": m1.id, "chat_id": chat.id, "account_id": aaron.id, "text": "hi", "created_at": m1.created_at.isoformat()},
        {"id": m2.id, "chat_id": chat.id, "account_id": aaron.id, "text": "bye", "created_at": m2.created_at.isoformat()},
    ]

def test_get_messages_from_nonexsistent_chat(session, client):
    response = client.get(f"/chats/100/messages")
    assert response.status_code == 404
    assert response.json() == {
        "error": "entity_not_found",
        "message": "Unable to find chat with id=100"
    }


def test_get_accounts(session, client):
    aaron = DBAccount(username='aaron', email='aaron@example.com', hashed_password='aaronpass')
    ted = DBAccount(username='ted', email='ted@example.com', hashed_password='tedpass')
    session.add_all([aaron, ted])
    session.commit()

    chat = DBChat(name="Message Chat", owner_id=aaron.id)
    session.add(chat)
    session.commit()

    chat_membership_aaron = DBChatMembership(chat_id=chat.id, account_id=aaron.id)
    chat_membership_ted = DBChatMembership(chat_id=chat.id, account_id=ted.id)
    session.add_all([chat_membership_aaron, chat_membership_ted])
    session.commit()

    response = client.get(f"/chats/{chat.id}/accounts")
    assert response.status_code == 200
    assert response.json()["metadata"]["count"] == 2
    assert response.json()["accounts"] == [
        {"id": aaron.id, "username": "aaron"},
        {"id": ted.id, "username": "ted"},
    ]


def test_get_accounts_from_nonexsistent_chat(session, client):
    response = client.get(f"/chats/100/accounts")
    assert response.status_code == 404
    assert response.json() == {
        "error": "entity_not_found",
        "message": "Unable to find chat with id=100"
    }

def test_create_chat(session, client):
    aaron = DBAccount(username='aaron', email='aaron@example.com', hashed_password='aaronpass')
    session.add(aaron)
    session.commit()

    chat_data = {
        "name": "new_chat",
        "owner_id": aaron.id
    }
    response = client.post("/chats", json=chat_data)
    assert response.status_code == 201
    assert response.json()["name"] == "new_chat"
    assert response.json()["owner_id"] == aaron.id

def test_no_chat_owner(session, client):
    chat_data = {
        "name": "new_chat",
        "owner_id": 9999
    }

    response = client.post("/chats", json=chat_data)
    assert response.status_code == 404 
    assert response.json() == {
        "error": "entity_not_found",
        "message": "Unable to find account with id=9999"
    }

def test_duplicate_chat_name(session, client):
    aaron = DBAccount(username='aaron', email="aaron@example.com", hashed_password='aaronpass')
    session.add(aaron)
    session.commit()

    chat1 = DBChat(name="new_chat", owner_id=aaron.id)
    session.add(chat1)
    session.commit()

    chat_data = {
        "name": "new_chat",
        "owner_id": aaron.id
    }
    response = client.post("/chats", json=chat_data)
    assert response.status_code == 422
    assert response.json() == {
        "error": "duplicate_entity_value",
        "message": "Duplicate value: chat with name=new_chat already exists"
    }

def test_update_chat(session, client):
    aaron = DBAccount(username='aaron', email='aaron@example.com', hashed_password='aaronpass')
    session.add(aaron)
    session.commit()

    chat = DBChat(name="one", owner_id=aaron.id)
    session.add(chat)
    session.commit()

    update_data = {
        "name": "updated_chat",
        "owner_id": aaron.id
    }

    account_data = {"account_id": aaron.id}
    response_account = client.post(f"/chats/{chat.id}/accounts", json=account_data)
    assert response_account.status_code == 201 
    assert response_account.json() 

    response = client.put(f"/chats/{chat.id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["name"] == "updated_chat"
    assert response.json()["owner_id"] == aaron.id



def test_update_nonexistent_chat(session, client):
    update_data = {
        "name": "updated_chat",
        "owner_id": 9999
    }
    response = client.put("/chats/100", json=update_data)
    assert response.status_code == 404
    assert response.json() == {
        "error": "entity_not_found",
        "message": "Unable to find chat with id=100"
    }

def test_update_duplicate_name(session, client):
    aaron = DBAccount(username='aaron', email='aaron@example.com', hashed_password='aaronpass')
    ted = DBAccount(username='ted', email='ted@example.com', hashed_password='tedpass')
    session.add_all([aaron, ted])
    session.commit()

    chat1 = DBChat(name="chat1", owner_id=aaron.id)
    chat2 = DBChat(name="chat2", owner_id=ted.id)
    session.add_all([chat1, chat2])
    session.commit()

    update_data = {
        "name": "chat2", 
        "owner_id": aaron.id
    }
    response = client.put(f"/chats/{chat1.id}", json=update_data)
    assert response.status_code == 422
    assert response.json() == {
        "error": "duplicate_entity_value",
        "message": "Duplicate value: chat with name=chat2 already exists"
    }

def test_delete_chat(session, client):
    aaron = DBAccount(username='aaron', email='aaron@example.com', hashed_password='aaronpass')
    session.add(aaron)
    session.commit()

    chat = DBChat(name="delete_chat", owner_id=aaron.id)
    session.add(chat)
    session.commit()

    response = client.delete(f"/chats/{chat.id}")
    assert response.status_code == 204

def test_delete_nonexistent_chat(session, client):
    response = client.delete("/chats/100")
    assert response.status_code == 404
    assert response.json() == {
        "error": "entity_not_found",
        "message": "Unable to find chat with id=100"
    }

def test_add_message(session, client):
    aaron = DBAccount(username='aaron', email='aaron@example.com', hashed_password='aaronpass')
    session.add(aaron)
    session.commit()

    chat = DBChat(name="its late", owner_id=aaron.id)
    session.add(chat)
    session.commit()

    account_data = {"account_id": aaron.id}

    response_account = client.post(f"/chats/{chat.id}/accounts", json=account_data)
    assert response_account.status_code == 201 
    assert response_account.json() 

    message_data = {
        "text": "Why am i up",
        "account_id": aaron.id 
    }
    
    response = client.post(f"/chats/{chat.id}/messages", json=message_data)
    assert response.status_code == 201
    assert response.json()["text"] == "Why am i up"


def test_add_message_nonexistent_chat(session, client):
    message_data = {
        "text": "Yeah its me",
        "account_id": 1
    }
    response = client.post("/chats/100/messages", json=message_data)
    assert response.status_code == 404
    assert response.json() == {
        "error": "entity_not_found",
        "message": "Unable to find chat with id=100"
    }

def test_add_message_account_not_member(session, client):
    aaron = DBAccount(username='aaron', email='aaron@example.com', hashed_password='aaronpass')
    ted = DBAccount(username='ted', email='ted@example.com', hashed_password='tedpass')
    session.add_all([aaron, ted])
    session.commit()

    chat = DBChat(name="Its ya boi", owner_id=aaron.id)
    session.add(chat)
    session.commit()

    message_data = {
        "text": "...ok",
        "account_id": ted.id
    }
    response = client.post(f"/chats/{chat.id}/messages", json=message_data)
    assert response.status_code == 422
    assert response.json() == {
        "error": "chat_membership_required",
        "message": "Account with id=2 must be a member of chat with id=1"
    }

def test_delete_message(session, client):
    aaron = DBAccount(username='aaron', email='aaron@example.com', hashed_password='aaronpass')
    session.add(aaron)
    session.commit()

    chat = DBChat(name="getting there", owner_id=aaron.id)
    session.add(chat)
    session.commit()

    message = DBMessage(chat_id=chat.id, account_id=aaron.id, text="slowly")
    session.add(message)
    session.commit()

    response = client.delete(f"/chats/{chat.id}/messages/{message.id}")
    assert response.status_code == 204

def test_delete_nonexistent_message(session, client):
    response = client.delete("/chats/100/messages/100")
    assert response.status_code == 404
    assert response.json() == {
        "error": "entity_not_found",
        "message": "Unable to find chat with id=100"
    }

def test_add_membership(session, client):
    aaron = DBAccount(username='aaron', email='aaron@example.com', hashed_password='aaronpass')
    session.add(aaron)
    session.commit()

    chat = DBChat(name="not too bad", owner_id=aaron.id)
    session.add(chat)
    session.commit()

    membership_data = {
        "account_id": aaron.id
    }
    response = client.post(f"/chats/{chat.id}/accounts", json=membership_data)
    assert response.status_code == 201
    assert response.json()["chat_id"] == chat.id
    assert response.json()["account_id"] == aaron.id

def test_add_membership_to_nonexistent_chat(session, client):
    membership_data = {
        "account_id": 1
    }
    response = client.post("/chats/100/accounts", json=membership_data)
    assert response.status_code == 404
    assert response.json() == {
        "error": "entity_not_found",
        "message": "Unable to find chat with id=100"
    }

def test_add_membership_to_nonexistent_account(session, client):
    aaron = DBAccount(username='aaron', email='aaron@example.com', hashed_password='aaronpass')
    session.add(aaron)
    session.commit()

    chat = DBChat(name="not too bad", owner_id=aaron.id)
    session.add(chat)
    session.commit()

    membership_data = {
        "account_id": 9999 
    }
    response = client.post("/chats/1/accounts", json=membership_data)
    assert response.status_code == 404
    assert response.json() == {
        "error": "entity_not_found",
        "message": "Unable to find account with id=9999"
    }

def test_delete_owner_membership(session, client):
    aaron = DBAccount(username='aaron', email='aaron@example.com', hashed_password='aaronpass')
    ted = DBAccount(username='ted', email='ted@example.com', hashed_password='tedpass')
    session.add_all([aaron, ted])
    session.commit()

    chat = DBChat(name="chatty", owner_id=ted.id)
    session.add(chat)
    session.commit()

    chat_membership = DBChatMembership(chat_id=chat.id, account_id=ted.id)
    session.add(chat_membership)
    session.commit()

    response = client.delete(f"/chats/{chat.id}/accounts/{ted.id}")
    assert response.status_code == 422
    assert response.json() == {
        "error": "chat_owner_removal",
        "message": "Unable to remove the owner of a chat"
    }


def test_delete_nonexistent_membership(session, client):
    response = client.delete("/chats/100/accounts/100")
    assert response.status_code == 404
    assert response.json() == {
        "error": "entity_not_found",
        "message": "Unable to find chat with id=100"
    }

def test_delete_membership_account_not_member(session, client):
    aaron = DBAccount(username='aaron', email='aaron@example.com', hashed_password='aaronpass')
    ted = DBAccount(username='ted', email='ted@example.com', hashed_password='tedpass')
    session.add_all([aaron, ted])
    session.commit()

    chat = DBChat(name="chat_for_membership", owner_id=aaron.id)
    session.add(chat)
    session.commit()

    response = client.delete(f"/chats/{chat.id}/accounts/{ted.id}")
    assert response.status_code == 422
    assert response.json() == {
        "error": "chat_membership_required",
        "message": "Account with id=2 must be a member of chat with id=1"
    }

def test_access_denied(session, client):
    a_password = "aaronpass"
    a_hashed_password = db_bcrypt.hash_password(a_password)
    aaron = DBAccount(username="aaronw", email="aaron@mail.com", hashed_password=a_hashed_password)
    session.add(aaron)
    session.commit()

    ted_password = "tedpass"
    ted_hashed_password = db_bcrypt.hash_password(ted_password)
    ted = DBAccount(username="ted", email="ted@mail.com", hashed_password=ted_hashed_password)
    session.add(ted)
    session.commit()

    login_data = {
        "username": "aaronw",
        "password": a_password
    }

    response = client.post("/auth/web/login", data=login_data)
    assert response.status_code == 204

    chat = DBChat(name="its late", owner_id=aaron.id)
    session.add(chat)
    session.commit()

    account_data = {"account_id": ted.id}

    response_account = client.post(f"/chats/{chat.id}/accounts", json=account_data)
    assert response_account.status_code == 201 
    assert response_account.json() 

    message_data = {
        "text": "Why am i up",
        "account_id": ted.id 
    }
    
    response = client.post(f"/chats/{chat.id}/messages", json=message_data)
    assert response.status_code == 403
    assert response.json() == {
        "error": "access_denied",
        "message": "Cannot create message on behalf of different account",
    }

