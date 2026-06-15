"""Deterministic safe code generation used by the CodeAgent."""

from .safety import safe_write, scan_code


def build_generated_game_code(game_name):
    return f'''"""Generated safe adapter for {game_name}."""

from src.game_interface import get_game


GAME_NAME = "{game_name}"


def make_game():
    return get_game(GAME_NAME)


def smoke_test():
    game = make_game()
    state = game.initial_state()
    moves = game.legal_moves(state)
    return bool(moves), game.current_player(state)
'''


def build_generated_tests_code(game_name):
    return f'''"""Generated smoke tests for {game_name}."""

from generated_code.generated_game import make_game
from src.alpha_beta import alpha_beta_cutoff_search


def run_generated_tests():
    game = make_game()
    state = game.initial_state()
    move, score = alpha_beta_cutoff_search(game, state, 1)
    assert move in game.legal_moves(state)
    assert isinstance(score, (int, float))
    return "ok"
'''


def build_generated_helpers_code(game_name):
    return f'''"""Generated Streamlit helper metadata for {game_name}."""

GAME_LABEL = "{game_name.replace("_", " ").title()}"


def describe_generated_game():
    return {{"label": GAME_LABEL, "source": "safe deterministic generator"}}
'''


class SafeCodeGenerator:
    def __init__(self, project_root):
        self.project_root = project_root

    def generate(self, spec):
        game_name = spec["game_name"]
        files = {
            "generated_code/generated_game.py": build_generated_game_code(game_name),
            "generated_code/generated_tests.py": build_generated_tests_code(game_name),
            "generated_code/generated_streamlit_helpers.py": build_generated_helpers_code(game_name),
        }
        results = []
        for relative_path, code in files.items():
            ok, message = scan_code(code)
            if not ok:
                raise ValueError(message)
            path = safe_write(self.project_root, relative_path, code)
            results.append({"file": relative_path, "status": "written", "message": str(path)})
        return results

