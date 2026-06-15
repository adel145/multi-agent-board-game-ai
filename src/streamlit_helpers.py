"""Streamlit UI helpers."""

from pathlib import Path

from .alpha_beta import alpha_beta_cutoff_search


def list_test_images(project_root):
    base = Path(project_root) / "data" / "test_images"
    images = []
    for path in sorted(base.rglob("*")):
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            images.append(path)
    return images


def save_upload(project_root, uploaded_file):
    target = Path(project_root) / "extracted" / "uploaded_images" / uploaded_file.name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(uploaded_file.getbuffer())
    return target


def board_to_html(state):
    rows = []
    for row in state["board"]:
        rows.append(" ".join(row))
    return "\n".join(rows)


def make_ai_move(game, state, depth):
    # הערה בעברית: אותו מנוע אלפא-בטא עובד לכל המשחקים דרך הממשק האחיד.
    move, score = alpha_beta_cutoff_search(game, state, depth)
    if move is None:
        return state, move, score
    return game.apply_move(state, move), move, score

