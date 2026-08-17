"""Generated smoke tests for connect_four."""

from generated_code.generated_game import make_game
from src.alpha_beta import alpha_beta_cutoff_search

def run_generated_tests():
    game = make_game()
    state = game.initial_state()
    move, score = alpha_beta_cutoff_search(game, state, 1)
    assert move in game.legal_moves(state)
    assert isinstance(score, (int, float))
    return "ok"
