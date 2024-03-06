from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from decimal import Decimal
from routes.coinflip.coinflip_models import Coinflip, CoinflipLink


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, unique=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(unique=True)
    password: str
    coins: Decimal = Field(default=0, max_digits=12, decimal_places=4)
    level: int = Field(default=1)
    
    coinflipgames: List["Coinflip"] = Relationship(back_populates="players", link_model=CoinflipLink)


class SignInBody(BaseModel):
    email: str
    password: str


class SignUpBody(BaseModel):
    username: str
    email: str
    password: str
