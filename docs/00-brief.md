# 00 - Brief (fuente original)

> Texto literal del correo recibido. No editar. Si hay conflicto entre cualquier otro documento y este, gana este.

Soy Victor. Hace un tiempo nos mandaste tu CV y lo tenemos guardado. Ahora tenemos abierta una posición de Python y datos (pide LLMs y agentes en producción) para un cliente, 100% remoto, entre 1.000 y 1.400 USD al mes, y por tu experiencia tu perfil encaja.

El siguiente paso es una prueba técnica de no más de 3 horas:

Haz un pequeño proyecto en Python con datos de pedidos.

1. **Carga:** genera un CSV de al menos 1.000 pedidos (fecha, cliente, país, producto, importe y estado) con algunos errores a propósito: duplicados, fechas mal escritas e importes vacíos. Escribe un script que lo limpie y lo guarde en PostgreSQL, SQLite o DuckDB.
2. **Modelos:** dos vistas SQL, ventas por mes y país, y los 10 clientes que más compran.
3. **API con FastAPI (obligatorio):** un endpoint que recibe una pregunta en lenguaje natural, por ejemplo "¿cuánto vendimos en España en marzo?", usa un LLM para convertirla en una consulta, la valida antes de ejecutarla (solo lectura y solo las tablas permitidas) y devuelve el resultado. Si el LLM falla o devuelve algo no válido, responde con un error claro.
4. **Al menos 3 tests con pytest:** la limpieza, la validación de la consulta y el endpoint con el LLM simulado.
5. **Un README** con cómo ejecutarlo, las decisiones que tomaste, qué harías con más tiempo y cómo usaste la IA (qué le pediste, qué aceptaste y qué corregiste).

Puedes usar el LLM que quieras (OpenAI, Claude, Gemini o uno local), pero no subas tu clave al repositorio.

Ve haciendo commits a medida que avanzas, para que se vea el progreso y cómo piensas; un solo commit con todo no vale.

**Entrega:** responder al correo con el enlace a un repositorio público de GitHub en un plazo de 48 horas desde que se lea, indicando cuánto tiempo llevó. Si la prueba está bien, se agenda una reunión de 30 minutos.
