from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from db import create_db_and_tables
from lib import ConnectionManager, get_current_user_socket
from dotenv import load_dotenv
from routes.auth.auth_routes import auth_router
from routes.coinflip.coinflip_routes import coinflip_router
from routes.coins.coin_routes import coin_router

app = FastAPI(title="Bakkacino API")
load_dotenv()

app.include_router(auth_router)
app.include_router(coinflip_router)
app.include_router(coin_router)

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.get("/")
def main():
    return "Hello World"


manager = ConnectionManager()


@app.websocket("/chat")
async def chat_socket(websocket: WebSocket):

    await websocket.accept()
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)


@app.websocket("/chat/{token}")
async def validated_chat(websocket: WebSocket, token):
    user = get_current_user_socket(token)

    await websocket.accept()
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if user and data:
                x = {
                    "user": user.username,
                    "type": "message",
                    "value": data,
                    "level": user.level
                }
                await manager.broadcast(x)
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
