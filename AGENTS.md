
# AGENTS.md
 
This file documents project-specific conventions for OpenCode agents.
 
## Project Overview
`ask-my-sales` is a Python technical test. Pipeline: dirty orders CSV -> cleaning script -> SQLite -> two SQL views -> FastAPI endpoint that turns a natural-language question into SQL using an LLM (NVIDIA API, OpenAI-compatible), validates the SQL (read-only, allowed tables only) and returns the result.
 
Stack: Python 3.12, FastAPI, stdlib `sqlite3` and `csv`, `sqlglot`, `openai` SDK, `pytest`, `ruff`.
 
Methodology: **Spec-Driven Development (SDD)**. `docs/` is the single source of truth. Code never gets ahead of the spec. If something is not in `docs/`, do NOT invent it: write the question in `docs/open-questions.md` and ask the human.
 
## Workflow (mandatory, every session)
Read in this order before touching code:
1. `docs/00-brief.md` - original requirements (the email), verbatim
2. `docs/01-constitution.md` - non-negotiable rules
3. `docs/02-spec.md` - WHAT to build, with acceptance criteria (R1..R6)
4. `docs/03-plan.md` - HOW to build it (architecture, modules, error mapping)
5. `docs/04-tasks.md` - ordered tasks; pick the first unchecked one
Then, for ONE task only:
1. Re-read the acceptance criteria it references in `02-spec.md`.
2. Write the test first when the task says so, then the implementation.
3. Run `pytest -q` and `ruff check .`. Do not mark the task done while anything fails.
4. Tick the task in `docs/04-tasks.md`; append real entries to `docs/ai-log.md` and `docs/time-log.md`; record any decision in `docs/decisions.md`.
5. Make exactly ONE commit per task using the full message (subject, body, Refs) from "Mensajes de commit completos" in `docs/04-tasks.md`. If what you actually did differs from the body, correct the body so it is truthful; never describe work you did not do.
6. Stop and report. Start another task only if the human's prompt explicitly names it (the human may name several consecutive tasks, e.g. "T5 and T6"; still one commit per task). Stop at once, even mid-task, on any open question, failing check, or when a task takes more than twice its estimate.
## Commands
- **Install**: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements-dev.txt`
- **Generate data**: `python -m app.generate_data`
- **Clean and load**: `python -m app.clean_load`
- **Run API**: `uvicorn app.main:app --reload`
- **Build**: not applicable
- **Test**: `pytest -q`
- **Lint**: `ruff check .`
- **Typecheck**: not used (type hints required, no checker configured)
- **Format**: `ruff format .`
## Project Structure
```
.
├── AGENTS.md
├── README.md
├── requirements.txt / requirements-dev.txt
├── .env.example                # no real values
├── pytest.ini
├── app/
│   ├── config.py               # env vars
│   ├── generate_data.py        # seeded dirty CSV generator
│   ├── cleaning.py             # pure cleaning functions
│   ├── clean_load.py           # CLI: raw CSV -> SQLite + views
│   ├── db.py                   # connections (read-write / read-only)
│   ├── validator.py            # SQL validation
│   ├── llm.py                  # LLM client + prompt
│   └── main.py                 # FastAPI app
├── sql/views.sql
├── data/raw/orders_dirty.csv   # committed; orders.db and rejected.csv are ignored
├── tests/
└── docs/                       # SDD documentation
```
 
## Conventions
- Code, comments and commit messages in English. Docs and README in Spanish.
- Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`, `chore:`), imperative, max 72 chars.
- Type hints on all functions. Small pure functions; standard library before new dependencies.
- Only dependencies listed in `docs/03-plan.md`. A new one needs an entry in `docs/decisions.md` first.
- Scope is exactly `docs/02-spec.md`. No auth, Docker, frontend, ORM or extra endpoints.
## Testing
- Tests never call the real LLM and never use the network. The endpoint test overrides the LLM dependency with a fake.
- Tests that need a database build a temporary SQLite file (`tmp_path`); never use `data/orders.db`.
- Required test files: `tests/test_cleaning.py`, `tests/test_validator.py`, `tests/test_api.py`.
## Gotchas
- Secrets: `NVIDIA_API_KEY` comes only from the environment (`.env` is git-ignored). Never read, print or commit `.env`. Never put a key in code, docs, tests or logs.
- LLM output is untrusted input. It is validated before execution AND executed on a read-only connection.
- Dates are ambiguous: numeric dates are always `DD/MM/YYYY` (Spanish convention). Do not use `dateutil` guessing.
- `sqlglot` must be used with `dialect="sqlite"`.
- Cleaning must be deterministic and idempotent (running it twice gives the same DB).
- `data/raw/orders_dirty.csv` is generated with a fixed seed; do not hand-edit it.
## References
- `docs/00-brief.md`, `docs/01-constitution.md`, `docs/02-spec.md`, `docs/03-plan.md`, `docs/04-tasks.md`
- `docs/decisions.md`, `docs/ai-log.md`, `docs/time-log.md`, `docs/open-questions.md`
 
