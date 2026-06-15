"""Generated safe adapter for tic_tac_toe."""

from src.game_interface import get_game


GAME_NAME = "tic_tac_toe"


def make_game():
    return get_game(GAME_NAME)


def smoke_test():
    game = make_game()
    state = game.initial_state()
    moves = game.legal_moves(state)
    return bool(moves), game.current_player(state)
