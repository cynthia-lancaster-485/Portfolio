from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse, Response


class EntityNotFound(Exception):
    def __init__(self, entity_name: str, entity_id: int):
        self.status_code = 404
        self.message = f"Unable to find {entity_name} with id={entity_id}"

    def response(self) -> Response:
        """HTTP response when a non-existent entity is requested."""
        return JSONResponse(
            status_code=self.status_code,
            content={
                "error": "entity_not_found",
                "message": self.message,
            },
        )

class DuplicateEntityValue(Exception):
    def __init__(self, entity_name: str, entity_type: str, type: str):
        self.status_code = 422
        self.message = f"Duplicate value: {type} with {entity_type}={entity_name} already exists"

    def response(self) -> Response:
        """HTTP response when a duplicate entry is made."""
        return JSONResponse(
            status_code=self.status_code,
            content={
                "error": "duplicate_entity_value",
                "message": self.message,
            },
        )
class ChatMembershipRequired(Exception):
    def __init__(self, chat_id: int, account_id: int):
        self.status_code = 422
        self.message = f"Account with id={account_id} must be a member of chat with id={chat_id}"

    def response(self) -> Response:
        """HTTP response when a chat membership is required."""
        return JSONResponse(
            status_code=self.status_code,
            content={
                "error": "chat_membership_required",
                "message": self.message,
            },
        )
class ChatOwnerRemoval(Exception):
    def __init__(self):
        self.status_code = 422
        self.message = f"Unable to remove the owner of a chat"

    def response(self) -> Response:
        """HTTP response when a chat membership is required."""
        return JSONResponse(
            status_code=self.status_code,
            content={
                "error": "chat_owner_removal",
                "message": self.message,
            },
        )
    
class AuthenticationRequired(Exception):
    def __init__(self):
        self.status_code = 403
        self.message = f"Not authenticated"

    def response(self) -> Response:
        """HTTP response when an access token is not provided"""
        return JSONResponse(
            status_code=self.status_code,
            content={
                "error": "authentication_required",
                "message": self.message,
            },
        )
    
class ExpiredAccessToken(Exception):
    def __init__(self):
        self.status_code = 403
        self.message = f"Authentication failed: expired access token"

    def response(self) -> Response:
        """HTTP response when an access token is expired"""
        return JSONResponse(
            status_code=self.status_code,
            content={
                "error": "expired_access_token",
                "message": self.message,
            },
        )
    
class InvalidAccessToken(Exception):
    def __init__(self):
        self.status_code = 403
        self.message = f"Authentication failed: invalid access token"

    def response(self) -> Response:
        """HTTP response when an access token is not provided"""
        return JSONResponse(
            status_code=self.status_code,
            content={
                "error": "invalid_access_token",
                "message": self.message,
            },
        )

class InvalidCredentials(Exception):
    def __init__(self):
        self.status_code = 401
        self.message = f"Authentication failed: invalid username or password"

    def response(self) -> Response:
        """HTTP response when a username or password is incorrect"""
        return JSONResponse(
            status_code=self.status_code,
            content={
                "error": "invalid_credentials",
                "message": self.message,
            },
        )

class AccessDenied(Exception):
    def __init__(self, type: str):
        self.status_code = 403
        self.message = f"Cannot create {type} on behalf of different account"

    def response(self) -> Response:
        """HTTP response when a account id doesn't match"""
        return JSONResponse(
            status_code=self.status_code,
            content={
                "error": "access_denied",
                "message": self.message,
            },
        )


app = FastAPI()
