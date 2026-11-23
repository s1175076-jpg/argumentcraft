---
title: ArgumentCraft
emoji: 🧠
colorFrom: yellow
colorTo: orange
sdk: docker
pinned: false
app_port: 7860
---

# ArgumentCraft · Argumentation & Debate Platform (MVP)

ArgumentCraft is an AI-in-Education prototype for argument practice. It combines the **Toulmin model** with an AI debate partner that uses **multi-turn Socratic questioning** to create cognitive conflict, and provides **thinking visualization** to help learners examine and revise their arguments.

## Core Features

- **Toulmin Argument Map**: Build Claim / Grounds / Warrant / Backing / Qualifier / Rebuttal.
- **Socratic AI Debate**: The AI asks 1–3 focused questions per turn, challenging evidence, reasoning, assumptions, qualifiers, and counterarguments.
- **Cognitive Conflict Visualization**: Shows challenge focus, conflict level (1–5), Toulmin feedback, and suggested revisions.
- **Multi-turn Dialogue**: Learners respond and continue the debate to iteratively improve their argument.
- **Shared Prompts & Roles**: Teachers can publish a class prompt; students can practice published prompts or self-directed topics. Demo accounts are included.
- **Export**: Export the current debate record (topic, Toulmin map, dialogue, AI feedback, JSON) as Markdown.
- **OpenAI-Compatible API**: Supports OpenAI or compatible endpoints (configure API key / Base URL / Model in the app).

## Tech Stack

- Python + FastAPI + Uvicorn
- OpenAI Python SDK (OpenAI-style Chat Completions API)
- HTML/CSS/JS frontend (served as static files)
- SQLite (`sqlite3`) for local users, tokens, assignments, and saved sessions

## Run in PyCharm

1. Open the project directory: `final-web`.
2. Create a virtual environment (PyCharm: Settings/Preferences → Python Interpreter → Add Interpreter).
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run `main.py` (recommended), or use:

   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8004
   ```

5. Open the browser:
   - Home (sign in/register): <http://127.0.0.1:8004/>
   - Main app: <http://127.0.0.1:8004/app>

6. Click **API** in the app and configure:
   - **API Key**: your OpenAI/compatible key
   - **Base URL** (optional): e.g. `https://api.openai.com/v1`
   - **Model**: e.g. `gpt-4o-mini` or a compatible model name

> Note: This is a local MVP prototype. The API key is stored in browser `localStorage` and sent to the local backend for model requests. Do not enter sensitive keys on shared/public machines.

## Demo Accounts

- Teacher: `teacher` / `ArgueTch_6065`
- Student: `student` / `ArgueStu_6065`

## Project Structure

```text
.
├── main.py                 # PyCharm entrypoint (Uvicorn, port 8004)
├── requirements.txt
├── .env.example
└── app/
    ├── main.py             # FastAPI app, routes /, /app, /api/*, /static
    ├── routers/
    │   ├── auth.py         # login/register/logout/me
    │   ├── classroom.py    # assignments and saved sessions
    │   └── debate.py       # /api/debate, /api/health
    ├── services/
    │   ├── auth.py
    │   ├── db.py           # SQLite schema, demo users, sessions
    │   ├── llm.py          # OpenAI-compatible client
    │   └── debate.py       # Toulmin/Socratic prompts and parsing
    ├── data/
    │   └── app.db          # local SQLite database
    └── static/
        ├── home.html       # sign-in / register
        └── index.html      # student & teacher UI
```

## INT7115 Alignment (Design Notes)

- **CILO1**: Demonstrates AI roles in education (tutoring/debate partner), learning impact, and ethical boundaries.
- **CILO2**: Involves LLM use, prompt design, structured outputs, and extensible feedback analysis.
- **CILO3**: Can serve as an original educational AI prototype for conceptualization, design, and evaluation.
- **CILO4**: Supports discussion of Socratic AI value, cognitive conflict, over-reliance, hallucination, bias, privacy, and evaluation evidence.

## Possible Extensions

- Persist full session/revision history for formative evaluation.
- Add teacher analytics for common argument weaknesses and revision trajectories.
- Add multi-agent debate roles (pro/con/judge) or classroom collaboration.
- Add rubric-based argument quality assessment (Toulmin completeness, evidence relevance).
- Support local models (e.g., Ollama/OpenAI-compatible) for cost/privacy.
- Add citation checks, fact-check prompts, AI-use disclosure, and reflection logs.

## Generative AI Declaration (Course Submission)

If you submit this prototype/code/documentation for INT7115 assessment, clearly state how generative AI was used (e.g., UI drafts, code scaffolding, prompt design, text editing), and keep your own critical revisions, design decisions, and evaluation evidence.
