import os
from main import generar_grafico_pregunta

def test_grafico():
    # Use existing test data (pregunta_id = 88)
    buf = generar_grafico_pregunta(88)
    with open('test_grafico.png', 'wb') as f:
        f.write(buf.read())
    print("Gráfico generado en test_grafico.png con tamaño:", os.path.getsize('test_grafico.png'), "bytes")

if __name__ == "__main__":
    test_grafico()
