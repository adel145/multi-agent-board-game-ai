"""Small local RAG implementation for board-game rules."""

import json
import importlib
import re
from pathlib import Path


DEFAULT_RULES = """
# Tic-Tac-Toe
Tic-Tac-Toe uses a 3x3 grid. Players X and O alternate placing marks in empty
cells. A player wins by making three in a row horizontally, vertically, or
diagonally. If the grid fills without a line, the game is a draw.

# Connect Four
Connect Four uses a vertical 6x7 board. Players drop discs into columns; the
disc falls to the lowest empty slot. A player wins by connecting four discs
horizontally, vertically, or diagonally. If no columns remain and no player has
four in a row, the game is a draw.

# Othello / Reversi
Othello uses an 8x8 board with four center discs at the start. A legal move
places a disc so one or more opponent discs are bracketed in a straight line
between the new disc and another friendly disc. Bracketed discs flip color.
If a player has no legal move, the player passes. The game ends when neither
player can move or the board is full; the higher disc count wins.

# Gomoku / Five in a Row
Simplified Gomoku uses a 9x9 square grid. Players place black and white stones
on empty intersections or cells. A player wins by forming five stones in a row
horizontally, vertically, or diagonally. If the board fills first, the game is a
draw.
"""


class LocalRulesRAG:
    def __init__(self, project_root):
        self.root = Path(project_root)
        self.data_pdf = self.root / "data" / "game_rules.pdf"
        self.text_path = self.root / "extracted" / "text" / "game_rules.txt"
        self.store_path = self.root / "vector_store" / "rules_store.json"

    def ensure_sources(self):
        self.text_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.data_pdf.exists():
            # הערה בעברית: זה קובץ מקור מקומי לקריאה; האפליקציה לא תלויה בספריית PDF חיצונית.
            self.data_pdf.write_text(DEFAULT_RULES, encoding="utf-8")
        if not self.text_path.exists():
            self.text_path.write_text(self._extract_rules_source(), encoding="utf-8")

    def extract_text(self):
        self.ensure_sources()
        text = self._extract_rules_source()
        # הערה בעברית: קובץ הטקסט הוא תוצר חילוץ מקומי מתוך data/game_rules.pdf.
        self.text_path.write_text(text, encoding="utf-8")
        return text

    def _extract_rules_source(self):
        """Read the required rules file, with optional PDF parser support.

        In the lab this can work with a plain text-backed ``game_rules.pdf`` or,
        if a real PDF and PyPDF2/pypdf are available, with extracted PDF pages.
        """
        raw = self.data_pdf.read_bytes() if self.data_pdf.exists() else b""
        if not raw:
            return DEFAULT_RULES
        if raw.startswith(b"%PDF"):
            parsed = self._try_pdf_libraries()
            return parsed or DEFAULT_RULES
        for encoding in ("utf-8", "utf-16", "cp1255", "latin-1"):
            try:
                text = raw.decode(encoding)
                if "Tic-Tac-Toe" in text and "Gomoku" in text:
                    return text
            except UnicodeDecodeError:
                continue
        return DEFAULT_RULES

    def _try_pdf_libraries(self):
        for module_name in ("pypdf", "PyPDF2"):
            try:
                module = importlib.import_module(module_name)
                reader = module.PdfReader(str(self.data_pdf))
                pages = [page.extract_text() or "" for page in reader.pages]
                text = "\n".join(pages).strip()
                if text:
                    return text
            except Exception:
                continue
        return ""

    def chunk_text(self, text):
        sections = re.split(r"\n(?=# )", text.strip())
        chunks = []
        for section in sections:
            title = section.splitlines()[0].replace("#", "").strip().lower()
            key = "general"
            if "tic" in title:
                key = "tic_tac_toe"
            elif "connect" in title:
                key = "connect_four"
            elif "othello" in title or "reversi" in title:
                key = "othello"
            elif "gomoku" in title or "five" in title:
                key = "gomoku"
            chunks.append({"game": key, "text": section.strip()})
        return chunks

    def build_or_load(self):
        self.ensure_sources()
        text = self.extract_text()
        chunks = self.chunk_text(text)
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self.store_path.write_text(json.dumps(chunks, indent=2), encoding="utf-8")
        return chunks

    def retrieve(self, game_name, query="", k=3):
        chunks = self.build_or_load()
        query_terms = set(re.findall(r"[a-z0-9]+", f"{game_name} {query}".lower()))

        def score(chunk):
            text = chunk["text"].lower()
            exact = 10 if chunk["game"] == game_name else 0
            lexical = sum(1 for term in query_terms if term in text)
            return exact + lexical

        ranked = sorted(chunks, key=score, reverse=True)
        return ranked[:k]
