"""
Tests para el endpoint POST /preguntas-extraccion.

Usa el fixture `test_db` (conftest.py) que garantiza una BD temporal
completamente aislada de msl_resultados.db.
"""


def test_crear_pregunta_categorica(test_db):
    """
    Verifica que POST /preguntas-extraccion:
      - Persiste una pregunta categórica con texto_pregunta, tipo y opciones.
      - Devuelve las 3 opciones esperadas en la respuesta.
      - El registro es recuperable vía GET /preguntas-extraccion.
    """
    client = test_db

    payload = {
        "texto_pregunta": "Técnica de IA",
        "tipo": "categorica",
        "opciones": ["CNN", "SVM", "Otro"],
    }

    # --- Crear la pregunta ---
    response = client.post("/preguntas-extraccion", json=payload)

    assert response.status_code == 200, (
        f"Se esperaba 200, se obtuvo {response.status_code}: {response.text}"
    )

    data = response.json()

    # Campos básicos
    assert data["texto_pregunta"] == "Técnica de IA"
    assert data["tipo"] == "categorica"

    # Las 3 opciones deben estar presentes y en el mismo orden
    assert isinstance(data["opciones"], list), "opciones debe ser una lista"
    assert data["opciones"] == ["CNN", "SVM", "Otro"], (
        f"Opciones inesperadas: {data['opciones']}"
    )

    # --- Verificar persistencia vía GET ---
    pregunta_id = data["id"]
    get_response = client.get("/preguntas-extraccion")

    assert get_response.status_code == 200
    preguntas = get_response.json()

    ids = [p["id"] for p in preguntas]
    assert pregunta_id in ids, (
        f"La pregunta con id={pregunta_id} no aparece en GET /preguntas-extraccion"
    )

    guardada = next(p for p in preguntas if p["id"] == pregunta_id)
    assert guardada["opciones"] == ["CNN", "SVM", "Otro"]
