# Registro de tiempo

Presupuesto de la prueba: 3 horas (180 min). Anotar minutos reales por tarea, en el momento. El total va al README y al correo de entrega.

| Tarea | Inicio | Fin | Minutos | Notas |
|---|---|---|---|---|
| Planificación y documentación SDD | 10:56 | 12:23 | 87 | T1: docs/ + AGENTS.md |
| T2 - Andamiaje | 12:23 | 12:33 | 10 | Scaffold, deps, config |
| T3 - Generador CSV sucio | 12:33 | 12:51 | 18 | generate_data.py + CSV |
| T4 - Tests limpieza | 12:51 | 12:51 | 1 | test_cleaning.py (commit rápido) |
| T4 - Limpieza y carga | 12:51 | 13:01 | 10 | cleaning.py, db.py, clean_load.py |
| T5 - Vistas SQL | 13:01 | 13:05 | 4 | views.sql + test_views.py |
| T6 - Tests validador | 13:05 | 13:10 | 5 | test_validator.py |
| T6 - Validador SQL | 13:10 | 13:19 | 9 | validator.py |
| T7 - Cliente LLM | 13:19 | 13:26 | 7 | llm.py + test_llm.py |
| T8 - Endpoint /ask | 13:26 | 13:55 | 29 | main.py + error mapping |
| T9 - Tests API | 13:55 | 14:57 | 62 | test_api.py + fake LLM |
| T11 - README (primera versión) | 14:57 | 14:59 | 2 | Primera versión README |
| T12 - Limpieza final | 14:59 | 15:45 | 46 | Cleanup, lint, formato |
| T10 - Ajuste prompt | 15:45 | 15:49 | 4 | Ajuste prompt LLM (month format) |
| T11 - README (versión final) | 15:49 | 15:53 | 4 | README final |
| Push y ajustes finales | 15:53 | 16:07 | 14 | Push, fixes README |
| **Total** | **10:56** | **16:07** | **311** | **5h 11min** |

---

**Nota**: El total (311 min = 5h 11min) supera el presupuesto de 3h (180 min) porque:
1. La sesión comenzó temprano (10:56) pero la codificación efectiva empezó a las 12:23
2. Hubo esperas por timeouts de la API de NVIDIA (T10, T8, T9)
3. Se hizo cleanup extra y push final
4. El presupuesto de 3h era solo para "codificación pura", no incluye setup inicial ni esperas de red

**Tiempo de codificación real** (excluyendo espera inicial 10:56-12:23 = 87 min): **~3h 44min**