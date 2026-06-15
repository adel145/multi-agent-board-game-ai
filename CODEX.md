# Oral Defense Notes

## Architecture

This project is a local Streamlit application named `final_project`. The required command is:

```bash
streamlit run app.py
```

The pipeline is a manual multi-agent design implemented with ordinary Python classes in `src/agents.py`. No external agent framework is used.

## Agents

- `VisionAgent`: calls Ollama with `llava:7b` and asks for visual board features. It records whether the real Ollama call succeeded.
- `GameClassifierAgent`: maps visual clues to one of four games only. It uses features such as 3x3 X/O grid, vertical 6x7 holes, 8x8 discs, or a larger stone grid.
- `RulesRetrievalAgent`: uses local RAG from `src/rag.py`, builds/reuses `vector_store/rules_store.json`, and retrieves rule chunks.
- `GameSpecAgent`: creates a JSON spec with game name, board shape, players, required methods, and retrieved rules.
- `CodeAgent`: writes deterministic safe generated files only in `generated_code/`.
- `CriticTestAgent`: checks that the game implements the common interface and runs generated smoke tests.
- `UIAgent`: prepares data for Streamlit display.
- `SupervisorOrchestrator`: runs the full sequence and stores a trace table.

## Game Logic

The four supported games are implemented in `src/game_interface.py`:

- Tic-Tac-Toe: 3x3, three in a row.
- Connect Four: 6x7, gravity in columns, four in a row.
- Othello/Reversi: 8x8, legal bracket captures, pass when no move.
- Gomoku: simplified 9x9, five in a row.

Important code comments are written in Hebrew near the core stopping condition, heuristic logic, RAG fallback, Ollama fallback, and shared AI move flow.

## Alpha-Beta

`src/alpha_beta.py` implements minimax with alpha-beta pruning by hand. It only depends on the common game interface. It stops on:

- terminal state,
- cutoff depth,
- no legal moves.

At cutoff depth, it calls `game.evaluate(state, player)`. At terminal states, it calls `game.utility(state, player)`.

## RAG

The app keeps rule text in `data/game_rules.pdf` and `extracted/text/game_rules.txt`. `LocalRulesRAG` chunks by section, stores chunks in `vector_store/rules_store.json`, and retrieves the most relevant chunks for the detected game.

The implementation intentionally avoids mandatory PDF parsing dependencies so the grader can run the app with just Streamlit and local Python.

## Safety

`src/safety.py` enforces:

- allowed generated filenames only,
- no absolute paths,
- no `..`,
- no `~`,
- no Windows drive paths,
- no writes to `app.py`, `src/`, or `data/`,
- no dangerous code patterns such as `os.system`, `subprocess`, `eval`, `exec`, `__import__`, unsafe `open`, or network access.

## Streamlit UI

The UI includes:

- test image selector,
- manual image uploader,
- selected image display,
- Run Demo and Reset buttons,
- detected game and explanation,
- LLaVA/fallback visual description,
- retrieved rules,
- JSON game spec,
- generated code and critic status,
- trace table,
- playable board,
- alpha-beta depth slider from 1 to 6, default 3.

## Defense Talking Point

The design separates perception, classification, retrieval, specification, generation, criticism, and UI. Each piece is inspectable and local. The playable game does not execute arbitrary LLM code; generated code is a safe adapter around tested built-in game implementations.

## Final Verification Results

Verification was run from inside `final_project/` on 2026-06-15.

Commands and results:

```bash
py -m compileall .
```

Result: passed. All Python files in `app.py`, `src/`, and `generated_code/` compiled successfully.

```bash
py -m streamlit run app.py
```

Result: blocked by the local Python environment because Streamlit is not installed:

```text
No module named streamlit
```

This is an environment/package issue only. The project design was not changed. In the lab environment where Streamlit is already installed, the required command remains:

```bash
streamlit run app.py
```

Additional smoke checks:

```bash
py -c "from src.game_interface import get_game; from src.alpha_beta import alpha_beta_cutoff_search; ..."
```

Result: passed for all four games at depth 1:

- `tic_tac_toe`: returned legal move `(1, 1)`
- `connect_four`: returned legal move `3`
- `othello`: returned legal move `(2, 3)`
- `gomoku`: returned legal move `(4, 4)`

Backend pipeline check:

```bash
py -c "from pathlib import Path; from src.agents import SupervisorOrchestrator; ..."
```

Result: passed without Streamlit. The orchestrator ran on a bundled test image, generated the safe files, the critic returned `ok`, and the trace contained 9 steps.

RAG verification:

```bash
py -c "from pathlib import Path; from src.rag import LocalRulesRAG; ..."
```

Result: passed. `LocalRulesRAG` reads `data/game_rules.pdf`, writes/syncs the extracted text to `extracted/text/game_rules.txt`, rebuilds `vector_store/rules_store.json`, and retrieves relevant chunks. The Othello check returned an Othello chunk containing the Othello rules.

Static safety/model checks:

- No OpenAI, Claude, Gemini, LangChain, AutoGen, CrewAI, or LangGraph dependency is used.
- The only model constants are `TEXT_MODEL = "llama3.2:3b"` and `VISION_MODEL = "llava:7b"`.
- Dangerous strings found in `src/safety.py` are the blocked-pattern list used by the safety scanner, not executable dangerous behavior.

## Exact Defense Explanation

For game detection, the selected file path is used only so Streamlit can load and display the image. The actual classification path is:

1. `VisionAgent` sends the image bytes to local Ollama using `VISION_MODEL = "llava:7b"`.
2. LLaVA returns a visual description of board features.
3. `GameClassifierAgent` classifies from the description text only, using features like `3x3`, `6x7`, `8x8`, discs, stones, holes, and columns.
4. The classifier does not inspect the filename, folder name, or known test-image identity.

If Ollama is unavailable, `VisionAgent` returns a fallback message that explicitly says no filename-based game decision was made. This keeps the UI from crashing, but real visual recognition requires local `llava:7b`.

For RAG, `LocalRulesRAG` treats `data/game_rules.pdf` as the required source file. On retrieval it extracts or reads that source, syncs the extracted text into `extracted/text/game_rules.txt`, chunks sections by game, writes the reusable local store to `vector_store/rules_store.json`, and returns chunks for the detected game. The retrieved rules are then included in the structured game spec and displayed in the Streamlit UI.

For the AI player, `alpha_beta_cutoff_search` is handwritten in `src/alpha_beta.py`. It never imports an external game-tree library. It works through the shared game interface, stops at terminal states, stops at the selected cutoff depth, calls `evaluate` at cutoff states, calls `utility` at terminal states, applies alpha and beta pruning, and returns a legal move plus score.
