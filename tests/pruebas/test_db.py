import sqlite3
from main import init_db, DB_PATH
init_db()
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cursor.fetchall()]
print('Tablas en la base de datos:', tables)
if 'extraccion_respuestas_otras' in tables:
    print('OK: La tabla extraccion_respuestas_otras se creo exitosamente.')
    cursor.execute("PRAGMA table_info(extraccion_respuestas_otras);")
    columns = cursor.fetchall()
    print('Columnas:')
    for col in columns:
        print(f' - {col[1]} ({col[2]})')
else:
    print('ERROR: No se encontro la tabla.')
conn.close()
