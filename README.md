# ask-my-sales

Proyecto de prueba técnica: pipeline de datos de pedidos con API de lenguaje natural.

> **Entrega**: Repositorio público en GitHub con historial de commits por tarea (SDD).

---

## Requisitos

- Python 3.12+
- Variables de entorno en `.env` (ver `.env.example`)

---

## Instalación

```bash
# Clonar repositorio
git clone <url-del-repo>
cd ask-my-sales

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Instalar dependencias (desarrollo: tests, lint, etc.)
pip install -r requirements-dev.txt
# Solo producción (sin tests/lint):
# pip install -r requirements.txt
```
> **Nota**: `requirements-dev.txt` ya incluye `requirements.txt` (usa `-r requirements.txt` internamente). Para desarrollo usa `requirements-dev.txt`.
```

---

## Uso paso a paso

### 1. Generar CSV sucio (1050 filas, seed 42)
```bash
python -m app.generate_data
```
Genera `data/raw/orders_dirty.csv` con:
- 1000 pedidos base + 50 duplicados exactos
- 40 fechas en formatos alternativos (`DD/MM/YYYY`, `DD-MM-YYYY`, `D mmm YYYY`)
- 15 fechas inválidas irrecuperables
- 30 importes vacíos

### 2. Limpiar y cargar a SQLite + vistas
```bash
python -m app.clean_load
```
Salida esperada:
```
rows_in=1050, loaded=955, duplicates_removed=50, rejected_invalid_date=15, rejected_empty_amount=30, dates_normalized=40
```
Crea:
- `data/orders.db` con tabla `orders`
- `data/rejected.csv` (filas rechazadas con motivo)
- Vistas SQL: `sales_by_month_country`, `top_customers`

### 3. Levantar API
```bash
uvicorn app.main:app --reload --port 8000
```
API disponible en: `http://localhost:8000`

### 4. Probar endpoint `/ask`
```bash
# Health check
curl http://localhost:8000/health
# {"status":"ok"}

# Preguntas de ejemplo
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "cuanto vendimos en Espana en marzo"}'

curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "cuales son los 3 paises con mas ventas"}'

curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "cuantos pedidos cancelados hubo en Chile"}'

curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "cual fue el ticket medio por producto"}'

# Debe fallar con 422 INVALID_SQL
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "borra todos los pedidos de Mexico"}'
```

### 4.1. Salida esperada de las peticiones

**1. Ventas en España en marzo:**
```json
{
  "question": "cuanto vendimos en Espana en marzo",
  "sql": "SELECT total_sales FROM sales_by_month_country WHERE country = 'España' AND month = '2025-03' LIMIT 1000",
  "columns": ["total_sales"],
  "rows": [[1320.06]],
  "row_count": 1
}
```

**2. Top 3 países con más ventas:**
```json
{
  "question": "cuales son los 3 paises con mas ventas",
  "sql": "SELECT country, SUM(total_sales) AS total_sales FROM sales_by_month_country GROUP BY country ORDER BY total_sales DESC LIMIT 3",
  "columns": ["country", "total_sales"],
  "rows": [["Ecuador", 23858.95], ["Argentina", 23045.67], ["Chile", 21573.51]],
  "row_count": 3
}
```

**3. Pedidos cancelados en Chile:**
```json
{
  "question": "cuantos pedidos cancelados hubo en Chile",
  "sql": "SELECT COUNT(*) FROM orders WHERE country = 'Chile' AND status = 'cancelado' LIMIT 1000",
  "columns": ["COUNT(*)"],
  "rows": [[18]],
  "row_count": 1
}
```

**4. Ticket medio por producto:**
```json
{
  "question": "cual fue el ticket medio por producto",
  "sql": "SELECT product, AVG(amount) AS ticket_medio FROM orders WHERE status = 'completado' AND order_date BETWEEN '2025-01-01' AND '2025-12-31' GROUP BY product LIMIT 1000",
  "columns": ["product", "ticket_medio"],
  "rows": [
    ["Altavoz", 279.17],
    ["Auriculares", 239.66],
    ["Cable USB-C", 239.63],
    ["Disco SSD", 269.87],
    ["Mochila", 268.24],
    ["Monitor", 237.00],
    ["Portátil", 236.85],
    ["Ratón", 267.67],
    ["Teclado", 239.12],
    ["Webcam", 289.87]
  ],
  "row_count": 10
}
```

**5. Intento de borrar pedidos (bloqueado):**
```json
{
  "detail": {
    "error": {
      "code": "INVALID_SQL",
      "message": "Only SELECT statements are allowed, got Delete"
    }
  }
}
```
```

**Código de respuesta HTTP:**
- `200 OK`: Consultas válidas
- `422 INVALID_SQL`: SQL no válido o peligroso
- `502 LLM_UNAVAILABLE`: Error del LLM (timeout, red, auth)
- `503 LLM_NOT_CONFIGURED`: Falta NVIDIA_API_KEY o NVIDIA_MODEL

### 5. Swagger UI (interactivo)
Abre en navegador: **http://localhost:8000/docs**

### 6. Tests
```bash
pytest -q
```
Salida esperada: `101 passed`

---

## Decisiones tomadas

Resumen de `docs/decisions.md`:

| ID | Decisión | Motivo |
|----|----------|--------|
| D1 | SQLite como BD | Cero instalación para evaluador |
| D2 | `csv` + `datetime` stdlib | Control explícito de formatos, sin pandas |
| D3 | Fechas numéricas = `DD/MM/YYYY` | Convención española, evita ambigüedad |
| D4 | Rechazar importes vacíos/fechas irrecuperables a `rejected.csv` | Auditable, no inventa datos |
| D5 | Solo `completado` = venta | Pedidos pendientes/cancelados no son ingreso |
| D6 | Esquema en inglés, valores en español | Código estándar; preguntas en español |
| D7 | `sqlglot` para validar SQL por AST | Robusto ante comentarios, mayúsculas, subconsultas |
| D8 | Dos barreras: validador + conexión read-only | Defensa en profundidad |
| D9 | SDK `openai` contra NVIDIA, sin LangChain | API compatible; fácil de testear con mock |
| D10 | Endpoint síncrono (`def`) | SDK y `sqlite3` síncronos; FastAPI usa thread pool |
| D11 | Modelo NVIDIA: `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` | Rápido, compatible OpenAI, timeout 30s |
| D12 | 502 cuando LLM falla | Comportamiento correcto ante API externa no disponible |
| D13 | Modelo en .env: `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` | Probado en T10 |

Ver `docs/decisions.md` para lista completa.

---

## Qué haría con más tiempo

- **Autenticación y rate limiting** en `/ask` para producción
- **Caché de consultas frecuentes** (Redis) para reducir llamadas al LLM
- **Métricas y logging estructurado** (Prometheus/Grafana) para observabilidad
- **Tests de contrato** con `schemathesis` para validar OpenAPI schema
- **Dockerfile** y docker-compose para despliegue reproducible
- **Paginación y streaming** de respuestas grandes
- **Validación semántica** del SQL generado (ej. detectar `WHERE 1=0`)
- **Caché de esquema** para evitar consultar BD en cada request

---

## Cómo usé la IA

Resumen de `docs/ai-log.md`:

| Tarea | Herramienta | Qué pedí | Qué acepté | Qué corregí/rechacé |
|-------|-------------|----------|------------|---------------------|
| Planificación | Claude (chat) | Metodología SDD, estructura `docs/` | Ciclo tarea→commit, criterios en spec | (ninguno) |
| T1-T4 | opencode | Generar CSV, limpieza, carga SQLite, vistas | Código completo, tests pasando | Ajusté formato fechas en generador para pasar R1-AC3 exacto |
| T5 | opencode | Tests de vistas SQL | Tests `test_views.py` | Ninguno, pasaron a la primera |
| T6 | opencode | Validador SQL con sqlglot | `validator.py` + 56 tests | Añadí `exp.TsOrDsToTimestamp` tras descubrir nodo interno de sqlglot para `STRFTIME` |
| T7 | opencode | Cliente LLM NVIDIA + prompt | `llm.py` completo | Eliminé import `Depends` innecesario, usé `httpx.Client` para evitar error `proxies` en openai SDK |
| T8 | opencode | Endpoint `/ask` + `/health` | `main.py` con mapeo 503/502/422/400 | `get_llm_client` recibe `Settings` para evitar `get_settings()` en constructor |
| T9 | opencode | Tests API con LLM simulado | `test_api.py` 7 tests (200/502/422/503) | `monkeypatch` en `app.main.get_llm_client` y `app.config.get_settings` |
| T10 | opencode | Verificación extremo a extremo | 5 preguntas reales contra API | LLM respondió 502 (timeout red/API). Validación y errores funcionan correctamente. Pregunta peligrosa rechazada con 422. |

---

## Tiempo total real invertido

Ver `docs/time-log.md` (rellenado manualmente).

---

## Variables de entorno (`.env.example`)

```bash
NVIDIA_API_KEY=
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=nvidia/nemotron-3-nano-omni-30b-a3b-reasoning
DB_PATH=data/orders.db
```

> **Importante**: `NVIDIA_API_KEY` y `NVIDIA_MODEL` son obligatorios. Nunca subir `.env` al repo (está en `.gitignore`).

---

## Tests

```bash
pytest -q          # 101 tests pasan
ruff check .       # lint limpio
```

Archivos de test:
- `tests/test_cleaning.py` - 15 tests (parseo fechas, importes, duplicados, CSV real)
- `tests/test_validator.py` - 56 tests (SELECT válidos, DROP/UPDATE/INSERT/DELETE, comentarios, PRAGMA, funciones, tablas no permitidas)
- `tests/test_views.py` - 7 tests (vistas SQL, totales, orden, límites)
- `tests/test_llm.py` - 16 tests (post-procesado: fences, bloques think, whitespace)
- `tests/test_api.py` - 7 tests (endpoint `/ask`: 200, 502, 422, 503, validación entrada)

---

## Estructura del proyecto

```
.
├── .env.example
├── .gitignore
├── requirements.txt / requirements-dev.txt
├── pytest.ini
├── pyproject.toml (ruff config)
├── app/
│   ├── config.py           # Settings desde .env
│   ├── generate_data.py    # CSV sucio con seed 42
│   ├── cleaning.py         # Funciones puras de limpieza
│   ├── clean_load.py       # CLI: CSV → SQLite + vistas
│   ├── db.py               # Conexiones RW/RO (PRAGMA query_only=ON)
│   ├── validator.py        # Validador SQL (sqlglot AST)
│   ├── llm.py              # Cliente NVIDIA + prompt + post-procesado
│   └── main.py             # FastAPI app, endpoint /ask
├── sql/views.sql           # Vistas: sales_by_month_country, top_customers
├── data/raw/orders_dirty.csv (committed)
├── tests/
│   ├── test_cleaning.py
│   ├── test_validator.py
│   ├── test_views.py
│   ├── test_llm.py
│   └── test_api.py
└── docs/                   # SDD documentation
```

---

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

---

## Seguridad

- **Sin claves en repo**: `.env` en `.gitignore`, solo `.env.example` sin valores
- **Sin secretos en historial**: `git log -p | grep -i "nvapi-"` → vacío
- **SQL inyectado imposible**: Validador AST + conexión read-only (`PRAGMA query_only=ON`)
- **LLM no confiable**: Validación antes de ejecución Y ejecución en read-only

---

## Licencia

Prueba técnica - Uso educativo/evaluación.