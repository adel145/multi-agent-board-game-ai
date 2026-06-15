"""Manual multi-agent pipeline for the board-game demo."""

import importlib.util
import json
import time
from pathlib import Path

from .code_generation import SafeCodeGenerator
from .game_interface import get_game
from .rag import LocalRulesRAG
from .vision import OllamaVisionClient, TEXT_MODEL, VISION_MODEL


GAME_LABELS = {
    "tic_tac_toe": "Tic-Tac-Toe",
    "connect_four": "Connect Four",
    "othello": "Othello / Reversi",
    "gomoku": "Gomoku / Five in a Row",
}


class TraceMixin:
    def _trace(self, trace, agent, action, result):
        trace.append({
            "step": len(trace) + 1,
            "time": time.strftime("%H:%M:%S"),
            "agent": agent,
            "action": action,
            "result": result,
        })


class VisionAgent(TraceMixin):
    def __init__(self):
        self.client = OllamaVisionClient(VISION_MODEL)

    def run(self, image_path, trace):
        description, live = self.client.describe(image_path)
        self._trace(trace, "VisionAgent", f"Call {VISION_MODEL}", "Ollama response" if live else "Fallback description")
        return {"description": description, "ollama_live": live}


class GameClassifierAgent(TraceMixin):
    def run(self, vision_result, trace):
        text = vision_result["description"].lower()
        scores = {
            "tic_tac_toe": sum(token in text for token in ["3x3", "three by three", "tic", "toe", "x and o", "x/o"]),
            "connect_four": sum(token in text for token in ["6x7", "six by seven", "connect", "vertical", "holes", "columns"]),
            "othello": sum(token in text for token in ["8x8", "eight by eight", "othello", "reversi", "black and white discs", "center"]),
            "gomoku": sum(token in text for token in ["gomoku", "five", "large square grid", "stones", "9x9", "nine by nine"]),
        }
        game_name = max(scores, key=scores.get)
        if scores[game_name] == 0:
            game_name = "tic_tac_toe"
        explanation = self._explain(game_name)
        self._trace(trace, "GameClassifierAgent", "Classify from visual features", f"{GAME_LABELS[game_name]} detected")
        return {"game_name": game_name, "label": GAME_LABELS[game_name], "scores": scores, "explanation": explanation}

    def _explain(self, game_name):
        explanations = {
            "tic_tac_toe": "The visual evidence points to a 3x3 X/O grid.",
            "connect_four": "The visual evidence points to a vertical 6x7 board with discs dropped into columns.",
            "othello": "The visual evidence points to an 8x8 board with black and white flippable discs.",
            "gomoku": "The visual evidence points to a larger square grid with black and white stones.",
        }
        return explanations[game_name]


class RulesRetrievalAgent(TraceMixin):
    def __init__(self, project_root):
        self.rag = LocalRulesRAG(project_root)

    def run(self, game_name, trace):
        chunks = self.rag.retrieve(game_name, query=GAME_LABELS[game_name])
        self._trace(trace, "RulesRetrievalAgent", "Retrieve local RAG chunks", f"{len(chunks)} chunk(s)")
        return chunks


class GameSpecAgent(TraceMixin):
    def run(self, classification, chunks, trace):
        game_name = classification["game_name"]
        game = get_game(game_name)
        spec = {
            "game_name": game_name,
            "display_name": classification["label"],
            "board": {"rows": game.rows, "cols": game.cols},
            "players": ["X", "O"],
            "required_interface": [
                "initial_state", "current_player", "legal_moves", "apply_move",
                "is_terminal", "utility", "evaluate", "render_state",
            ],
            "rules_summary": " ".join(chunk["text"] for chunk in chunks),
        }
        self._trace(trace, "GameSpecAgent", "Create structured JSON spec", f"{game.rows}x{game.cols} board")
        return spec


class CodeAgent(TraceMixin):
    def __init__(self, project_root):
        self.generator = SafeCodeGenerator(project_root)

    def run(self, spec, trace):
        files = self.generator.generate(spec)
        self._trace(trace, "CodeAgent", "Generate safe code in generated_code", f"{len(files)} file(s)")
        return files


class CriticTestAgent(TraceMixin):
    def __init__(self, project_root):
        self.project_root = Path(project_root)

    def run(self, spec, trace):
        game = get_game(spec["game_name"])
        missing = [name for name in spec["required_interface"] if not hasattr(game, name)]
        if missing:
            raise AssertionError(f"Missing interface methods: {missing}")
        test_path = self.project_root / "generated_code" / "generated_tests.py"
        module_spec = importlib.util.spec_from_file_location("generated_tests", test_path)
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
        generated_status = module.run_generated_tests()
        self._trace(trace, "CriticTestAgent", "Validate spec and generated tests", generated_status)
        return {"missing_methods": missing, "generated_tests": generated_status}


class UIAgent(TraceMixin):
    def run(self, spec, classification, chunks, trace):
        ui_data = {
            "title": spec["display_name"],
            "game_name": spec["game_name"],
            "explanation": classification["explanation"],
            "retrieved_rules": chunks,
            "spec_json": json.dumps(spec, indent=2),
        }
        self._trace(trace, "UIAgent", "Prepare Streamlit UI data", spec["display_name"])
        return ui_data


class SupervisorOrchestrator(TraceMixin):
    def __init__(self, project_root):
        self.project_root = project_root
        self.vision = VisionAgent()
        self.classifier = GameClassifierAgent()
        self.rules = RulesRetrievalAgent(project_root)
        self.spec = GameSpecAgent()
        self.code = CodeAgent(project_root)
        self.critic = CriticTestAgent(project_root)
        self.ui = UIAgent()

    def run(self, image_path):
        trace = []
        self._trace(trace, "SupervisorOrchestrator", "Start pipeline", "image -> playable game")
        vision = self.vision.run(image_path, trace)
        classification = self.classifier.run(vision, trace)
        chunks = self.rules.run(classification["game_name"], trace)
        spec = self.spec.run(classification, chunks, trace)
        generated_files = self.code.run(spec, trace)
        critic = self.critic.run(spec, trace)
        ui_data = self.ui.run(spec, classification, chunks, trace)
        self._trace(trace, "SupervisorOrchestrator", "Finish pipeline", "ready")
        return {
            "vision": vision,
            "classification": classification,
            "rules": chunks,
            "spec": spec,
            "generated_files": generated_files,
            "critic": critic,
            "ui": ui_data,
            "trace": trace,
            "models": {"text": TEXT_MODEL, "vision": VISION_MODEL},
        }
