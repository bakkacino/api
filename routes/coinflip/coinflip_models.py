from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
import routes.auth.auth_models as auth_models
from pydantic import BaseModel


class CoinflipLink(SQLModel, table=True):
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", primary_key=True)
    coinflip_id: Optional[int] = Field(default=None, foreign_key="coinflip.id", primary_key=True)


class Coinflip(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, unique=True)
    bet_amount: int
    active: bool = Field(default=True)

    players: List["auth_models.User"] = Relationship(back_populates="coinflipgames", link_model=CoinflipLink)


class GameUser(BaseModel):
    username: str
    level: int


class GameModel(BaseModel):
    id: int
    bet_amount: int
    active: bool

    players: List[GameUser]
