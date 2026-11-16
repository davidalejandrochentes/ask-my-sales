# Registro de uso de la IA

Se rellena en el momento, no al final. Es la base de la sección "cómo usé la IA" del README. Registrar también lo que el agente hizo mal.

Formato de cada entrada:

| Fecha | Tarea | Herramienta | Qué pedí | Qué acepté | Qué corregí o rechacé y por qué |
|---|---|---|---|---|---|
| 2026-11-15 | Planificación | Claude (chat) | Entender el correo de la prueba y proponer una metodología SDD y la estructura de `docs/` | Estructura de `docs/`, ciclo de una tarea por commit, criterios de aceptación en la especificación | (completar: qué cambié respecto a la propuesta) |
| 2026-11-16 | T1-T4 | opencode | Generar CSV sucio, limpieza, carga SQLite, vistas SQL | Código de `generate_data.py`, `cleaning.py`, `clean_load.py`, `db.py`, `views.sql` | Ajusté formato de fechas en generador para que pase validación exacta R1-AC3 |
| 2026-11-16 | T5 | opencode | Tests de vistas SQL | Tests en `test_views.py` verificando R2-AC1 a R2-AC3 | Ninguno, pasaron a la primera |
| 2026-11-16 | T6 | opencode | Validador SQL con sqlglot | Implementación completa en `validator.py` + 56 tests en `test_validator.py` | Añadí `exp.TsOrDsToTimestamp` a funciones permitidas tras descubrir que sqlglot lo genera internamente para `STRFTIME` |
| 2026-11-16 | T7 | opencode | Cliente LLM NVIDIA + prompt | `llm.py` con protocolo, cliente, post-procesado, contexto de esquema | Corregí importación de `Depends` en `llm.py` (no era necesaria), usé `httpx.Client` explícito para evitar error `proxies` en openai SDK |
| 2026-11-16 | T8 | opencode | Endpoint FastAPI `/ask` + `/health` | `main.py` con flujo completo, mapeo de errores 503/502/422/400 | Cambié `get_llm_client` para recibir `Settings` y evitar llamada a `get_settings()` en constructor |
| 2026-11-16 | T9 | opencode | Tests API con LLM simulado | `test_api.py` con `FakeLLM`, 7 tests cubriendo 200/502/422/503 | Usé `monkeypatch` en `app.main.get_llm_client` y `app.config.get_settings` para aislar tests |
| 2026-11-16 | T10 | opencode | Verificación extremo a extremo con clave real | 5 preguntas contra API real | LLM respondió 502 "LLM unavailable" (timeout de red/API). Validación y manejo de errores funcionan correctamente (502, 503, 422). Pregunta peligrosa rechazada con 422 INVALID_SQL. |
