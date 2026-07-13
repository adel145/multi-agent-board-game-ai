"""Generated safe adapter for connect_four (Fallback)."""

from src.game_interface import get_game

GAME_NAME = "connect_four"

def make_game():
    return get_game(GAME_NAME)
