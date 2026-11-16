# 02 - Especificación (QUÉ)

Cada requisito deriva de `00-brief.md` y tiene criterios de aceptación verificables (AC). Las tareas de `04-tasks.md` referencian estos IDs.

## Datos de dominio

- Tienda ficticia. Rango de fechas de los pedidos: **2025-01-01 a 2025-12-31**.
- Países (8): España, México, Argentina, Colombia, Chile, Perú, Ecuador, Estados Unidos.
- Productos (10), por ejemplo: Teclado, Ratón, Monitor, Portátil, Auriculares, Webcam, Altavoz, Disco SSD, Cable USB-C, Mochila.
- Estados: `completado` (70 %), `pendiente` (15 %), `cancelado` (15 %).
- Clientes: al menos 100 nombres distintos, con repetición (hay clientes que compran varias veces).
- Importe: entre 5.00 y 500.00, dos decimales, punto decimal.
- Esquema en inglés, valores en español. Una **venta** es un pedido con estado `completado`.

## R1 - Carga (CSV sucio, limpieza, base de datos)

- **R1-AC1** Existe `data/raw/orders_dirty.csv`, UTF-8, cabecera exacta `fecha,cliente,pais,producto,importe,estado`, con **1.050 filas** de datos (sin contar la cabecera).
- **R1-AC2** El generador usa semilla fija (42): dos ejecuciones producen un archivo idéntico byte a byte.
- **R1-AC3** Errores inyectados, sobre filas distintas entre sí (nunca dos errores en la misma fila), en estas cantidades exactas:
  - 50 duplicados exactos (copias de filas por lo demás correctas).
  - 40 fechas en formato alternativo válido y recuperable: `DD/MM/YYYY`, `DD-MM-YYYY` o `D mmm YYYY` con mes abreviado en español (`ene, feb, mar, abr, may, jun, jul, ago, sep, oct, nov, dic`), por ejemplo `15 mar 2025`.
  - 15 fechas inválidas e irrecuperables: por ejemplo `2025-13-45`, `31/02/2025`, `ayer`, `2025/3/`.
  - 30 importes vacíos.
  - El resto de las fechas están en `YYYY-MM-DD`.
  - Las 1.000 filas base son únicas entre sí según la clave de duplicado de R1-AC5 (el generador lo garantiza, regenerando una fila si hace falta), para que los únicos duplicados sean los 50 inyectados y `loaded=955` sea exacto.
- **R1-AC4** `python -m app.clean_load` lee el CSV y crea (recreando si existe) la tabla `orders` en SQLite con el esquema:
  `order_id INTEGER PRIMARY KEY AUTOINCREMENT, order_date TEXT NOT NULL (YYYY-MM-DD), customer TEXT NOT NULL, country TEXT NOT NULL, product TEXT NOT NULL, amount REAL NOT NULL, status TEXT NOT NULL`.
- **R1-AC5** Reglas de limpieza:
  1. Se recortan espacios en todos los campos de texto.
  2. Las fechas se normalizan a `YYYY-MM-DD` solo con los formatos de R1-AC3 (los numéricos son siempre día/mes/año). Cualquier otra se rechaza con motivo `invalid_date`.
  3. Importe vacío o no numérico se **rechaza** con motivo `empty_amount`. No se imputa ni se rellena con 0.
  4. Si una fila falla por varios motivos, se registra el primero según el orden: fecha, importe.
  5. Se eliminan duplicados **después** de normalizar y rechazar. Clave de duplicado: `(order_date, customer, country, product, amount, status)`. Se conserva la primera aparición.
- **R1-AC6** Las filas rechazadas se escriben en `data/rejected.csv` con las columnas originales más `reason`. Los duplicados eliminados solo se cuentan.
- **R1-AC7** Al terminar, el script imprime un resumen. Con el CSV de R1-AC1 el resultado esperado es exactamente:
  `rows_in=1050, loaded=955, duplicates_removed=50, rejected_invalid_date=15, rejected_empty_amount=30, dates_normalized=40`.
- **R1-AC8** Es idempotente: ejecutarlo dos veces deja la base con el mismo contenido.
- **R1-AC9** La ruta de la base sale de la variable `DB_PATH` (por defecto `data/orders.db`).

## R2 - Vistas SQL

Definidas en `sql/views.sql` y creadas por `clean_load` tras cargar `orders`.

- **R2-AC1** `sales_by_month_country(month, country, orders, total_sales)`: solo pedidos `completado`; `month` en formato `YYYY-MM`; `total_sales` redondeado a 2 decimales; ordenada por `month`, `country`.
- **R2-AC2** `top_customers(customer, orders, total_spent)`: solo pedidos `completado`; ordenada por `total_spent` descendente y, en empate, `customer` ascendente; exactamente 10 filas.
- **R2-AC3** La suma de `total_sales` de la primera vista coincide con la suma de `amount` de los pedidos `completado` en `orders`.

## R3 - API FastAPI

- **R3-AC1** `POST /ask` con cuerpo `{"question": "<texto, 1 a 500 caracteres>"}`.
- **R3-AC2** Éxito (200): `{"question": str, "sql": str, "columns": [str], "rows": [[...]], "row_count": int}`.
- **R3-AC3** Flujo: construir contexto de esquema -> pedir SQL al LLM -> validar -> ejecutar en solo lectura -> responder. El SQL validado es el que se ejecuta y el que se devuelve.
- **R3-AC4** Validación del SQL (todas obligatorias):
  1. Exactamente una sentencia.
  2. La sentencia raíz es `SELECT` (se admiten CTE `WITH ... SELECT`). Se rechazan `UNION`, `INSERT`, `UPDATE`, `DELETE`, `DROP`, `CREATE`, `ALTER`, `ATTACH`, `PRAGMA` y cualquier otra cosa.
  3. Solo se pueden consultar las tablas/vistas permitidas: `orders`, `sales_by_month_country`, `top_customers` (los alias de CTE se permiten).
  4. Sin comentarios (`--`, `/* */`).
  5. Sin funciones fuera de la lista permitida (se define en `03-plan.md`).
  6. Si no tiene `LIMIT`, se añade `LIMIT 1000`.
- **R3-AC5** Segunda barrera: la consulta se ejecuta en una conexión SQLite abierta en modo solo lectura (`mode=ro`) con `PRAGMA query_only=ON`.
- **R3-AC6** Errores con cuerpo `{"error": {"code": str, "message": str}}`:

  | Situación | HTTP | code |
  |---|---|---|
  | El LLM falla (red, timeout, auth, respuesta vacía) | 502 | `LLM_UNAVAILABLE` |
  | El SQL del LLM no pasa la validación | 422 | `INVALID_SQL` |
  | SQL válido pero falla al ejecutarse | 400 | `SQL_EXECUTION_ERROR` |
  | Falta `NVIDIA_API_KEY` | 503 | `LLM_NOT_CONFIGURED` |
  | Cuerpo de la petición inválido | 422 | (el estándar de FastAPI) |

- **R3-AC7** `GET /health` devuelve `{"status": "ok"}`.
- **R3-AC8** La clave se lee de `NVIDIA_API_KEY`; el modelo de `NVIDIA_MODEL` y la URL base de `NVIDIA_BASE_URL`. Nunca aparece en respuestas, logs ni mensajes de error.

## R4 - Tests (pytest)

- **R4-AC1** `tests/test_cleaning.py`: formatos de fecha (incluido mes en español), fecha inválida rechazada, importe vacío rechazado, duplicados eliminados y el resumen exacto de R1-AC7 sobre el CSV real.
- **R4-AC2** `tests/test_validator.py`: acepta `SELECT` válidos (incluida una CTE) y rechaza al menos: `DROP TABLE`, dos sentencias separadas por `;`, `UPDATE`, tabla no permitida (`sqlite_master`), comentario, `PRAGMA` y función no permitida.
- **R4-AC3** `tests/test_api.py` (LLM simulado con dependency override): caso feliz 200; LLM que lanza error -> 502; LLM que devuelve SQL peligroso -> 422.
- **R4-AC4** `pytest -q` pasa en un entorno limpio sin red y sin `NVIDIA_API_KEY`.

## R5 - README

En español, con: requisitos y cómo ejecutar paso a paso (instalar, generar, limpiar/cargar, levantar la API, ejemplo `curl`, tests); decisiones tomadas (resumen de `decisions.md`); qué haría con más tiempo; cómo usé la IA (qué pedí, qué acepté, qué corregí, resumido desde `ai-log.md`); tiempo total real invertido.

## R6 - Repositorio y proceso

- **R6-AC1** Repositorio público de GitHub.
- **R6-AC2** Historial con un commit por tarea (mínimo 10 commits), sin ningún commit que contenga claves, ni siquiera borradas después.
- **R6-AC3** `.env.example` sin valores reales; `.env`, `*.db` y `data/rejected.csv` ignorados.
- **R6-AC4** `time-log.md` con el tiempo real; total en el README.