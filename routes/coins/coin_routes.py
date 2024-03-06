import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from lib import ConnectionManager, get_current_user_socket
from sqlmodel import Session, select
from db import engine
from routes.auth.auth_models import User

coin_router = APIRouter(
    prefix="/coins",
    tags=["Coins"]
)


manager = ConnectionManager()


@coin_router.websocket("/{token}")
async def coin_socket(websocket: WebSocket, token: str):
    user = get_current_user_socket(token)
    
    await websocket.accept()
    await manager.connect(websocket)
    
    async def get_update_coins():
        while True:
            def get_coins():
                with Session(engine) as session:
                    result = session.exec(select(User).where(User.id == user.id)).one()
                    return result.coins

            new_coins = get_coins()
    
            x = {
                "coins": int(new_coins)
            }
            await manager.send_personal_message(x, websocket)
            await asyncio.sleep(5)

    task = await asyncio.create_task(get_update_coins())
    try:
        if user:
            asyncio.run(task)
                
    except WebSocketDisconnect:
        task.cancel()
        await manager.disconnect(websocket)
