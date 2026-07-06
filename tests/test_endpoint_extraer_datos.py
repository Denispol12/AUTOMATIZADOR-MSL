"""
Tests del flujo completo del endpoint POST /extraer-datos.

Verifica que:
  1. El endpoint devuelve HTTP 200.
  2. Las respuestas categóricas se guardan en formato one-hot correcto
     en la tabla extraccion_respuestas_categoricas:
       - La opción elegida tiene valor=1
       - El resto de opciones tienen valor=0

Sin llamadas a la API real: evaluar_extraccion_pdf() está mockeada.
"""

import sqlite3
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

import main

# PDF mínimo de prueba (ya creado en test_evaluar_extraccion.py)
DUMMY_PDF = Path(__file__).parent / "fixtures" / "dummy.pdf"

# Contenido binario del PDF de prueba para enviarlo como multipart
PDF_BYTES = DUMMY_PDF.read_bytes()


@pytest.fixture
def pregunta_categorica(test_db):
    """
    Inserta 1 pregunta categórica con 3 opciones y devuelve
    (client, pregunta_id, opciones).
    """
    client = test_db

    opciones = ["CNN", "SVM", "Otro"]
    r = client.post("/preguntas-extraccion", json={
        "texto_pregunta": "Técnica de IA",
        "tipo": "categorica",
        "opciones": opciones,
    })
    assert r.status_code == 200, f"Error al crear pregunta: {r.text}"

    pregunta_id = r.json()["id"]
    return client, pregunta_id, opciones


def test_extraer_datos_guarda_one_hot(pregunta_categorica, tmp_path, monkeypatch):
    """
    Flujo completo del endpoint POST /extraer-datos:

    - evaluar_extraccion_pdf() devuelve {"<id>": "CNN"} (mockeado).
    - El endpoint guarda en extraccion_respuestas_categoricas:
        CNN=1, SVM=0, Otro=0, No especificado=0
    - La respuesta HTTP es 200.
    """
    client, pregunta_id, opciones = pregunta_categorica

    # Respuesta simulada del modelo: elige "CNN"
    respuesta_mock = {str(pregunta_id): "CNN"}

    # Redirigir UPLOADS_DIR a tmp_path para no ensuciar uploads/ real
    monkeypatch.setattr(main, "UPLOADS_DIR", tmp_path)

    with patch(
        "main.evaluar_extraccion_pdf",
        new=AsyncMock(return_value=respuesta_mock),
    ):
        response = client.post(
            "/extraer-datos",
            files={"archivo": ("articulo_prueba.pdf", BytesIO(PDF_BYTES), "application/pdf")},
        )

    # --- 1. Verificar HTTP 200 ---
    assert response.status_code == 200, (
        f"Se esperaba 200, se obtuvo {response.status_code}: {response.text}"
    )

    # --- 2. Verificar formato one-hot en la BD ---
    with main._get_conn() as conn:
        filas = conn.execute(
            """
            SELECT opcion_texto, valor
            FROM extraccion_respuestas_categoricas
            WHERE articulo_nombre = ? AND pregunta_id = ?
            ORDER BY opcion_texto
            """,
            ("articulo_prueba.pdf", pregunta_id),
        ).fetchall()

    assert len(filas) > 0, "No se insertaron filas en extraccion_respuestas_categoricas"

    # Construir dict opcion → valor para facilitar los asserts
    resultado_onehot = {f["opcion_texto"]: f["valor"] for f in filas}

    # La opción elegida debe tener valor=1
    assert resultado_onehot.get("CNN") == 1, (
        f"Se esperaba CNN=1, se obtuvo: {resultado_onehot}"
    )

    # Las demás opciones deben tener valor=0
    for opcion_cero in ["SVM", "Otro", "No especificado"]:
        assert resultado_onehot.get(opcion_cero) == 0, (
            f"Se esperaba {opcion_cero}=0, se obtuvo: {resultado_onehot}"
        )

    # Exactamente 1 fila con valor=1 (unicidad del one-hot)
    total_unos = sum(v for v in resultado_onehot.values() if v == 1)
    assert total_unos == 1, (
        f"Debe haber exactamente 1 opción con valor=1, se encontraron {total_unos}: {resultado_onehot}"
    )


def test_extraer_datos_rechaza_no_pdf(pregunta_categorica):
    """
    Verifica que el endpoint rechaza con 400 archivos que no sean .pdf.
    """
    client, _pid, _opciones = pregunta_categorica

    response = client.post(
        "/extraer-datos",
        files={"archivo": ("documento.txt", BytesIO(b"texto"), "text/plain")},
    )

    assert response.status_code == 400, (
        f"Se esperaba 400 para un .txt, se obtuvo {response.status_code}"
    )


def test_extraer_datos_mismatch_fallback_otro(pregunta_categorica, tmp_path, monkeypatch):
    """
    Verifica que si la IA responde con un texto libre que no coincide
    con las opciones configuradas, se marca 'Otro' como 1 (si existe)
    y el texto original de la IA se guarda en extraccion_respuestas_otras.
    """
    client, pregunta_id, opciones = pregunta_categorica

    # Respuesta simulada de la IA que NO coincide con ninguna opción exacta
    texto_original = "Técnica ultra novedosa 3D"
    respuesta_mock = {str(pregunta_id): texto_original}

    # Redirigir UPLOADS_DIR a tmp_path
    monkeypatch.setattr(main, "UPLOADS_DIR", tmp_path)

    with patch(
        "main.evaluar_extraccion_pdf",
        new=AsyncMock(return_value=respuesta_mock),
    ):
        response = client.post(
            "/extraer-datos",
            files={"archivo": ("articulo_prueba.pdf", BytesIO(PDF_BYTES), "application/pdf")},
        )

    assert response.status_code == 200

    # 1. Verificar que 'Otro' tiene valor=1 en extraccion_respuestas_categoricas
    with main._get_conn() as conn:
        filas = conn.execute(
            """
            SELECT opcion_texto, valor
            FROM extraccion_respuestas_categoricas
            WHERE articulo_nombre = ? AND pregunta_id = ?
            ORDER BY opcion_texto
            """,
            ("articulo_prueba.pdf", pregunta_id),
        ).fetchall()

    resultado_onehot = {f["opcion_texto"]: f["valor"] for f in filas}
    
    # 'Otro' debe estar en 1
    assert resultado_onehot.get("Otro") == 1, f"Se esperaba Otro=1, se obtuvo: {resultado_onehot}"
    # Las demás opciones deben estar en 0
    assert resultado_onehot.get("CNN") == 0
    assert resultado_onehot.get("SVM") == 0
    assert resultado_onehot.get("No especificado") == 0

    # 2. Verificar que se guardó en extraccion_respuestas_otras con la columna respuesta_original_ia
    with main._get_conn() as conn:
        fila_otra = conn.execute(
            """
            SELECT respuesta, respuesta_original_ia
            FROM extraccion_respuestas_otras
            WHERE articulo_nombre = ? AND pregunta_id = ?
            """,
            ("articulo_prueba.pdf", pregunta_id),
        ).fetchone()

    assert fila_otra is not None, "Debe existir un registro en extraccion_respuestas_otras"
    assert fila_otra["respuesta"] is None, "La columna respuesta para categóricas debe ser None"
    assert fila_otra["respuesta_original_ia"] == texto_original, (
        f"Se esperaba '{texto_original}', se obtuvo: {dict(fila_otra)}"
    )

    # 3. Verificar que GET /extraccion-respuestas devuelve el campo "originales_ia"
    res_get = client.get("/extraccion-respuestas")
    assert res_get.status_code == 200
    datos = res_get.json()
    art_data = next((item for item in datos if item["articulo_nombre"] == "articulo_prueba.pdf"), None)
    assert art_data is not None
    assert art_data["respuestas"].get(str(pregunta_id)) == "Otro"
    assert art_data["originales_ia"].get(str(pregunta_id)) == texto_original

    # 4. Verificar que GET /exportar-extraccion funciona
    res_excel = client.get("/exportar-extraccion")
    assert res_excel.status_code == 200


def test_eliminar_extraccion_respuestas_articulo(test_db):
    """
    Verifica que DELETE /extraccion-respuestas/{articulo_nombre}
    elimina únicamente las respuestas asociadas a dicho artículo.
    """
    client = test_db

    # Insertar algunas respuestas de prueba
    with main._get_conn() as conn:
        conn.execute(
            """
            INSERT INTO extraccion_respuestas_categoricas (articulo_nombre, pregunta_id, opcion_texto, valor)
            VALUES 
            ('art1.pdf', 1, 'Op1', 1),
            ('art1.pdf', 1, 'Op2', 0),
            ('art2.pdf', 1, 'Op1', 0),
            ('art2.pdf', 1, 'Op2', 1)
            """
        )
        conn.execute(
            """
            INSERT INTO extraccion_respuestas_otras (articulo_nombre, pregunta_id, respuesta)
            VALUES 
            ('art1.pdf', 2, 'Respuesta 1'),
            ('art2.pdf', 2, 'Respuesta 2')
            """
        )

    # 1. Comprobar que inicialmente están ambos artículos
    res_get = client.get("/extraccion-respuestas")
    assert res_get.status_code == 200
    articulos_iniciales = [item["articulo_nombre"] for item in res_get.json()]
    assert "art1.pdf" in articulos_iniciales
    assert "art2.pdf" in articulos_iniciales

    # 2. Eliminar 'art1.pdf'
    res_delete = client.delete("/extraccion-respuestas/art1.pdf")
    assert res_delete.status_code == 200
    assert res_delete.json() == {"ok": True, "articulo": "art1.pdf"}

    # 3. Comprobar que solo queda 'art2.pdf' en las respuestas
    res_get_new = client.get("/extraccion-respuestas")
    articulos_nuevos = [item["articulo_nombre"] for item in res_get_new.json()]
    assert "art1.pdf" not in articulos_nuevos
    assert "art2.pdf" in articulos_nuevos

    # 4. Comprobar que no queda ningún rastro en la base de datos para art1.pdf
    with main._get_conn() as conn:
        count_cat = conn.execute(
            "SELECT COUNT(*) FROM extraccion_respuestas_categoricas WHERE articulo_nombre = 'art1.pdf'"
        ).fetchone()[0]
        count_otras = conn.execute(
            "SELECT COUNT(*) FROM extraccion_respuestas_otras WHERE articulo_nombre = 'art1.pdf'"
        ).fetchone()[0]

    assert count_cat == 0
    assert count_otras == 0


def test_estadisticas_extraccion_detecta_inconsistencias(pregunta_categorica):
    """
    Verifica que GET /estadisticas-extraccion/{pregunta_id}
    devuelve la lista de frecuencias válidas, más la cantidad y el detalle
    de los artículos con categorías obsoletas.
    """
    client, pregunta_id, opciones = pregunta_categorica

    with main._get_conn() as conn:
        conn.execute(
            """
            INSERT INTO extraccion_respuestas_categoricas (articulo_nombre, pregunta_id, opcion_texto, valor)
            VALUES 
            ('art_valid1.pdf', ?, 'CNN', 1),
            ('art_valid1.pdf', ?, 'SVM', 0),
            ('art_valid1.pdf', ?, 'Otro', 0),
            ('art_valid1.pdf', ?, 'No especificado', 0),
            
            ('art_valid2.pdf', ?, 'CNN', 0),
            ('art_valid2.pdf', ?, 'SVM', 1),
            ('art_valid2.pdf', ?, 'Otro', 0),
            ('art_valid2.pdf', ?, 'No especificado', 0),
            
            ('art_obsoleto.pdf', ?, 'CNN', 0),
            ('art_obsoleto.pdf', ?, 'SVM', 0),
            ('art_obsoleto.pdf', ?, 'Otro', 0),
            ('art_obsoleto.pdf', ?, 'No especificado', 0),
            ('art_obsoleto.pdf', ?, 'Random Forest', 1)
            """,
            (
                pregunta_id, pregunta_id, pregunta_id, pregunta_id,
                pregunta_id, pregunta_id, pregunta_id, pregunta_id,
                pregunta_id, pregunta_id, pregunta_id, pregunta_id, pregunta_id
            )
        )

    response = client.get(f"/estadisticas-extraccion/{pregunta_id}")
    assert response.status_code == 200
    res_data = response.json()

    assert "frecuencias" in res_data
    assert "filas_omitidas" in res_data
    assert "detalle_omitidas" in res_data

    frecuencias = res_data["frecuencias"]
    cnn_freq = next((f for f in frecuencias if f["opcion"] == "CNN"), None)
    svm_freq = next((f for f in frecuencias if f["opcion"] == "SVM"), None)
    assert cnn_freq is not None and cnn_freq["cantidad"] == 1
    assert svm_freq is not None and svm_freq["cantidad"] == 1

    rf_freq = next((f for f in frecuencias if f["opcion"] == "Random Forest"), None)
    assert rf_freq is None

    assert res_data["filas_omitidas"] == 1
    assert res_data["detalle_omitidas"] == ["art_obsoleto.pdf"]
