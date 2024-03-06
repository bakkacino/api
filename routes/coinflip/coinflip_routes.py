from fastapi import APIRouter, Depends, HTTPException, WebSocketException
from sqlmodel import Session, select
from db import engine
from routes.coinflip.coinflip_models import Coinflip, GameModel, GameUser
from routes.auth.auth_models import User
from lib import get_current_user, get_current_user_socket


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

            new_game = GameModel(id=game.id, bet_amount=game.bet_amount, active=game.active, players=players)
            games.append(new_game)

        return games


@coinflip_router.post("/create", tags=["Coinflip"])
def create_game(bet_amount: int, current_user: User = Depends(get_current_user)):
    
    if bet_amount > 0:
        raise HTTPException(status_code=400, detail="Bet amount cant be null.")

    if current_user.coins < bet_amount:
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


# @coinflip_router.websocket("/join/{game_id}/{token}")
# def join_game_ws(game_id: int, token: str): 
#     user = get_current_user_socket(token)
#     
#     with Session(engine) as session:
#         result = session.exec(select(Coinflip).where(Coinflip.id == game_id))
#         game = result.first()
#         
