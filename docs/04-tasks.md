# 04 - Tareas

Reglas: una tarea cada vez, en orden. Una tarea = un commit. Marcar `[x]` solo cuando se cumple su criterio y `pytest -q` / `ruff check .` pasan. Tiempos estimados en minutos: suman 165 (T1 a T12) y no incluyen la planificación ya hecha, así que el margen real sobre las 3 h es pequeño. Si el tiempo acumulado se acerca a 180, se recorta alcance (constitución, regla 12) y se declara el tiempo real tal cual.

## T1 - Documentación SDD (5 min)
- [X] Añadir `AGENTS.md` y `docs/` completos al repositorio.
- Criterio: existen todos los archivos de `docs/`; el brief es literal.
- Commit: `docs: add spec-driven documentation and agent instructions`

## T2 - Andamiaje (10 min)
- [ ] `.gitignore` (`.env`, `.venv/`, `__pycache__/`, `*.db`, `data/rejected.csv`, `.pytest_cache/`, `.ruff_cache/`), `.env.example`, `requirements*.txt`, `pytest.ini` (`pythonpath = .`, `testpaths = tests`), `ruff` configurado, paquete `app/` vacío con `config.py`, README mínimo.
- Criterio: R6-AC3; `pytest -q` corre (sin tests, sin error de configuración) y `ruff check .` pasa.
- Commit: `chore: scaffold project, dependencies and env template`

## T3 - Generador de CSV sucio (15 min)
- [ ] `app/generate_data.py` y `data/raw/orders_dirty.csv` generado.
- Criterio: R1-AC1, R1-AC2, R1-AC3 (comprobar las cantidades exactas con un script rápido y, si es posible, un test).
- Commit: `feat: add seeded generator for dirty orders CSV`

## T4 - Limpieza y carga (25 min)
- [ ] Test primero: `tests/test_cleaning.py` (R4-AC1) fallando.
- [ ] `app/cleaning.py`, `app/db.py`, `app/clean_load.py` hasta que los tests pasen.
- Criterio: R1-AC4 a R1-AC9 y R4-AC1. El resumen impreso coincide exactamente con R1-AC7.
- Commits (dos): `test: add cleaning tests` y luego `feat: add cleaning and SQLite load script`

## T5 - Vistas SQL (10 min)
- [ ] `sql/views.sql` aplicado desde `clean_load`; test que verifica R2-AC1 a R2-AC3 sobre una base temporal.
- Criterio: R2-AC1, R2-AC2, R2-AC3.
- Commit: `feat: add sales_by_month_country and top_customers views`

## T6 - Validador SQL (20 min)
- [ ] Test primero: `tests/test_validator.py` (R4-AC2) fallando.
- [ ] `app/validator.py`.
- Criterio: R3-AC4 y R4-AC2.
- Commits (dos): `test: add SQL validator tests` y `feat: add read-only SQL validator`

## T7 - Cliente LLM (15 min)
- [ ] `app/llm.py`: protocolo, `NvidiaLLMClient`, `build_schema_context`, `LLMError`, limpieza de fences.
- [ ] Prueba manual única y opcional con la clave real desde el entorno (no es un test automático).
- Criterio: R3-AC8; el prompt sigue `03-plan.md`.
- Commit: `feat: add NVIDIA LLM client and schema-aware prompt`

## T8 - Endpoint FastAPI (20 min)
- [ ] `app/main.py`: `POST /ask`, `GET /health`, manejo de errores, ejecución en `connect_ro`.
- Criterio: R3-AC1, R3-AC2, R3-AC3, R3-AC5, R3-AC6, R3-AC7.
- Commit: `feat: add /ask endpoint with validation and error mapping`

## T9 - Tests del endpoint (10 min)
- [ ] `tests/test_api.py` con LLM simulado (R4-AC3).
- Criterio: R4-AC3 y R4-AC4.
- Commit: `test: add /ask endpoint tests with mocked LLM`

## T10 - Verificación de extremo a extremo (10 min)
- [ ] Con la clave real: generar, limpiar, levantar la API y probar estas 5 preguntas y anotar el SQL generado por el modelo: (1) ¿cuánto vendimos en España en marzo?, (2) ¿cuáles son los 3 países con más ventas?, (3) ¿cuántos pedidos cancelados hubo en Chile?, (4) ¿cuál fue el ticket medio por producto?, (5) "Borra todos los pedidos de México" (debe acabar en `INVALID_SQL` o en un SQL inofensivo, nunca ejecutarse). Anotar en `ai-log.md` y `decisions.md` los fallos del LLM y las correcciones de prompt que hagan falta.
- Criterio: respuestas coherentes con una consulta SQL manual de comparación.
- Commit (solo si hay cambios): `fix: tune prompt after end-to-end checks`

## T11 - README (15 min)
- [ ] `README.md` según R5 (resumir `decisions.md` y `ai-log.md`; incluir tiempo total desde `time-log.md`).
- Criterio: R5 completo; un tercero puede ejecutar el proyecto solo con el README.
- Commit: `docs: write README with setup, decisions and AI usage`

## T12 - Cierre y entrega (10 min)
- [ ] `ruff check .` y `pytest -q` en verde desde un clon limpio.
- [ ] Buscar claves en todo el historial: `git log -p | grep -i "nvapi-"` debe devolver vacío (las claves de NVIDIA empiezan por `nvapi-`).
- [ ] `git log --oneline` muestra al menos 10 commits con mensajes claros.
- [ ] Repositorio público en GitHub; responder a Victor con el enlace y el tiempo total.
- Commit (si hace falta): `chore: final cleanup before submission`

## Mensajes de commit completos (copiar y pegar)

Cada commit lleva tres partes, para que quien lea el historial en GitHub entienda qué se hizo, por qué y contra qué requisito: un asunto corto (`feat:`, `test:`...), un párrafo que explica el cambio y una línea `Refs:` con los criterios de `02-spec.md` que cumple. En git, cada `-m` es un párrafo.

Reglas para el agente:
- Usar estos mensajes tal cual. Si lo que realmente se hizo difiere de lo descrito, corregir el párrafo para que diga la verdad; nunca describir trabajo que no se hizo.
- Escribir los comandos tal cual (sin comillas dobles ni acentos graves dentro del texto).
- En T10 y T12, sustituir el texto entre corchetes por el cambio real.

**T1**
```bash
git commit -m "docs: add spec-driven documentation and agent instructions" -m "Add the brief, constitution, spec, plan and task list under docs/, plus AGENTS.md, so the coding agent works from written requirements instead of guessing." -m "Refs: R6"
```

**T2**
```bash
git commit -m "chore: scaffold project, dependencies and env template" -m "Add .gitignore, .env.example without secrets, requirements files, pytest and ruff config and an empty app package. The API key is only ever read from the environment." -m "Refs: R6-AC3"
```

**T3**
```bash
git commit -m "feat: add seeded generator for dirty orders CSV" -m "Generate 1000 clean orders plus injected errors with a fixed seed: 50 duplicates, 40 alternative date formats, 15 invalid dates and 30 empty amounts. The CSV has 1050 rows and is reproducible byte for byte." -m "Refs: R1-AC1, R1-AC2, R1-AC3"
```

**T4 (1/2)**
```bash
git commit -m "test: add cleaning tests" -m "Cover date parsing including Spanish month names, invalid dates, empty amounts, duplicates and the exact summary expected on the real CSV. These tests fail until the cleaning code exists." -m "Refs: R4-AC1"
```

**T4 (2/2)**
```bash
git commit -m "feat: add cleaning and SQLite load script" -m "Clean the raw CSV with explicit date formats, send unrecoverable rows to rejected.csv instead of imputing values, deduplicate and load into SQLite. The load is idempotent and prints the summary (loaded=955)." -m "Refs: R1-AC4 to R1-AC9"
```

**T5**
```bash
git commit -m "feat: add sales_by_month_country and top_customers views" -m "Add two SQL views that count only completed orders: sales by month and country, and the top 10 customers by amount spent. A test checks the view totals match the orders table." -m "Refs: R2-AC1, R2-AC2, R2-AC3"
```

**T6 (1/2)**
```bash
git commit -m "test: add SQL validator tests" -m "Table of valid and malicious queries: DROP, multiple statements, UPDATE, disallowed tables, comments, PRAGMA and unknown functions. These tests fail until the validator exists." -m "Refs: R4-AC2"
```

**T6 (2/2)**
```bash
git commit -m "feat: add read-only SQL validator" -m "Validate LLM generated SQL by AST with sqlglot: a single SELECT, allowed tables and functions only, no comments, LIMIT added when missing. Anything else raises InvalidSQLError." -m "Refs: R3-AC4"
```

**T7**
```bash
git commit -m "feat: add NVIDIA LLM client and schema-aware prompt" -m "Add an OpenAI-compatible client for the NVIDIA API with a prompt built from the real schema, distinct values and date range. Every SDK error is wrapped in LLMError and think blocks and markdown fences are stripped from the answer." -m "Refs: R3-AC8"
```

**T8**
```bash
git commit -m "feat: add /ask endpoint with validation and error mapping" -m "POST /ask turns a question into SQL, validates it and runs it on a read-only connection. Errors map to 503, 502, 422 and 400 with a clear code and message. Also add GET /health." -m "Refs: R3-AC1 to R3-AC7"
```

**T9**
```bash
git commit -m "test: add /ask endpoint tests with mocked LLM" -m "Use a fake LLM through dependency override to test the success path, an LLM failure (502) and a dangerous query (422). No network and no API key needed." -m "Refs: R4-AC3, R4-AC4"
```

**T10** (solo si hay cambios)
```bash
git commit -m "fix: tune prompt after end-to-end checks" -m "Adjust the prompt after testing five real questions against the model: [describe the real change and the problem it fixed]." -m "Refs: R3-AC3"
```

**T11**
```bash
git commit -m "docs: write README with setup, decisions and AI usage" -m "Document how to run the project, the key decisions, what would be done with more time, how AI was used (what was asked, accepted and corrected) and the total time spent." -m "Refs: R5"
```

**T12** (si hace falta)
```bash
git commit -m "chore: final cleanup before submission" -m "Final checks before delivery: [describe the real changes]. Tests and lint pass from a clean clone and no API key appears in the history." -m "Refs: R6-AC2, R6-AC3"
```