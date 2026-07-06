"""
Tests para evaluar_extraccion_pdf().

Verifica que la función parsea correctamente la respuesta JSON del modelo
sin realizar ninguna llamada real a la API (DeepSeek/Gemini).

Estrategia de mock:
  - main.cliente_deepseek  → inyectado con create=True (no existe en módulo)
                             simula .files.upload() y .files.delete()
  - main._generar_con_reintento → corrutina AsyncMock que devuelve texto JSON
  - main.ultima_llamada = 0.0  → evita el sleep de rate-limiting
  - builtins.open           → mock mínimo para que el with open(...) no falle
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest

import main

# PDF de prueba que existe en el repo (15 bytes, suficiente para open())
DUMMY_PDF = Path(__file__).parent / "fixtures" / "dummy.pdf"


@pytest.fixture
def preguntas_insertadas(test_db):
    """
    Extiende test_db insertando 2 preguntas de prueba y devuelve
    (client, id_categorica, id_numerica).
    """
    client = test_db

    r1 = client.post("/preguntas-extraccion", json={
        "texto_pregunta": "Técnica de IA",
        "tipo": "categorica",
        "opciones": ["CNN", "SVM", "Otro"],
    })
    assert r1.status_code == 200
    id_cat = r1.json()["id"]

    r2 = client.post("/preguntas-extraccion", json={
        "texto_pregunta": "Año de publicación",
        "tipo": "numerica",
        "opciones": None,
    })
    assert r2.status_code == 200
    id_num = r2.json()["id"]

    return client, id_cat, id_num


def _run_evaluar(respuesta_texto: str) -> dict:
    """
    Ejecuta evaluar_extraccion_pdf() con todos los puntos externos mockeados.
    Devuelve el dict resultado.
    """
    mock_respuesta = MagicMock()
    mock_respuesta.text = respuesta_texto

    mock_archivo = MagicMock()
    mock_archivo.name = "files/dummy-test-id"

    mock_cliente = MagicMock()
    mock_cliente.files.upload.return_value = mock_archivo
    mock_cliente.files.delete.return_value = None

    # cliente_deepseek no existe en main como atributo de módulo,
    # se inyecta con create=True para que patch lo añada temporalmente.
    with (
        patch("main.cliente_deepseek", mock_cliente, create=True),
        patch(
            "main._generar_con_reintento",
            new=AsyncMock(return_value=mock_respuesta),
        ),
        patch.object(main, "ultima_llamada", 0.0),
        # Evitar lectura real del PDF (el upload está mockeado de todas formas)
        patch("builtins.open", mock_open(read_data=b"%PDF-1.0\n%%EOF\n")),
    ):
        return asyncio.run(main.evaluar_extraccion_pdf(DUMMY_PDF))


def test_evaluar_extraccion_pdf_parsea_respuesta(preguntas_insertadas):
    """
    Verifica que evaluar_extraccion_pdf():
      1. Llama a _generar_con_reintento mockeada (sin créditos de API).
      2. Parsea el JSON de la respuesta simulada correctamente.
      3. Devuelve un dict con los IDs de pregunta como claves y valores correctos.
    """
    _client, id_cat, id_num = preguntas_insertadas

    respuesta_simulada = f'{{"{id_cat}": "CNN", "{id_num}": "2023"}}'
    resultado = _run_evaluar(respuesta_simulada)

    assert isinstance(resultado, dict), (
        f"Se esperaba un dict, se obtuvo: {type(resultado)}"
    )
    assert str(id_cat) in resultado, (
        f"La clave '{id_cat}' (categórica) no está en el resultado: {resultado}"
    )
    assert str(id_num) in resultado, (
        f"La clave '{id_num}' (numérica) no está en el resultado: {resultado}"
    )
    assert resultado[str(id_cat)] == "CNN", (
        f"Se esperaba 'CNN', se obtuvo: {resultado[str(id_cat)]}"
    )
    assert resultado[str(id_num)] == "2023", (
        f"Se esperaba '2023', se obtuvo: {resultado[str(id_num)]}"
    )


def test_evaluar_extraccion_pdf_maneja_json_con_markdown(preguntas_insertadas):
    """
    Verifica que la función elimina correctamente los bloques ```json ... ```
    que los modelos suelen incluir alrededor del JSON.
    """
    _client, id_cat, id_num = preguntas_insertadas

    respuesta_con_markdown = (
        f'```json\n{{"{id_cat}": "SVM", "{id_num}": "2022"}}\n```'
    )
    resultado = _run_evaluar(respuesta_con_markdown)

    assert isinstance(resultado, dict)
    assert resultado.get(str(id_cat)) == "SVM", (
        f"Se esperaba 'SVM', se obtuvo: {resultado.get(str(id_cat))}"
    )
    assert resultado.get(str(id_num)) == "2022", (
        f"Se esperaba '2022', se obtuvo: {resultado.get(str(id_num))}"
    )
