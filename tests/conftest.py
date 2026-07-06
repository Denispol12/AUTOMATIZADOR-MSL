"""
Configuración global de pytest para el proyecto MSL Validator.

El fixture `test_db` garantiza que cada test:
  1. Usa una base de datos SQLite temporal (test_msl.db) completamente
     aislada de msl_resultados.db.
  2. Recibe un TestClient de FastAPI ya inicializado (startup ejecutado).
  3. Al finalizar, borra test_msl.db automáticamente.
"""

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


# Hide pdfplumber from tests so evaluar_extraccion_pdf falls back to read_bytes(),
# preventing errors when builtins.open is mocked.
sys.modules['pdfplumber'] = None

TEST_DB_PATH = Path("test_msl.db")


@pytest.fixture
def test_db(monkeypatch, tmp_path):
    """
    Fixture de base de datos aislada.

    - Parchea `main.DB_PATH` con un archivo temporal en tmp_path para que
      `_get_conn()` e `init_db()` nunca toquen msl_resultados.db.
    - Construye el TestClient (dispara @app.on_event('startup') → init_db()).
    - Hace yield del cliente para que el test lo use.
    - Después del test borra el archivo de BD temporal.
    """
    import main  # importación diferida para que el parche funcione

    db_temp = tmp_path / "test_msl.db"

    # Parchar la variable global antes de que TestClient llame a startup
    monkeypatch.setattr(main, "DB_PATH", db_temp)

    with TestClient(main.app) as client:
        yield client

    # Limpieza explícita (tmp_path ya lo hace, pero por claridad)
    if db_temp.exists():
        db_temp.unlink()
