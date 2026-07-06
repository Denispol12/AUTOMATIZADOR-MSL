"""
Test de integración REAL contra la API de DeepSeek.

IMPORTANTE: Este test consume crédito real de la cuenta DeepSeek.
Ejecútalo manualmente solo cuando quieras verificar la conexión real:

    pytest tests/test_integracion_real.py -v -s

El flag -s muestra la respuesta de DeepSeek en la terminal.

Se salta automáticamente si la variable de entorno DEEPSEEK_API_KEY
no está configurada (o si la misma key del código es la que quieres
usar, descomenta la línea FORCE_RUN al final).
"""

import os
from pathlib import Path

import pytest

import main

# ── PDF de prueba real (copiado en fixtures/) ──────────────────────────────────
PDF_REAL = Path(__file__).parent / "fixtures" / "maize_cnn_bilstm.pdf"

# ── Condición de salto ─────────────────────────────────────────────────────────
# El test se omite a menos que exista la variable de entorno DEEPSEEK_API_KEY.
# Para ejecutarlo: set DEEPSEEK_API_KEY=sk-xxxx  (o export en bash)
# También puedes forzar la ejecución descomentando FORCE_RUN abajo.
DEEPSEEK_KEY_ENV = os.getenv("DEEPSEEK_API_KEY")

# FORCE_RUN = True  # ← descomenta esta línea para forzar la ejecución
FORCE_RUN = False

skip_si_sin_key = pytest.mark.skipif(
    not DEEPSEEK_KEY_ENV and not FORCE_RUN,
    reason=(
        "Test de integración real omitido: configura la variable de entorno "
        "DEEPSEEK_API_KEY o pon FORCE_RUN = True en el test para ejecutarlo."
    ),
)


@skip_si_sin_key
def test_evaluar_pdf_real_con_deepseek(test_db, monkeypatch, tmp_path):
    """
    Llama a evaluar_extraccion_pdf() con:
      - Un PDF real de ~3.6 MB (artículo académico sobre maíz e IA).
      - 1 pregunta categórica sobre la técnica de IA usada.
      - La API de DeepSeek real (no mockeada).

    Verifica:
      1. La respuesta es un dict no vacío.
      2. El valor para la pregunta categórica está entre las opciones
         configuradas O es "No especificado" (respuesta válida del modelo).
    """
    client = test_db  # BD temporal, DB_PATH ya parcheada por el fixture

    # Si existe la env var, úsala para actualizar el cliente en tiempo de test
    if DEEPSEEK_KEY_ENV:
        import openai as openai_sdk
        monkeypatch.setattr(
            main,
            "cliente_deepseek",
            openai_sdk.OpenAI(
                api_key=DEEPSEEK_KEY_ENV,
                base_url="https://api.deepseek.com",
            ),
        )
    # Si FORCE_RUN=True sin env var, usa el cliente hardcodeado en main.py

    # --- Insertar pregunta categórica de prueba ---
    opciones = ["CNN", "BiLSTM", "SVM", "Random Forest", "Transformer", "Otro"]
    r = client.post("/preguntas-extraccion", json={
        "texto_pregunta": "¿Qué técnica de inteligencia artificial se usa principalmente?",
        "tipo": "categorica",
        "opciones": opciones,
    })
    assert r.status_code == 200, f"Error al crear pregunta: {r.text}"
    pregunta_id = r.json()["id"]

    # Opciones válidas (incluyendo la que agrega el sistema)
    opciones_validas = set(opciones) | {"No especificado"}

    print(f"\n[Integración] PDF: {PDF_REAL.name} ({PDF_REAL.stat().st_size / 1024:.0f} KB)")
    print(f"[Integración] Pregunta ID {pregunta_id}: técnica de IA")
    print(f"[Integración] Opciones válidas: {sorted(opciones_validas)}")
    print("[Integración] Llamando a DeepSeek API... (puede tardar ~15-30s)")

    # --- Llamar a la función real ---
    import asyncio
    resultado = asyncio.run(main.evaluar_extraccion_pdf(PDF_REAL))

    print(f"[Integración] Respuesta de DeepSeek: {resultado}")

    # --- Asserts ---
    assert isinstance(resultado, dict), (
        f"Se esperaba un dict, se obtuvo: {type(resultado)} → {resultado}"
    )
    assert len(resultado) > 0, (
        "DeepSeek devolvió un dict vacío — posible error de parseo JSON o API"
    )

    clave = str(pregunta_id)
    assert clave in resultado, (
        f"La respuesta no contiene la clave '{clave}' de la pregunta. "
        f"Respuesta completa: {resultado}"
    )

    respuesta_modelo = str(resultado[clave]).strip()
    assert respuesta_modelo in opciones_validas, (
        f"La respuesta '{respuesta_modelo}' no está entre las opciones válidas: "
        f"{sorted(opciones_validas)}\n"
        f"(El modelo puede haber inventado texto — revisar el prompt)"
    )

    print(f"[Integracion] PASS - Respuesta valida: '{respuesta_modelo}'")


@skip_si_sin_key
def test_evaluar_lote_bibtex_real_con_deepseek(test_db, monkeypatch):
    """
    Verifica que evaluar_lote_bibtex() llame exitosamente a DeepSeek
    de extremo a extremo cuando la API key está configurada.
    """
    # Si existe la env var, úsala para actualizar el cliente en tiempo de test
    if DEEPSEEK_KEY_ENV:
        import openai as openai_sdk
        monkeypatch.setattr(
            main,
            "cliente_deepseek",
            openai_sdk.OpenAI(
                api_key=DEEPSEEK_KEY_ENV,
                base_url="https://api.deepseek.com",
            ),
        )

    # 1. Crear 2 entradas de prueba con título y abstract reales
    entradas = [
        {
            "titulo": "Deep Learning for Automatic Insect Pest Detection in Agriculture",
            "autores": "John Doe, Jane Smith",
            "anio": "2023",
            "revista": "Computers and Electronics in Agriculture",
            "abstract": "In this paper, we propose a novel convolutional neural network architecture for detecting internal insect infestation in agricultural crops. Our method achieves high accuracy and uses near-infrared images coupled with deep learning techniques.",
            "palabras_clave": "deep learning, pest detection, agriculture, computer vision"
        },
        {
            "titulo": "Traditional Manual Trapping Methods for Orchard Pests",
            "autores": "Bob Johnson",
            "anio": "2018",
            "revista": "Journal of Pest Management",
            "abstract": "We evaluate traditional manual traps and human visual inspection for counting orchard pests. This study does not use any digital imaging or artificial intelligence models, relying entirely on physical inspection by field workers.",
            "palabras_clave": "manual trap, visual inspection, agriculture"
        }
    ]

    print("\n[Integración BibTeX] Llamando a evaluar_lote_bibtex con DeepSeek V4 Pro... (puede tardar ~5-15s)")
    
    # 2. Llamar a evaluar_lote_bibtex() con esas entradas
    import asyncio
    resultados = asyncio.run(main.evaluar_lote_bibtex(entradas))

    print(f"[Integración BibTeX] Resultados reales devueltos:")
    for idx, res in enumerate(resultados):
        print(f"  Artículo {idx} -> Decision: {res.get('decision')}, Confianza: {res.get('confianza')}, Justificacion: {res.get('justificacion')}")

    # 3. Verificar que devuelva una lista con la misma cantidad de elementos enviados
    assert isinstance(resultados, list), f"Se esperaba una lista, se obtuvo: {type(resultados)}"
    assert len(resultados) == len(entradas), f"Se esperaban {len(entradas)} resultados, se obtuvieron {len(resultados)}"

    # Cada elemento tiene una decisión válida
    decisiones_validas = {"incluido", "excluido", "revisar_manualmente"}
    for idx, res in enumerate(resultados):
        decision = res.get("decision")
        assert decision in decisiones_validas, (
            f"El artículo {idx} tiene una decisión inválida: '{decision}'"
        )
