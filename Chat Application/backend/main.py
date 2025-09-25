"""PonyExpress backend API application.

Args:
    app (FastAPI): The FastAPI application
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.dependencies import create_db_tables

from backend.routers import accounts, chats, auth

from backend.exceptions import EntityNotFound, DuplicateEntityValue, ChatMembershipRequired, ChatOwnerRemoval, AuthenticationRequired, ExpiredAccessToken, InvalidAccessToken, InvalidCredentials, AccessDenied

from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_tables()
    yield


app = FastAPI(
    title="chat",
    summary="chat-aplication",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

@app.get("/status", response_model=None, status_code=204)
def status():
    pass
@app.exception_handler(EntityNotFound)
@app.exception_handler(DuplicateEntityValue)
@app.exception_handler(ChatMembershipRequired)
@app.exception_handler(ChatOwnerRemoval)
@app.exception_handler(AuthenticationRequired)
@app.exception_handler(ExpiredAccessToken)
@app.exception_handler(InvalidAccessToken)
@app.exception_handler(InvalidCredentials)
@app.exception_handler(AccessDenied)


def entity_not_found_handler(response, exc):
	return exc.response()


app.include_router(accounts.router)
app.include_router(chats.router)
app.include_router(auth.router)

