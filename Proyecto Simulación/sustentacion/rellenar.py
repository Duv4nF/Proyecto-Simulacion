"""Rellena las plantillas de la sustentación con las cifras del análisis.

Las plantillas (sustentacion/plantillas/*) usan marcadores {{Nombre}}, con los mismos nombres
que las macros \\cifraNombre de articulo/tablas/cifras.tex. Así el guion y la guía de estudio
citan exactamente las mismas cifras que el artículo y las diapositivas.

Uso:  python sustentacion/rellenar.py
Salida: sustentacion/guion_sustentacion.md y sustentacion/guia_estudio.html
"""
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CIFRAS = AQUI.parent / "articulo" / "tablas" / "cifras.tex"


def macros():
    texto = CIFRAS.read_text(encoding="utf-8")
    salida = {}
    for nombre, valor in re.findall(r"\\newcommand\{\\cifra(\w+)\}\{(.*)\}", texto):
        salida[nombre] = valor.replace("{,}", ",").replace("\\,", "\u202f").replace("--", "–")
    return salida


def rellenar(texto, m):
    faltan = sorted(set(re.findall(r"\{\{(\w+)\}\}", texto)) - set(m))
    if faltan:
        sys.exit(f"faltan cifras: {faltan}")
    return re.sub(r"\{\{(\w+)\}\}", lambda x: m[x.group(1)], texto)


def main():
    m = macros()
    for plantilla, salida in (("guion_sustentacion.md", "guion_sustentacion.md"), ("guia_estudio.html", "guia_estudio.html")):
        texto = (AQUI / "plantillas" / plantilla).read_text(encoding="utf-8")
        (AQUI / salida).write_text(rellenar(texto, m), encoding="utf-8")
        print("escrito", salida)


if __name__ == "__main__":
    main()
