import sqlite3
from main import init_db, DB_PATH, _get_conn, construir_prompt_extraccion

init_db()

with _get_conn() as conn:
    conn.execute('DELETE FROM preguntas_extraccion')
    
    conn.execute('''
        INSERT INTO preguntas_extraccion (texto_pregunta, tipo, opciones, orden)
        VALUES 
        ('Técnica de IA utilizada', 'categorica', '["CNN", "SVM"]', 1),
        ('Precisión reportada', 'numerica', NULL, 2),
        ('Resumen', 'texto_libre', NULL, 3)
    ''')

prompt = construir_prompt_extraccion()
print('--- PROMPT GENERADO ---')
print(prompt)
print('-----------------------')
