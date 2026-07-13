from pathlib import Path
import importlib.util
import sys
import streamlit as st

from src.agents import SupervisorOrchestrator
from src.game_interface import EMPTY, get_game
from src.streamlit_helpers import list_test_images, make_ai_move, save_upload


PROJECT_ROOT = Path(__file__).parent.resolve()


def reset_demo():
    for key in ["pipeline", "selected_image", "game_state", "play_game_name", "last_ai"]:
        st.session_state.pop(key, None)


def move_label(move):
    if move == "pass":
        return "pass"
    if isinstance(move, tuple):
        return f"{move[0]}, {move[1]}"
    return str(move)


def load_playable_game(game_name):
    generated_path = PROJECT_ROOT / "generated_code" / "generated_game.py"
    if generated_path.exists():
        # Clear the module from Python's cache if it exists
        if "generated_game_runtime" in sys.modules:
            del sys.modules["generated_game_runtime"]
            
        spec = importlib.util.spec_from_file_location("generated_game_runtime", generated_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.make_game()
    return get_game(game_name)

def get_piece_label(game_name, cell):
    """Maps the internal X and O logic to specific colored shapes."""
    from src.game_interface import EMPTY
    if cell == EMPTY:
        return " "
        
    themes = {
        "connect_four": {"X": "🔴", "O": "🟡"},  # Red and Yellow circles
        "gomoku": {"X": "⚫", "O": "⚪"},        # Black and White stones
        "othello": {"X": "⚫", "O": "⚪"},       # Black and White discs
        "tic_tac_toe": {"X": "❌", "O": "⭕"}      # Stylized Cross and Ring
    }
    return themes.get(game_name, {}).get(cell, cell)


def inject_dynamic_css(game_name):
    """Injects CSS to theme the board background and button shapes based on the game."""
    css = """
    <style>
    /* Base button text size and alignment */
    div[data-testid="stButton"] button {
        height: 70px;
        width: 100%;
        font-size: 32px !important;
        font-weight: bold;
        transition: all 0.2s ease-in-out;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    div[data-testid="stButton"] button:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    """
    
    if game_name == "connect_four":
        css += """
        /* Classic blue vertical board */
        div[data-testid="stVerticalBlock"] > div > div > div[data-testid="stHorizontalBlock"] {
            background-color: #1e40af; /* Deep blue */
            padding: 10px;
            border-radius: 12px;
            box-shadow: inset 0 -4px 10px rgba(0,0,0,0.5);
        }
        /* Circular cutouts for the board */
        div[data-testid="stButton"] button {
            border-radius: 50%;
            background-color: #0f172a; /* Dark empty hole */
            border: 3px solid #1e3a8a;
        }
        """
    elif game_name == "othello":
        css += """
        /* Green felt board with wood borders */
        div[data-testid="stVerticalBlock"] > div > div > div[data-testid="stHorizontalBlock"] {
            background-color: #166534; /* Dark green felt */
            padding: 8px;
            border-radius: 4px;
            border: 6px solid #452c10; /* Wood border */
        }
        div[data-testid="stButton"] button {
            border-radius: 50%;
            background-color: #14532d;
            border: 1px solid #166534;
        }
        """
    elif game_name == "gomoku":
        css += """
        /* Light wooden Go board */
        div[data-testid="stVerticalBlock"] > div > div > div[data-testid="stHorizontalBlock"] {
            background-color: #d97706; /* Wood tone */
            padding: 10px;
            border-radius: 4px;
            /* Subtle grid lines */
            background-image: repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(0,0,0,0.03) 10px, rgba(0,0,0,0.03) 20px);
        }
        div[data-testid="stButton"] button {
            border-radius: 50%;
            background-color: rgba(0,0,0,0.05); /* Very subtle empty space */
            border: none;
        }
        """
    else: # tic_tac_toe
        css += """
        /* Modern dark stone aesthetic */
        div[data-testid="stVerticalBlock"] > div > div > div[data-testid="stHorizontalBlock"] {
            background-color: #2b2b36;
            padding: 5px;
            border-radius: 12px;
        }
        div[data-testid="stButton"] button {
            border-radius: 12px;
            background-color: #1e1e28;
            border: 2px solid #3a3a4a;
        }
        """
        
    css += "</style>"
    st.markdown(css, unsafe_allow_html=True)


def render_board(game, state, depth):
    st.subheader("Playable AI Game")
    st.caption(f"Turn: {game.current_player(state)}")
    
    # Inject the specific CSS for the currently detected game
    inject_dynamic_css(game.name)
    
    board = state["board"]
    for r, row in enumerate(board):
        cols = st.columns(len(row))
        for c, cell in enumerate(row):
            # Use the new mapping function instead of raw 'X' and 'O'
            label = get_piece_label(game.name, cell)
            
            disabled = (r, c) not in game.legal_moves(state) or game.is_terminal(state)
            if game.name == "connect_four":
                disabled = c not in game.legal_moves(state) or game.is_terminal(state)
                
            with cols[c]:
                if st.button(label, key=f"cell_{game.name}_{r}_{c}", disabled=disabled, use_container_width=True):
                    move = c if game.name == "connect_four" else (r, c)
                    st.session_state.game_state = game.apply_move(state, move)
                    st.rerun()
                    
    legal = game.legal_moves(st.session_state.game_state)
    if legal == ["pass"] and st.button("Pass"):
        st.session_state.game_state = game.apply_move(st.session_state.game_state, "pass")
        st.rerun()
        
    left, right = st.columns(2)
    with left:
        if st.button("AI Move", disabled=game.is_terminal(st.session_state.game_state), use_container_width=True):
            new_state, move, score = make_ai_move(game, st.session_state.game_state, depth)
            st.session_state.game_state = new_state
            st.session_state.last_ai = {"move": move_label(move), "score": score}
            st.rerun()
    with right:
        if st.button("New Game", use_container_width=True):
            st.session_state.game_state = game.initial_state()
            st.session_state.last_ai = None
            st.rerun()
            
    if st.session_state.get("last_ai"):
        st.info(f"AI chose {st.session_state.last_ai['move']} with score {st.session_state.last_ai['score']}.")
    if game.is_terminal(st.session_state.game_state):
        st.success(f"Game over. Utility for X: {game.utility(st.session_state.game_state, 'X')}")


def main():
    st.set_page_config(page_title="Multi-Agent Board Game AI", layout="wide")
    st.title("Multi-Agent Board-Game Recognition and Play")
    st.write("Local Streamlit demo using Ollama LLaVA, local RAG, safe code generation, and Alpha-Beta search.")

    depth = st.slider("Alpha-Beta depth", 1, 6, 3)
    images = list_test_images(PROJECT_ROOT)
    options = [""] + [str(path.relative_to(PROJECT_ROOT)) for path in images]
    selected = st.selectbox("Choose image from test folders", options)
    uploaded = st.file_uploader("Upload image manually", type=["png", "jpg", "jpeg", "webp"])

    if uploaded:
        st.session_state.selected_image = save_upload(PROJECT_ROOT, uploaded)
    elif selected:
        st.session_state.selected_image = PROJECT_ROOT / selected

    if st.session_state.get("selected_image"):
        st.image(str(st.session_state.selected_image), caption=str(st.session_state.selected_image), width=420)

    c1, c2 = st.columns(2)
    with c1:
        run = st.button("Run Demo", type="primary", use_container_width=True, disabled=not st.session_state.get("selected_image"))
    with c2:
        if st.button("Reset", use_container_width=True):
            reset_demo()
            st.rerun()

    if run:
        with st.spinner("Running manual agent pipeline..."):
            orchestrator = SupervisorOrchestrator(PROJECT_ROOT)
            st.session_state.pipeline = orchestrator.run(st.session_state.selected_image)
            game_name = st.session_state.pipeline["classification"]["game_name"]
            st.session_state.play_game_name = game_name
            st.session_state.game_state = get_game(game_name).initial_state()

    if st.session_state.get("pipeline"):
        result = st.session_state.pipeline
        st.header(result["classification"]["label"])
        st.write(result["classification"]["explanation"])
        st.caption(f"Models: TEXT_MODEL={result['models']['text']} | VISION_MODEL={result['models']['vision']}")
        st.subheader("LLaVA Description")
        st.write(result["vision"]["description"])

        left, right = st.columns(2)
        with left:
            st.subheader("Retrieved Rules from RAG")
            for chunk in result["rules"]:
                st.markdown(chunk["text"])
        with right:
            st.subheader("Structured Game Spec")
            st.json(result["spec"])

        st.subheader("Generated Code and Critic")
        st.write(result["generated_files"])
        st.write(result["critic"])

        st.subheader("Agent Trace")
        st.dataframe(result["trace"], use_container_width=True)

        game = load_playable_game(st.session_state.play_game_name)
        if "game_state" not in st.session_state:
            st.session_state.game_state = game.initial_state()
        render_board(game, st.session_state.game_state, depth)


if __name__ == "__main__":
    main()
