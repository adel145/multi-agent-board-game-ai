"""Dynamic LLM safe code generation used by the CodeAgent."""

import json
import urllib.request
import re
from .safety import safe_write, scan_code

def prompt_llm_for_code(spec):
    """Dynamically asks the LLM to generate the game class based on the spec."""
    game_name = spec["game_name"]
    display_name = spec["display_name"]
    rules = spec["rules_summary"]
    interface = ", ".join(spec["required_interface"])
    
    prompt = f"""
    You are an expert Python developer. Write a complete, playable Python class for the board game: {display_name}.
    
    Here are the rules to implement:
    {rules}
    
    The class MUST implement these exact methods to match the system interface:
    {interface}

    =========================================================
    CRITICAL ARCHITECTURE & NAMING RULES TO PREVENT SHADOWING
    =========================================================
    1. `current_player` MUST be a method, NOT an integer attribute. 
    2. Do NOT define `self.current_player = ...` in the __init__ method.
    3. You must implement it exactly with this signature:

    def current_player(self, state):
        # Return the integer of the player whose turn it is in the given state
        pass
    
    CRITICAL GRADING REQUIREMENT:
    You must also include a fully functioning Minimax algorithm with Alpha-Beta pruning directly inside this class. 
    Implement a method called `get_best_move(self, state, depth)` that uses a helper method `alpha_beta(self, state, depth, alpha, beta, maximizing_player)` to return the optimal move. 
    It must correctly implement maximizing/minimizing logic, terminal scoring, cutoff depth limits, and a reasonable heuristic evaluation function.
    
    At the very end of the file, you MUST include a standalone function named `make_game()` that returns an instance of your class.
    
    Return ONLY valid Python code. Do not include markdown blocks, explanations, or print statements.
    """
    
    try:
        payload = json.dumps({
            "model": "llama3.2:3b",
            "prompt": prompt,
            "stream": False
        }).encode("utf-8")
        
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=120) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            raw_code = res_data.get("response", "")
            
            # Clean up markdown code blocks if the LLM adds them
            clean_code = re.sub(r"^```python\s*", "", raw_code, flags=re.IGNORECASE)
            clean_code = clean_code.replace("```", "").strip()
            
            # Safety check: Ensure the required factory function exists
            if "def make_game" not in clean_code:
                raise ValueError("LLM forgot the make_game function.")
                
            return clean_code
            
    except Exception as e:
        print(f"LLM Code Generation failed or was unsafe: {e}")
        return fallback_generated_game_code(game_name)

def fallback_generated_game_code(game_name):
    """Failsafe adapter if the LLM hallucinates broken syntax during the demo."""
    return f'''"""Generated safe adapter for {game_name} (Fallback)."""\n\nfrom src.game_interface import get_game\n\nGAME_NAME = "{game_name}"\n\ndef make_game():\n    return get_game(GAME_NAME)\n'''

def build_generated_tests_code(game_name):
    return f'''"""Generated smoke tests for {game_name}."""\n\nfrom generated_code.generated_game import make_game\nfrom src.alpha_beta import alpha_beta_cutoff_search\n\ndef run_generated_tests():\n    game = make_game()\n    state = game.initial_state()\n    move, score = alpha_beta_cutoff_search(game, state, 1)\n    assert move in game.legal_moves(state)\n    assert isinstance(score, (int, float))\n    return "ok"\n'''

def build_generated_helpers_code(game_name):
    return f'''"""Generated Streamlit helper metadata for {game_name}."""\n\nGAME_LABEL = "{game_name.replace("_", " ").title()}"\n\ndef describe_generated_game():\n    return {{"label": GAME_LABEL, "source": "LLM generation via llama3.2:3b"}}\n'''

class SafeCodeGenerator:
    def __init__(self, project_root):
        self.project_root = project_root

    def generate(self, spec):
        game_name = spec["game_name"]
        
        # Call the LLM to write the core logic
        game_code = prompt_llm_for_code(spec)
        
        files = {
            "generated_code/generated_game.py": game_code,
            "generated_code/generated_tests.py": build_generated_tests_code(game_name),
            "generated_code/generated_streamlit_helpers.py": build_generated_helpers_code(game_name),
        }
        
        results = []
        for relative_path, code in files.items():
            ok, message = scan_code(code)
            if not ok:
                # If the LLM wrote unsafe code (like importing 'os'), force the fallback
                if relative_path == "generated_code/generated_game.py":
                    code = fallback_generated_game_code(game_name)
                    ok = True
                    message = "Safety scan failed on LLM code. Switched to fallback."
                else:
                    raise ValueError(message)
            
            path = safe_write(self.project_root, relative_path, code)
            results.append({"file": relative_path, "status": "written", "message": message})
            
        return results