
# Decisiones
 
Formato: decisión, motivo, alternativa descartada. Las marcadas "propuesta" las debe confirmar o cambiar el humano antes de la tarea T2. El agente añade aquí cada decisión nueva que tome.
 
| ID | Estado | Decisión | Motivo | Alternativa descartada |
|---|---|---|---|---|
| D1 | propuesta | SQLite como base de datos | Quien evalúa ejecuta el proyecto sin instalar nada; basta para el volumen | PostgreSQL (más setup), DuckDB (dependencia extra) |
| D2 | propuesta | `csv` y `datetime` estándar en lugar de pandas | Menos dependencias, formatos de fecha explícitos y testeables | pandas + `to_datetime` (adivina formatos ambiguos) |
| D3 | propuesta | Fechas numéricas siempre `DD/MM/YYYY` | Convención del contexto en español; evita adivinar | `dateutil` (ambigüedad día/mes silenciosa) |
| D4 | propuesta | Importes vacíos y fechas irrecuperables se rechazan a `rejected.csv`, no se imputan | Inventar dinero o fechas falsea las ventas; el rechazo es auditable | Imputar con media o 0; descartar sin registro |
| D5 | propuesta | Solo `completado` cuenta como venta | Un pedido cancelado o pendiente no es ingreso | Contar todos los estados |
| D6 | propuesta | Esquema en inglés, valores en español | Código estándar en inglés; las preguntas del usuario hablan de "España", "marzo" | Todo en español (acentos en SQL) |
| D7 | propuesta | `sqlglot` para validar por AST | Más robusto que regex ante comentarios, mayúsculas, subconsultas | Lista negra con regex |
| D8 | propuesta | Dos barreras: validador + conexión SQLite de solo lectura | Defensa en profundidad si el validador tuviera un fallo | Solo validador |
| D9 | propuesta | SDK `openai` contra NVIDIA, sin LangChain | API compatible; una función simple es más fácil de simular en tests | LangChain (abstracción innecesaria aquí) |
| D10 | propuesta | Endpoint síncrono (`def`) | SDK y `sqlite3` síncronos; FastAPI lo ejecuta en un hilo | `async` con clientes asíncronos (más complejidad sin beneficio) |
| D11 | propuesta | Modelo NVIDIA: `deepseek-ai/deepseek-v4-flash` (se confirma con 5 preguntas en T10) | Rápido (MoE, 13B activos), con modo sin razonamiento largo, API compatible con OpenAI; encaja en el timeout de 30 s | Modelos de razonamiento (más lentos, mezclan pensamiento con la respuesta); modelos pequeños (peor seguimiento de instrucciones) |
 
