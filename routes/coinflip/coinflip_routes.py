import asyncio

from fastapi import APIRouter, Depends, HTTPException, WebSocketException, WebSocket, WebSocketDisconnect
from sqlmodel import Session, select
from db import engine
from routes.coinflip.coinflip_models import Coinflip, GameModel, GameUser
from routes.auth.auth_models import User
from lib import get_current_user, get_current_user_socket
from routes.coinflip.coinflip_lib import CoinflipGameConnectionManager


coinflip_router = APIRouter(
    prefix="/coinflip",
    tags=["Coinflip"]
)


@coinflip_router.get("/", tags=["Coinflip"])
def get_games():
    with Session(engine) as session:
        result = session.exec(select(Coinflip)).all()

        games = []

        for game in result:
            players = []

            for player in game.players:
                new_player = GameUser(username=player.username, level=player.level)
                players.append(new_player)

            new_game = GameModel(id=game.id, bet_amount=game.bet_amount, status=game.status, players=players)
            games.append(new_game)

        return games


@coinflip_router.post("/create", tags=["Coinflip"])
def create_game(bet_amount: int, current_user: User = Depends(get_current_user)):
    
    if bet_amount < 1:
        raise HTTPException(status_code=400, detail="Bet amount cant be null.")

    if current_user.coins > bet_amount:
        raise HTTPException(status_code=400, detail="Not enough coins.")

    current_user.coins = current_user.coins - bet_amount

    game = Coinflip(bet_amount=bet_amount, players=[current_user])
    with Session(engine) as session:
        session.add(game)
        session.add(current_user)
        session.commit()
        session.refresh(game)
        return game.id
    

@coinflip_router.post("/join")
def join_game(game_id: int, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        result = session.exec(select(Coinflip).where(Coinflip.id == game_id))
        game = result.first()
        
        if current_user in game.players:
            raise HTTPException(status_code=400, detail="You cannot join your own game.")
        
        if not game:
            raise HTTPException(status_code=404, detail="Game does not exist.")
        
        if len(game.players) >= 2:
            raise HTTPException(status_code=400, detail="Game is already full.")
        
        game.players.append(current_user)
        session.commit()
        session.refresh(game)
        return game_id


manager = CoinflipGameConnectionManager()


@coinflip_router.websocket("/join/{game_id}/{token}")
async def game_ws(websocket: WebSocket, game_id: int, token: str):
    user = get_current_user_socket(token)

    with Session(engine) as session:
        result = session.exec(select(Coinflip).where(Coinflip.id == game_id))
        game = result.first()

        if game is None:
            raise WebSocketException(code=404, reason="Game doesnt exist.")

        # if user not in game.players:
        #     raise WebSocketException(code=403, reason="You are not a player of this game.")

        await websocket.accept()
        await manager.connect(websocket, game_id)

        is_host = manager.is_host(game_id, websocket)

        joined_players = 0

        if is_host:
            joined_players = 1

        try:
            if is_host:
                await manager.send_message_to_game(game_id, {"type": "host", "message": f"{user.username} is the host."})

            await manager.send_message_to_game(game_id, {"type": "join", "message": f"{user.username} joined the game."})

            while True:
                # data = await websocket.receive_json()
                if is_host:
                    ready = await manager.game_ready(game_id)
                    if ready:
                        print("Game play here")
                        await asyncio.sleep(5)
                    await manager.cleanup_game(game_id)
                await asyncio.sleep(1)
        except WebSocketDisconnect:
            await CoinflipGameConnectionManager().disconnect(websocket)
