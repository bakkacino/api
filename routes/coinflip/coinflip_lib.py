from fastapi import WebSocket
import json
from typing import List


class Games:
    def __init__(self, game_id: int):
        self.game_id = game_id
        self.players: List[WebSocket] = []


class CoinflipGameConnectionManager:
    def __init__(self):
        self.active_games: list[Games] = []

    async def connect(self, websocket: WebSocket, game_id: int):
        game = self.get_game_by_id(game_id)
        if game:
            game.players.append(websocket)
        else:
            new_game = Games(game_id)
            new_game.players.append(websocket)
            self.active_games.append(new_game)

    async def disconnect(self, websocket: WebSocket):
        for game in self.active_games:
            if websocket in game.players:
                game.players.remove(websocket)

    async def send_personal_message(self, message: json, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: json):
        for game in self.active_games:
            for player in game.players:
                await player.send_json(message)
                
    async def send_message_to_game(self, game_id: int, message: json):
        game = self.get_game_by_id(game_id)
        if game:
            for player in game.players:
                await player.send_json(message)
                
    def get_game_by_id(self, game_id: int):
        for game in self.active_games:
            if game.game_id == game_id:
                return game
        return None

    def cleanup_game(self, game_id: int):
        self.active_games = [game for game in self.active_games if game.game_id != game_id]
        
    async def game_ready(self, game_id: int):
        game = self.get_game_by_id(game_id)
        if game:
            if len(game.players) == 2:
                await self.send_message_to_game(game_id, {"message": "test"})
                return True
        return False
    
    async def is_host(self, game_id: int, websocket: WebSocket):
        game = self.get_game_by_id(game_id)
        if game:
            if game.players[0] == websocket:
                return True
            else:
                return False
        return False
    