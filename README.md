# ask-my-sales

Proyecto de prueba técnica: pipeline de datos de pedidos con API de lenguaje natural.

## Requisitos

- Python 3.12
- Variables de entorno en `.env` (ver `.env.example`)

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Uso

```bash
# Generar CSV sucio
python -m app.generate_data

# Limpiar y cargar a SQLite
python -m app.clean_load

# Levantar API
uvicorn app.main:app --reload

# Probar endpoint
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"question": "cuanto vendimos en Espana en marzo"}'

# Tests
pytest -q
```

## Arquitectura

```
data/raw/orders_dirty.csv (1050 filas, seed 42)
    ↓ app.clean_load (limpieza, deduplicación, rechazo a rejected.csv)
data/orders.db (tabla orders + vistas sales_by_month_country, top_customers)
    ↓ POST /ask (pregunta en lenguaje natural)
app.llm (SDK openai → NVIDIA API) → SQL
    ↓ app.validator (sqlglot AST, solo SELECT, tablas permitidas, funciones permitidas, LIMIT)
data/orders.db (conexión read-only, PRAGMA query_only=ON)
    ↓ resultado JSON
```

## Decisiones principales

| ID | Decisión | Motivo |
|---|---|---|
| D1 | SQLite como base de datos | Cero instalación para evaluador |
| D2 | `csv` y `datetime` estándar | Control explícito de formatos, sin pandas |
| D3 | Fechas numéricas = `DD/MM/YYYY` | Convención española, evita ambigüedad |
| D4 | Rechazar importes vacíos/fechas irrecuperables a `rejected.csv` | Auditable, no inventa datos |
| D5 | Solo `completado` = venta | Pedidos cancelados/pendientes no son ingresos |
| D6 | Esquema en inglés, valores en español | Código estándar; preguntas en español |
| D7 | `sqlglot` para validar por AST | Robusto ante comentarios, mayúsculas, subconsultas |
| D8 | Dos barreras: validador + conexión read-only | Defensa en profundidad |
| D9 | SDK `openai` contra NVIDIA, sin LangChain | API compatible; fácil de testear con mock |
| D10 | Endpoint síncrono (`def`) | SDK y `sqlite3` síncronos; FastAPI usa thread pool |
| D11 | Modelo NVIDIA: `deepseek-ai/deepseek-v4-flash` | Rápido, compatible OpenAI, encaja en timeout 30s |
| D12 | 502 cuando LLM falla | Comportamiento correcto ante API externa no disponible |
| D13 | Modelo en .env: `deepseek-ai/deepseek-v4.1-flash` | Probado en T10; ajustar si falla |

## Qué haría con más tiempo

- **Autenticación y rate limiting** en `/ask` para uso en producción
- **Caché de consultas frecuentes** (Redis) para reducir llamadas al LLM
- **Métricas y logging estructurado** (Prometheus/Grafana) para observabilidad
- **Tests de contrato** con `schemathesis` para validar OpenAPI schema
- **Dockerfile** y docker-compose para despliegue reproducible
- **Paginación y streaming** de respuestas grandes
- **Validación semántica** del SQL generado (ej. detectar `WHERE 1=0`)

## Cómo usé la IA

| Tarea | Herramienta | Qué pedí | Qué acepté | Qué corregí/rechacé |
|---|---|---|---|---|
| Planificación | Claude (chat) | Metodología SDD, estructura `docs/` | Ciclo tarea→commit, criterios en spec | (ninguno, base acordada) |
| T1-T4 | opencode | Generar CSV, limpieza, carga, vistas | Código completo, tests pasando | Ajusté formato fechas en generador para pasar R1-AC3 exacto |
| T5 | opencode | Tests de vistas SQL | Tests `test_views.py` | Ninguno, pasaron a la primera |
| T6 | opencode | Validador SQL + tests | `validator.py` + 56 tests | Añadí `exp.TsOrDsToTimestamp` tras descubrir nodo interno de sqlglot |
| T7 | opencode | Cliente LLM NVIDIA + prompt | `llm.py` completo | Eliminé import `Depends` innecesario, usé `httpx.Client` para evitar error `proxies` |
| T8 | opencode | Endpoint `/ask` + `/health` | `main.py` con mapeo 503/502/422/400 | `get_llm_client` recibe `Settings` para evitar `get_settings()` en constructor |
| T9 | opencode | Tests API con LLM simulado | `test_api.py` 7 tests (200/502/422/503) | `monkeypatch` en `app.main.get_llm_client` y `app.config.get_settings` |
| T10 | opencode | Verificación extremo a extremo | 5 preguntas reales contra API | LLM respondió 502 (timeout de red/API). Validación y errores funcionan correctamente. |

## Tiempo total real invertido

Ver `docs/time-log.md` (rellenado manualmente).

## Variables de entorno (`.env.example`)

```bash
NVIDIA_API_KEY=
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=
DB_PATH=data/orders.db
```

## Tests

```bash
pytest -q          # 101 tests pasan
ruff check .       # lint limpio
```

## Estructura del proyecto

```
.
├── .env.example
├── requirements.txt / requirements-dev.txt
├── pytest.ini
├── pyproject.toml (ruff config)
├── app/
│   ├── config.py          # carga .env, settings
│   ├── generate_data.py   # CSV sucio con seed 42
│   ├── cleaning.py        # funciones puras de limpieza
│   ├── clean_load.py      # CLI: CSV → SQLite + vistas
│   ├── db.py              # conexiones read-write / read-only
│   ├── validator.py       # validador SQL (sqlglot AST)
│   ├── llm.py             # cliente NVIDIA + prompt + post-procesado
│   └── main.py            # FastAPI app, endpoint /ask
├── sql/views.sql          # dos vistas SQL
├── data/raw/orders_dirty.csv (committed)
├── tests/
│   ├── test_cleaning.py
│   ├── test_validator.py
│   ├── test_llm.py
│   ├── test_views.py
│   └── test_api.py
└── docs/                  # SDD documentation
```