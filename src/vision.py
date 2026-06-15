"""Vision calls for Ollama LLaVA plus local fallback descriptions."""

import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

TEXT_MODEL = "llama3.2:3b"
VISION_MODEL = "llava:7b"


class OllamaVisionClient:
    def __init__(self, model=VISION_MODEL, host="http://localhost:11434"):
        self.model = model
        self.host = host.rstrip("/")

    def describe(self, image_path):
        prompt = (
            "Describe the board game image. Focus on grid size, symbols, discs, "
            "stones, board orientation, and whether it resembles tic-tac-toe, "
            "connect four, othello/reversi, or gomoku."
        )
        try:
            image_b64 = base64.b64encode(Path(image_path).read_bytes()).decode("ascii")
            payload = json.dumps({
                "model": self.model,
                "prompt": prompt,
                "images": [image_b64],
                "stream": False,
            }).encode("utf-8")
            req = urllib.request.Request(
                f"{self.host}/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=45) as response:
                data = json.loads(response.read().decode("utf-8"))
                return data.get("response", "").strip(), True
        except (OSError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            # הערה בעברית: אם Ollama לא פעיל, האפליקציה עדיין עובדת עם תיאור גיבוי שמבוסס על הבחירה.
            return self.fallback_description(image_path, exc), False

    def fallback_description(self, image_path, exc=None):
        size_text = self._read_png_size(image_path)
        return (
            "Fallback visual description: Ollama/LLaVA was not reachable, so no "
            f"filename-based game decision was made. Image metadata: {size_text}. "
            "Run with local llava:7b for visual grid and piece recognition."
        )

    def _read_png_size(self, image_path):
        try:
            data = Path(image_path).read_bytes()
            if data.startswith(b"\x89PNG\r\n\x1a\n"):
                width = int.from_bytes(data[16:20], "big")
                height = int.from_bytes(data[20:24], "big")
                return f"PNG {width}x{height}"
        except OSError:
            pass
        return "size unavailable"
