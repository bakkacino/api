from fastapi import WebSocket, WebSocketDisconnect, HTTPException, Depends, WebSocketException
from fastapi.security import OAuth2PasswordBearer
import json
import jwt
from dotenv import load_dotenv
from sqlmodel import Session, select
from db import engine
import os
from routes.auth.auth_models import User

load_dotenv()


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: json, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: json):
        for connection in self.active_connections:
            await connection.send_json(message)
            

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_current_user(token: str = Depends(oauth2_scheme)):
    decoded_token = None

    try:
        decoded_token = jwt.decode(token, os.environ.get("JWT_SECRET"), algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="The authentication token has expired. Please log in again to obtain a new token.")
    except jwt.DecodeError:
        raise HTTPException(status_code=401, detail="The provided authentication token is invalid. Please log in again to obtain a new token.")

    uid = decoded_token["id"]

    with Session(engine) as session:
        result = session.exec(select(User).where(User.id == uid))
        user = result.first()

    if not user:
        raise HTTPException(status_code=401, detail="The authentication token is not associated to a user.")

    return user


def get_current_user_socket(token: str):
    decoded_token = None

    try:
        decoded_token = jwt.decode(token, os.environ.get("JWT_SECRET"), algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise WebSocketException(code=401, reason="The authentication token has expired. Please log in again to obtain a new token.")
    except jwt.DecodeError:
        raise WebSocketException(code=401, reason="The provided authentication token is invalid. Please log in again to obtain a new token.")

    uid = decoded_token["id"]

    with Session(engine) as session:
        result = session.exec(select(User).where(User.id == uid))
        user = result.first()

    if not user:
        raise WebSocketException(code=401, reason="The authentication token is not associated to a user.")

    return user
