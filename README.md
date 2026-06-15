# Multi-Agent Board-Game AI

Local AI project for board-game image recognition, RAG-based rule retrieval, safe code generation, and playable game AI with Minimax and Alpha-Beta Cutoff.

This project was built as a final project for a Generative AI / Agentic AI course. It focuses on transparent local orchestration: no cloud LLM APIs, no external agent frameworks, and no external game-tree libraries.

## Current Status

In progress. The full local pipeline, Streamlit UI, RAG flow, safe code generation, game implementations, and Alpha-Beta engine are implemented. Image classification uses local Ollama/LLaVA when available, but real-world classification quality still depends on the quality of the uploaded image and the local `llava:7b` response, so this part is the main area for future improvement.

## Main Features

- Local Streamlit app launched with `streamlit run app.py`
- Image selection from bundled test folders
- Manual image upload
- Local LLaVA vision analysis through Ollama
- Manual multi-agent pipeline with trace table
- RAG retrieval over local game rules
- Structured JSON game specification
- Safe generated Python adapters in `generated_code/`
- Playable board-game UI
- Shared Alpha-Beta Cutoff search engine
- Depth slider from 1 to 6
- Four supported games with one common interface

## Supported Games

- Tic-Tac-Toe
- Connect Four
- Othello / Reversi
- Gomoku / Five in a Row, simplified 9x9

## Architecture Overview

```text
Image
  -> VisionAgent
  -> GameClassifierAgent
  -> RulesRetrievalAgent
  -> GameSpecAgent
  -> CodeAgent
  -> CriticTestAgent
  -> UIAgent
  -> playable Streamlit game
```

The implementation is intentionally simple and inspectable. Each agent is a plain Python class in `src/agents.py`, coordinated by `SupervisorOrchestrator`. The project does not use AutoGen, CrewAI, LangGraph, LangChain Agents, or any other external agent framework.

## Multi-Agent Pipeline

- `VisionAgent`: sends image bytes to local Ollama using `llava:7b`.
- `GameClassifierAgent`: classifies from visual description features, not filenames.
- `RulesRetrievalAgent`: retrieves rules from local project data.
- `GameSpecAgent`: creates a structured JSON spec for the detected game.
- `CodeAgent`: writes generated files only to approved paths in `generated_code/`.
- `CriticTestAgent`: validates the interface and runs generated smoke tests.
- `UIAgent`: prepares Streamlit display data.
- `SupervisorOrchestrator`: runs the full workflow and records an agent trace.

## Tech Stack

- Python
- Streamlit
- Ollama
- `llava:7b` for vision
- `llama3.2:3b` as the allowed text model constant
- Local JSON-backed RAG store
- Handwritten Minimax with Alpha-Beta Cutoff

Only these model names are used:

```python
TEXT_MODEL = "llama3.2:3b"
VISION_MODEL = "llava:7b"
```

## How To Run

From the project folder:

```bash
streamlit run app.py
```

Then:

1. Select a bundled test image or upload a new image.
2. Click `Run Demo`.
3. Review the detected game, rules, JSON spec, generated code status, and trace.
4. Play against the Alpha-Beta AI using the depth slider.

## Project Structure

```text
final_project/
├── app.py
├── README.md
├── CODEX.md
├── data/
│   ├── game_images_catalog.pdf
│   ├── game_rules.pdf
│   └── test_images/
├── generated_code/
├── extracted/
├── vector_store/
└── src/
    ├── agents.py
    ├── rag.py
    ├── vision.py
    ├── game_interface.py
    ├── alpha_beta.py
    ├── code_generation.py
    ├── safety.py
    └── streamlit_helpers.py
```

## Screenshots

Screenshots will be added after the app is run in an environment with Streamlit installed.

Suggested screenshots:

- Main image selection and upload screen
- Agent trace table
- Retrieved rules and structured game spec
- Playable game board with AI move output

## Safety

Generated code is restricted to:

- `generated_code/generated_game.py`
- `generated_code/generated_tests.py`
- `generated_code/generated_streamlit_helpers.py`

The safety layer blocks absolute paths, parent traversal, home paths, Windows drive paths, writes to source/data/app files, and dangerous patterns such as `os.system`, `subprocess`, `eval`, `exec`, unsafe dynamic imports, unsafe `open`, and network access.

## Verification

Verified locally on 2026-06-15:

```bash
py -m compileall .
```

Result: passed.

Backend smoke tests passed for:

- Alpha-Beta legal move selection on all four games at depth 1
- RAG retrieval from `data/game_rules.pdf` / extracted local text
- Full backend orchestrator path, including generated files and critic tests

Known local environment limitation:

```bash
py -m streamlit run app.py
```

Result on this machine: `No module named streamlit`. The project design was not changed. In the course/lab environment with Streamlit installed, use the required command:

```bash
streamlit run app.py
```

## Known Limitations

- Image classification quality depends on local Ollama and `llava:7b` output.
- The fallback mode keeps the app from crashing if Ollama is unavailable, but true visual recognition requires local LLaVA.
- The included screenshots section is currently a placeholder.
- The rules source is mirrored as extracted text so the app can run without requiring a PDF parser package.

## What I Learned

This project connects several AI engineering ideas into one runnable system: multimodal perception, retrieval, agent orchestration, code safety, deterministic game logic, and adversarial search. The most important lesson was how to keep an AI pipeline inspectable and bounded: each agent has a narrow role, generated code is sandboxed to approved files, and the game AI relies on a transparent Alpha-Beta implementation instead of a black-box library.

## Why This Project Matters

Many AI demos stop at generating text. This project goes further by turning a visual input into a working interactive system with retrieval, validation, generated artifacts, and a playable AI opponent. It demonstrates practical engineering habits that matter in production-style AI work: local execution, traceability, safety checks, graceful failure modes, and clear separation between model-driven reasoning and trusted deterministic logic.

