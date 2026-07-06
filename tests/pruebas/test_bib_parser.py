"""
Script de diagnóstico del parser BibTeX del proyecto.
Analiza cuántas entradas pierde bibtexparser v1 y por qué.
Ejecutar: python test_bib_parser.py <archivo.bib>
"""
import sys
import re
import bibtexparser

def contar_entradas_raw(texto_bib: str) -> int:
    """Cuenta las entradas usando un regex simple sin parsear."""
    # Busca todas las líneas que empiezan con @TIPO{ o @TIPO(
    return len(re.findall(r'^@(?!comment|preamble|string)[a-zA-Z]+\s*[{(]',
                          texto_bib, re.MULTILINE | re.IGNORECASE))

def main():
    ruta = sys.argv[1] if len(sys.argv) > 1 else None
    
    if ruta:
        with open(ruta, "rb") as f:
            raw = f.read()
        texto_bib = raw.decode("utf-8", errors="replace")
    else:
        # Demo con datos sintéticos
        texto_bib = """
@ARTICLE{id001, title={A}, year={2020}, abstract={90% accuracy}}
@CONFERENCE{id002, title={B}, year={2021}}
@REVIEW{id003, title={C}, year={2022}}
@ARTICLE{id004, title={D {nested braces}}, year={2023}}
@ARTICLE{id005, title={E}, year={2024}}
"""
    
    total_raw = contar_entradas_raw(texto_bib)
    
    # Parser ACTUAL del proyecto
    parser = bibtexparser.bparser.BibTexParser(common_strings=True)
    parser.ignore_nonstandard_types = False
    bib_db = bibtexparser.loads(texto_bib, parser=parser)
    total_parseadas = len(bib_db.entries)
    
    print(f"=" * 60)
    print(f"DIAGNÓSTICO DEL PARSER BIBTEX")
    print(f"=" * 60)
    print(f"Entradas encontradas con regex (raw): {total_raw}")
    print(f"Entradas parseadas por bibtexparser:  {total_parseadas}")
    print(f"Entradas PERDIDAS:                    {total_raw - total_parseadas}")
    print()
    
    # Contar por tipo
    tipos_raw = {}
    for m in re.finditer(r'^@([a-zA-Z]+)\s*[{(]', texto_bib, re.MULTILINE):
        t = m.group(1).upper()
        if t not in ('COMMENT', 'PREAMBLE', 'STRING'):
            tipos_raw[t] = tipos_raw.get(t, 0) + 1
    
    tipos_parse = {}
    for e in bib_db.entries:
        t = e.get('ENTRYTYPE', 'unknown').upper()
        tipos_parse[t] = tipos_parse.get(t, 0) + 1
    
    print("Tipos detectados (raw):")
    for t, n in sorted(tipos_raw.items()):
        parseadas = tipos_parse.get(t, 0)
        perdidas = n - parseadas
        status = f"  ← PIERDE {perdidas}" if perdidas > 0 else ""
        print(f"  @{t}: {n} raw | {parseadas} parseadas{status}")
    
    print()
    if hasattr(bib_db, 'failed_blocks') and bib_db.failed_blocks:
        print(f"Bloques fallidos registrados por bibtexparser: {len(bib_db.failed_blocks)}")
        for i, fb in enumerate(bib_db.failed_blocks[:5]):
            print(f"  [{i+1}] {str(fb)[:120]}")
    else:
        print("No se registraron bloques fallidos explícitamente.")

if __name__ == "__main__":
    main()
