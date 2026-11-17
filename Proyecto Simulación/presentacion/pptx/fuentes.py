"""Prepara las fuentes TrueType para la versión en PowerPoint.

- LM Mono 8 / LM Mono 9: Latin Modern Mono (la del código en Beamer) convertida de CFF a TrueType.
- LM Formulas: las letras en cursiva matemática de Latin Modern Math en las posiciones ASCII (escribir "p"
  da la p de TeX), cifras y signos rectos, espacios matemáticos (fino, medio, grueso) y el cuadrado de las
  viñetas de Beamer (0,8 ex de lado, levantado 0,3 ex respecto a IBM Plex Sans).
"""
import sys
from fontTools.ttLib import TTFont, newTable
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables._g_l_y_f import Glyph
from fontTools import subset

LM = sys.argv[1]   # carpeta .../fonts/opentype/public
OUT = sys.argv[2]


def a_truetype(font):
    """CFF -> glyf (curvas cuadráticas), siguiendo el ejemplo otf2ttf de fontTools."""
    orden = font.getGlyphOrder()
    gs = font.getGlyphSet()
    glyf = {}
    for nombre in orden:
        pen = TTGlyphPen(gs)
        gs[nombre].draw(Cu2QuPen(pen, 1.0, reverse_direction=True))
        glyf[nombre] = pen.glyph()
    font["loca"] = newTable("loca")
    font["glyf"] = t = newTable("glyf")
    t.glyphOrder = orden
    t.glyphs = glyf
    del font["CFF "]
    if "VORG" in font:
        del font["VORG"]
    font["glyf"].compile(font)
    font["maxp"] = newTable("maxp")
    m = font["maxp"]
    m.tableVersion = 0x00010000
    for k in ("maxZones", "maxTwilightPoints", "maxStorage", "maxFunctionDefs", "maxInstructionDefs",
              "maxStackElements", "maxSizeOfInstructions", "maxComponentElements"):
        setattr(m, k, 0)
    m.maxZones = 1
    font["head"].glyphDataFormat = 0
    font["head"].indexToLocFormat = 0
    font["post"].formatType = 2.0
    font["post"].extraNames = []
    font["post"].mapping = {}
    font["post"].glyphOrder = orden
    font.sfntVersion = "\x00\x01\x00\x00"
    m.recalc(font)


def nombrar(font, familia, ps):
    n = font["name"]
    n.names = [r for r in n.names if r.nameID not in (1, 2, 3, 4, 6, 16, 17, 21, 22)]
    for pid, eid, lid in ((3, 1, 0x409), (1, 0, 0)):
        n.setName(familia, 1, pid, eid, lid)
        n.setName("Regular", 2, pid, eid, lid)
        n.setName(familia + " Regular", 3, pid, eid, lid)
        n.setName(familia, 4, pid, eid, lid)
        n.setName(ps, 6, pid, eid, lid)
    font["OS/2"].fsSelection = (font["OS/2"].fsSelection & ~0b1100001) | 0b1000000  # REGULAR
    font["OS/2"].fsType = 0
    font["head"].macStyle = 0


def metricas(font, asc, desc):
    font["hhea"].ascent, font["hhea"].descent, font["hhea"].lineGap = asc, -desc, 0
    o = font["OS/2"]
    o.usWinAscent, o.usWinDescent = asc, desc
    o.sTypoAscender, o.sTypoDescender, o.sTypoLineGap = asc, -desc, 0


def suavizado(font):
    """Tabla gasp como la de IBM Plex: sin ella PowerPoint ajusta a la rejilla y redondea los anchos de glifo."""
    g = newTable("gasp")
    g.version = 1
    g.gaspRange = {8: 10, 16: 7, 65535: 15}
    font["gasp"] = g
    font["head"].flags |= 0b1000


# ---------------------------------------------------------------- LM Mono 8 y 9
for tam in (8, 9):
    f = TTFont(f"{LM}/lm/lmmono{tam}-regular.otf")
    a_truetype(f)
    suavizado(f)
    # marcada como de ancho fijo, PowerPoint redondea su avance en tamaños pequeños; como proporcional, no
    f["post"].isFixedPitch = 0
    f["OS/2"].panose.bProportion = 0
    nombrar(f, f"LM Mono {tam}", f"LMMono{tam}-Regular-PPT")
    f.save(f"{OUT}/LMMono{tam}-Regular.ttf")
    print("LM Mono", tam, "listo")

# ---------------------------------------------------------------- cursiva de Beamer
# Beamer usa IBM Plex Sans Regular inclinada 0,18 (FakeSlant), no la cursiva verdadera. PowerPoint simula la
# cursiva con otro ángulo, así que se genera la versión inclinada. La licencia OFL de Plex reserva el nombre
# "Plex" para la fuente original: la derivada lleva otro nombre y conserva el aviso de copyright y la licencia.
from fontTools.pens.transformPen import TransformPen
PLEX = sys.argv[3] if len(sys.argv) > 3 else None
if PLEX:
    f = TTFont(f"{PLEX}/IBMPlexSans-Regular.ttf")
    gs = f.getGlyphSet()
    glyf = f["glyf"]
    nuevos = {}
    for nombre in f.getGlyphOrder():
        pen = TTGlyphPen(gs)
        gs[nombre].draw(TransformPen(pen, (1, 0, 0.18, 1, 0, 0)))
        nuevos[nombre] = pen.glyph()
    for nombre, g in nuevos.items():
        glyf[nombre] = g
        glyf[nombre].recalcBounds(glyf)
    for t in ("fpgm", "prep", "cvt ", "DSIG"):
        if t in f:
            del f[t]
    f["post"].italicAngle = -10.2
    f["hhea"].caretSlopeRise, f["hhea"].caretSlopeRun = 1000, 180
    nombrar(f, "Sans Oblicua Diapositivas", "SansOblicuaDiapositivas-Regular")
    suavizado(f)
    f["maxp"].recalc(f)
    f.save(f"{OUT}/SansOblicuaDiapositivas-Regular.ttf")
    print("oblicua lista")

# ---------------------------------------------------------------- LM Formulas
cursiva = {}
for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    cursiva[ord(c)] = 0x1D434 + i
for i, c in enumerate("abcdefghijklmnopqrstuvwxyz"):
    cursiva[ord(c)] = 0x2133 + 0 if False else 0x1D44E + i
cursiva[ord("h")] = 0x210E  # la h cursiva vive en otro bloque
rectos = [ord(c) for c in "0123456789()[]=+,.;:/!?'|<>"] + [0x2212, 0xD7, 0x2192, 0x2190, 0x2264, 0x2265,
                                                         0x2260, 0x221E, 0x2208, 0x2211, 0x22C5, 0x00B7, 0x2032]
fuente = TTFont(f"{LM}/lm-math/latinmodern-math.otf")
cmap_orig = fuente.getBestCmap()
opciones = subset.Options()
opciones.layout_features = []
opciones.drop_tables += ["MATH", "GSUB", "GPOS", "GDEF"]
opciones.name_IDs = ["*"]
opciones.notdef_outline = True
sub = subset.Subsetter(opciones)
sub.populate(unicodes=list(cursiva.values()) + rectos)
sub.subset(fuente)
a_truetype(fuente)

orden = fuente.getGlyphOrder()
hmtx = fuente["hmtx"]
glyf = fuente["glyf"]
UPM = 1000


def glifo_vacio(nombre, ancho):
    g = TTGlyphPen(None).glyph()
    glyf.glyphs[nombre] = g
    hmtx.metrics[nombre] = (ancho, 0)
    orden.append(nombre)


# espacios: TeX \, = 3/18 em, \: = 4/18 em, \; = 5/18 em; espacio normal 1/3 em
espacios = {0x20: ("space", 333), 0xA0: ("nbspace", 333), 0x2009: ("thinspace", 167), 0x2006: ("sixperemspace", 167),
            0x202F: ("narrownbspace", 167), 0x205F: ("mediummathspace", 222), 0x2004: ("thickspace", 278),
            0x200A: ("hairspace", 83)}
for cp, (nombre, ancho) in espacios.items():
    glifo_vacio(nombre, ancho)

# cuadrado de viñeta: 0,8 ex de Plex (ex = 0,516 em) => 413 unidades, base a 0,3 ex => 155
pen = TTGlyphPen(None)
lado, base = 413, 155
pen.moveTo((0, base)); pen.lineTo((0, base + lado)); pen.lineTo((lado, base + lado)); pen.lineTo((lado, base)); pen.closePath()
glyf.glyphs["vineta"] = pen.glyph()
glyf.glyphs["vineta"].recalcBounds(glyf)
hmtx.metrics["vineta"] = (lado, 0)
orden.append("vineta")
fuente.setGlyphOrder(orden)
glyf.glyphOrder = orden
fuente["post"].glyphOrder = orden

# cmap: ASCII -> cursiva matemática; el resto, sus propios glifos
mapa = {}
for asc, mat in cursiva.items():
    mapa[asc] = cmap_orig[mat]
for cp in rectos:
    if cp in cmap_orig:
        mapa[cp] = cmap_orig[cp]
mapa[ord("-")] = cmap_orig[0x2212]  # el guion se ve como el menos de TeX
mapa[ord("*")] = cmap_orig[0x22C5]
for cp, (nombre, _) in espacios.items():
    mapa[cp] = nombre
mapa[0x25A0] = "vineta"
mapa[0x25AA] = "vineta"
from fontTools.ttLib.tables._c_m_a_p import cmap_format_4
tabla = newTable("cmap")
tabla.tableVersion = 0
tabla.tables = []
for pid, eid in ((3, 1), (0, 3)):
    st = cmap_format_4(4)
    st.platformID, st.platEncID, st.language = pid, eid, 0
    st.cmap = dict(mapa)
    tabla.tables.append(st)
fuente["cmap"] = tabla
suavizado(fuente)
nombrar(fuente, "LM Formulas", "LMFormulas-Regular")
metricas(fuente, 1025, 275)
o = fuente["OS/2"]
o.usFirstCharIndex, o.usLastCharIndex = min(mapa), min(max(mapa), 0xFFFF)
o.ulUnicodeRange1 = o.ulUnicodeRange1 | 1
o.ulCodePageRange1 = 1
fuente["maxp"].recalc(fuente)
fuente["hhea"].numberOfHMetrics = len(orden)
fuente.save(f"{OUT}/LMFormulas-Regular.ttf")
print("LM Formulas listo:", len(orden), "glifos")
