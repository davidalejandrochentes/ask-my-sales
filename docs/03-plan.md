# 03 - Plan técnico (CÓMO)

## Stack

| Pieza | Elección | Motivo (detalle en decisions.md) |
|---|---|---|
| Python | 3.12 | |
| Base de datos | SQLite (`sqlite3` de la biblioteca estándar) | Cero instalación para quien evalúa |
| CSV y fechas | `csv` + `datetime` estándar | Control explícito de formatos; sin pandas |
| API | `fastapi`, `uvicorn` | Obligatorio |
| LLM | SDK `openai` apuntando a NVIDIA (`https://integrate.api.nvidia.com/v1`) | API compatible con OpenAI; sin LangChain |
| Validación SQL | `sqlglot` (dialecto `sqlite`) | Análisis por AST, no regex |
| Config | `python-dotenv` | Carga `.env` local |
| Tests | `pytest`, `httpx` (requerido por `TestClient`) | |
| Lint/format | `ruff` | |

`requirements.txt`: fastapi, uvicorn, openai, sqlglot, python-dotenv.
`requirements-dev.txt`: `-r requirements.txt`, pytest, httpx, ruff.
Fijar versiones exactas tras instalar (`pip freeze` de esas librerías). Esta lista es exhaustiva: cualquier otra librería requiere una entrada previa en `decisions.md`.

## Variables de entorno (`.env.example`)

```
NVIDIA_API_KEY=
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=
DB_PATH=data/orders.db
```

`NVIDIA_MODEL` sin valor por defecto en el código. Modelo elegido (D11): `deepseek-ai/deepseek-v4-flash`; el humano confirma el identificador exacto en el snippet "View Code" de build.nvidia.com y lo pone en su `.env`. Si falta, `LLM_NOT_CONFIGURED`.

## Módulos y responsabilidades

- `app/config.py`: lee variables de entorno (`get_settings()`). Nada de lógica.
- `app/generate_data.py`: `generate_rows(seed=42) -> list[dict]`, `write_csv(rows, path)`, `main()`. Genera 1.000 pedidos base correctos, luego inyecta los errores de R1-AC3 sobre filas distintas elegidas con el mismo generador aleatorio con semilla.
- `app/cleaning.py` (funciones puras, sin I/O de base de datos):
  - `parse_date(raw: str) -> str | None` (devuelve ISO o `None`)
  - `parse_amount(raw: str) -> float | None`
  - `clean_rows(raw_rows: Iterable[dict]) -> CleanResult` con `valid`, `rejected` (con `reason`) y contadores (`duplicates_removed`, `dates_normalized`, ...)
- `app/clean_load.py`: `main()`: lee CSV, llama a `clean_rows`, recrea `orders`, inserta, aplica `sql/views.sql`, escribe `data/rejected.csv`, imprime el resumen de R1-AC7.
- `app/db.py`: `connect_rw(path)`, `connect_ro(path)` (URI `file:...?mode=ro`, `PRAGMA query_only=ON`), `run_query(conn, sql) -> (columns, rows)`.
- `app/validator.py`: `validate_sql(sql: str) -> str` devuelve el SQL normalizado con `LIMIT`; lanza `InvalidSQLError(message)`.
- `app/llm.py`: `class LLMClient(Protocol)` con `generate_sql(question: str, schema_context: str) -> str`; implementación `NvidiaLLMClient`; `build_schema_context(conn) -> str`; `LLMError`.
- `app/main.py`: app FastAPI, dependencias `get_llm_client` y `get_db_path`, manejo de errores.
- `sql/views.sql`: `DROP VIEW IF EXISTS` + `CREATE VIEW` para las dos vistas.

## Algoritmo de limpieza

Por cada fila cruda: recortar espacios -> `parse_date` (si `None`, rechazar `invalid_date`) -> `parse_amount` (si `None`, rechazar `empty_amount`) -> añadir a válidas. Después, deduplicar válidas por la clave de R1-AC5 conservando la primera. `dates_normalized` cuenta las filas aceptadas (antes de deduplicar) cuya fecha cruda no era ya `YYYY-MM-DD`.

`parse_date` acepta únicamente: `YYYY-MM-DD`, `DD/MM/YYYY`, `DD-MM-YYYY`, `D mmm YYYY` (mes abreviado español, sin distinguir mayúsculas). Valida que la fecha exista en el calendario (31/02 es inválida). Sin `dateutil`.

## Validador SQL (algoritmo)

1. Rechazar si el texto contiene `--` o `/*`.
2. `sqlglot.parse(sql, dialect="sqlite")`. Error de parseo -> `InvalidSQLError`. Debe devolver exactamente 1 sentencia (ignorar vacías tras `;` final).
3. La raíz debe ser `exp.Select`. Cualquier nodo `exp.Insert/Update/Delete/Drop/Create/Alter/Command/Pragma/Attach/Union` en el árbol -> rechazar.
4. Para cada `exp.Table`: su nombre en minúsculas debe estar en `{orders, sales_by_month_country, top_customers}` o ser un alias de CTE declarado en la misma consulta.
5. Funciones: se permite una lista cerrada (`SUM, COUNT, AVG, MIN, MAX, ROUND, STRFTIME, SUBSTR, LOWER, UPPER, COALESCE, DATE, ABS`). Toda función desconocida (nodo `exp.Anonymous`) o no listada -> rechazar. El agente debe comprobar con un test cómo parsea sqlglot cada función de la lista antes de darla por buena.
6. Si no hay `LIMIT`, añadir `LIMIT 1000`. Devolver `.sql(dialect="sqlite")`.

## LLM: prompt

Mensaje de sistema (temperatura 0, `max_tokens` acotado, timeout 30 s):

- Rol: traductor de preguntas a SQL de SQLite.
- Devolver **solo** una sentencia SELECT, sin explicaciones ni bloques markdown.
- Solo tablas/vistas permitidas, con su DDL y descripción de cada vista.
- Contexto generado desde la base de datos: valores distintos de `country` y `status`, y rango `MIN/MAX(order_date)`.
- Reglas de negocio: "vendimos/ventas" = `status = 'completado'`; si la pregunta no indica año, usar el año del rango de datos; los meses se filtran con `strftime('%m', order_date)` o comparando `YYYY-MM`.
- Si no se puede responder con esas tablas, devolver una respuesta que no sea SQL (el validador la rechazará con `INVALID_SQL`).

Posprocesado en `llm.py`: usar solo el campo `content` de la respuesta (nunca campos de razonamiento), quitar cualquier bloque `<think>...</think>` con su contenido, quitar fences ```` ```sql ```` si existen y recortar espacios, en ese orden. `max_tokens=512`. Respuesta vacía tras el posprocesado -> `LLMError`. Cualquier excepción del SDK (`APIError`, timeout, conexión, auth) -> `LLMError` con mensaje genérico, sin filtrar la clave ni detalles internos.

## Mapeo de errores (main.py)

`LLMError` -> 502 `LLM_UNAVAILABLE`; settings sin clave/modelo -> 503 `LLM_NOT_CONFIGURED`; `InvalidSQLError` -> 422 `INVALID_SQL` (el mensaje incluye el motivo; el SQL rechazado se puede incluir para depurar); `sqlite3.Error` al ejecutar -> 400 `SQL_EXECUTION_ERROR`. Los handlers devuelven siempre `{"error": {"code", "message"}}`.

Orden de comprobación en `POST /ask`: configuración (503) -> llamada al LLM (502) -> validación (422) -> ejecución (400). Si fallan dos cosas a la vez, gana la primera de esta lista. `NvidiaLLMClient` envuelve toda excepción del SDK en `LLMError`; el test del endpoint simula el fallo haciendo que el fake lance `LLMError` directamente.

El endpoint es una función `def` síncrona (FastAPI la ejecuta en un hilo): el SDK `openai` y `sqlite3` usados son síncronos.

## Estrategia de tests

- `test_cleaning.py`: pruebas unitarias de `parse_date`/`parse_amount`/`clean_rows` con filas pequeñas, más una prueba que corre `clean_rows` sobre el CSV real y verifica R1-AC7.
- `test_validator.py`: tabla de casos válidos/ inválidos con `pytest.mark.parametrize`.
- `test_llm.py` (opcional, pequeño): función pura de posprocesado con textos de ejemplo (fences, bloque `<think>`, texto con espacios, vacío).
- `test_api.py`: base SQLite temporal creada en un fixture con unas pocas filas y las vistas; `FakeLLM` con `generate_sql` configurable; `app.dependency_overrides` para inyectar el fake y la ruta de la base; `TestClient`.