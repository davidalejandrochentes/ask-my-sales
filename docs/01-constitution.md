
# 01 - Constitución del proyecto
 
Reglas no negociables. Aplican al humano y al agente.
 
1. **Fuente de verdad.** Manda `docs/`. Orden de prioridad si hay conflicto: `00-brief` > `01-constitution` > `02-spec` > `03-plan` > `04-tasks`. Lo que no está escrito no se inventa: se anota en `open-questions.md` y se pregunta.
2. **Alcance mínimo.** Se construye solo lo que pide `02-spec.md`. Nada de autenticación, Docker, frontend, ORM, caché ni endpoints extra. Las mejoras van a la sección "qué haría con más tiempo" del README.
3. **Una tarea, un commit.** Cada tarea de `04-tasks.md` termina en un único commit con el mensaje indicado. Conventional Commits, en inglés, imperativo, máximo 72 caracteres en el asunto, más un párrafo que explica el cambio y una línea `Refs:` con los criterios de `02-spec.md` (mensajes completos en `04-tasks.md`). Quien lea el historial en GitHub debe entender qué se hizo y por qué. Un commit nunca deja los tests rotos.
4. **Seguridad de secretos.** La clave del LLM solo existe como variable de entorno. `.env` está en `.gitignore`; `.env.example` no lleva valores reales. Nunca se imprime, registra ni commitea una clave, ni siquiera "temporalmente".
5. **El SQL del LLM es entrada no confiable.** Se valida antes de ejecutar y se ejecuta en una conexión de solo lectura. Dos barreras independientes, no una.
6. **Tests deterministas.** Sin red, sin LLM real, sin dependencia del reloj ni de datos fuera del repo. El endpoint se prueba con un LLM simulado.
7. **Dependencias mínimas.** Solo las de `03-plan.md`. Biblioteca estándar antes que dependencia nueva. Cualquier adición se justifica en `decisions.md` antes de instalarla.
8. **No se inventan APIs.** Si no se está seguro de cómo funciona una función de una librería, se lee la documentación o se pregunta. Prohibido "probar a ver si compila" con nombres supuestos.
9. **Honestidad documental.** `ai-log.md` y `time-log.md` reflejan lo que realmente pasó, escrito en el momento, nunca reconstruido al final. Se registran también los errores del agente y las correcciones.
10. **Idioma.** Documentación y README en español. Código, comentarios, nombres y commits en inglés.
11. **Definición de "hecha"** para una tarea: criterio de aceptación cumplido, `pytest -q` y `ruff check .` en verde, documentos de seguimiento actualizados, commit realizado.
12. **Presupuesto de tiempo.** La prueba admite 3 horas. Si una tarea se alarga el doble de lo estimado, se detiene y se recorta alcance en lugar de seguir.
 
