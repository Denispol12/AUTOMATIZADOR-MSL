"""
Tests para construir_prompt_extraccion().

Verifica que el prompt de extracción se construye correctamente
a partir de las preguntas almacenadas en la BD, SIN llamar a ninguna
API externa (Gemini, DeepSeek, etc.).
"""

import main


def test_prompt_incluye_ambas_preguntas(test_db):
    """
    Con 2 preguntas ya insertadas (1 categórica + 1 numérica):
      - El prompt debe contener el texto de cada pregunta.
      - Para la categórica debe incluir todas sus opciones.
      - Para la numérica debe indicar que se responda con un número.
    """
    client = test_db  # TestClient con BD temporal ya inicializada

    # --- Insertar pregunta categórica ---
    r1 = client.post("/preguntas-extraccion", json={
        "texto_pregunta": "Técnica de IA",
        "tipo": "categorica",
        "opciones": ["CNN", "SVM", "Otro"],
    })
    assert r1.status_code == 200, f"Error al crear pregunta categórica: {r1.text}"

    # --- Insertar pregunta numérica ---
    r2 = client.post("/preguntas-extraccion", json={
        "texto_pregunta": "Año de publicación",
        "tipo": "numerica",
        "opciones": None,
    })
    assert r2.status_code == 200, f"Error al crear pregunta numérica: {r2.text}"

    # --- Llamar directamente a construir_prompt_extraccion() ---
    # Usa la misma main.DB_PATH parcheada por el fixture, por lo que
    # lee las preguntas recién insertadas en la BD temporal.
    prompt = main.construir_prompt_extraccion()

    # --- Asserts sobre el contenido del prompt ---

    # Texto de la pregunta categórica
    assert "Técnica de IA" in prompt, (
        f"El prompt no contiene 'Técnica de IA'.\nPrompt:\n{prompt}"
    )

    # Las 3 opciones de la pregunta categórica deben aparecer en el prompt
    for opcion in ["CNN", "SVM", "Otro"]:
        assert opcion in prompt, (
            f"El prompt no contiene la opción '{opcion}'.\nPrompt:\n{prompt}"
        )

    # Texto de la pregunta numérica
    assert "Año de publicación" in prompt, (
        f"El prompt no contiene 'Año de publicación'.\nPrompt:\n{prompt}"
    )

    # La instrucción numérica debe indicar que se responda con un número
    assert "número" in prompt.lower() or "No especificado" in prompt, (
        f"El prompt no contiene instrucción numérica esperada.\nPrompt:\n{prompt}"
    )

    # El prompt no debe estar vacío ni ser el mensaje de "sin preguntas"
    assert prompt != "No hay preguntas de extracción configuradas."
