import sqlite3
from main import init_db, _get_conn, obtener_frecuencias_pregunta

# 1. Asegurar estado
init_db()
with _get_conn() as conn:
    conn.execute('DELETE FROM preguntas_extraccion')
    conn.execute('DELETE FROM extraccion_respuestas_categoricas')
    conn.execute('''
        INSERT INTO preguntas_extraccion (id, texto_pregunta, tipo, opciones, orden)
        VALUES (88, 'Modelo', 'categorica', '["A", "B", "C"]', 1)
    ''')
    
    # 2. Insertar algunas respuestas: 3 para A, 2 para C, 0 para B
    # Articulo 1 -> A
    conn.execute("INSERT INTO extraccion_respuestas_categoricas (articulo_nombre, pregunta_id, opcion_texto, valor) VALUES ('art1.pdf', 88, 'A', 1)")
    conn.execute("INSERT INTO extraccion_respuestas_categoricas (articulo_nombre, pregunta_id, opcion_texto, valor) VALUES ('art1.pdf', 88, 'B', 0)")
    conn.execute("INSERT INTO extraccion_respuestas_categoricas (articulo_nombre, pregunta_id, opcion_texto, valor) VALUES ('art1.pdf', 88, 'C', 0)")
    
    # Articulo 2 -> A
    conn.execute("INSERT INTO extraccion_respuestas_categoricas (articulo_nombre, pregunta_id, opcion_texto, valor) VALUES ('art2.pdf', 88, 'A', 1)")
    
    # Articulo 3 -> A
    conn.execute("INSERT INTO extraccion_respuestas_categoricas (articulo_nombre, pregunta_id, opcion_texto, valor) VALUES ('art3.pdf', 88, 'A', 1)")
    
    # Articulo 4 -> C
    conn.execute("INSERT INTO extraccion_respuestas_categoricas (articulo_nombre, pregunta_id, opcion_texto, valor) VALUES ('art4.pdf', 88, 'C', 1)")
    
    # Articulo 5 -> C
    conn.execute("INSERT INTO extraccion_respuestas_categoricas (articulo_nombre, pregunta_id, opcion_texto, valor) VALUES ('art5.pdf', 88, 'C', 1)")
    
    # Articulo 6 -> (Ninguno elegido, algo anomalo)
    conn.execute("INSERT INTO extraccion_respuestas_categoricas (articulo_nombre, pregunta_id, opcion_texto, valor) VALUES ('art6.pdf', 88, 'B', 0)")

# 3. Probar funcion
res = obtener_frecuencias_pregunta(88)
print("Frecuencias obtenidas:", res)
