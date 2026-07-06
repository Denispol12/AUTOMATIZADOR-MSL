import sqlite3
import json
from main import init_db, DB_PATH, _get_conn

# 1. Preparar base de datos
init_db()
with _get_conn() as conn:
    conn.execute('DELETE FROM preguntas_extraccion')
    conn.execute('DELETE FROM extraccion_respuestas_categoricas')
    conn.execute('DELETE FROM extraccion_respuestas_otras')
    conn.execute('''
        INSERT INTO preguntas_extraccion (id, texto_pregunta, tipo, opciones, orden)
        VALUES 
        (99, 'Técnica de IA utilizada', 'categorica', '["CNN", "SVM"]', 1),
        (100, 'Precisión obtenida', 'numerica', NULL, 2),
        (101, 'Conclusión principal', 'texto_libre', NULL, 3)
    ''')
    
# 2. Mockear y ejecutar logica de extraccion-datos localmente
from fastapi import UploadFile
import io
import asyncio
from main import extraer_datos

class MockUploadFile:
    def __init__(self, filename):
        self.filename = filename
        self.file = io.BytesIO(b'pdf content')

import main
async def mock_evaluar(ruta): 
    return {
        '99': 'CNN',
        '100': '95.5',
        '101': 'Es una excelente investigación.'
    }
main.evaluar_extraccion_pdf = mock_evaluar

async def run_test():
    archivo = MockUploadFile('test_doc.pdf')
    res = await extraer_datos(archivo)
    print('Respuestas mockeadas:', res)
    
    with _get_conn() as conn:
        filas_cat = conn.execute('SELECT * FROM extraccion_respuestas_categoricas').fetchall()
        print('Total filas categoricas insertadas:', len(filas_cat))
        for f in filas_cat:
            print(f' - Opcion: {f["opcion_texto"]}, Valor: {f["valor"]}')
            
        filas_otr = conn.execute('SELECT * FROM extraccion_respuestas_otras').fetchall()
        print('Total filas otras insertadas:', len(filas_otr))
        for f in filas_otr:
            print(f' - ID Preg: {f["pregunta_id"]}, Resp: {f["respuesta"]}')

asyncio.run(run_test())
