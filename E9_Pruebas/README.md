# Unidad 5 CLN - Paso 9 (PIA: renta de vehiculos)

Archivos nuevos (no chocan con los del proyecto base, se pueden copiar a tu repo):
`src/renta/`, `tests/test_renta_*.py`, `datos/matriz_casos_pia.csv`.

## Ejecucion
    python -m venv .venv
    .venv\Scripts\Activate.ps1          # Windows  (macOS/Linux: source .venv/bin/activate)
    python -m pip install -r requirements.txt
    python -m ruff check src tests
    python -m pytest -v tests/test_renta_dominio.py tests/test_renta_servicio.py tests/test_renta_matriz_csv.py
    python -m pytest -v --cov=src.renta --cov-report=term-missing --cov-report=html --cov-fail-under=80
    # abrir htmlcov/index.html

Arquitectura: `dominio.py` (reglas puras) -> `servicio.py` (casos de uso + transaccion) ->
`repositorio.py` (SQLAlchemy, SQLite en memoria). La pasarela de pagos se simula con Mock.
