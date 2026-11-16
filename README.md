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
