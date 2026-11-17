"""Genera presentacion.pptx: la presentación de la sustentación en PowerPoint (16:9).

Diseño sencillo: fondo blanco, texto casi negro, un solo acento azul oscuro en los títulos, Calibri
(sin fuentes incrustadas), cajas de texto y viñetas nativas. Las cifras se leen de
articulo/tablas/cifras.tex y las notas del orador de presentacion/presentacion.tex al ejecutar el
script, así que todo se actualiza solo al regenerar.

Uso: python generar_pptx.py <carpeta del proyecto> <salida.pptx>
"""
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from lxml import etree  # noqa: E402
from pptx import Presentation  # noqa: E402
from pptx.dml.color import RGBColor  # noqa: E402
from pptx.enum.shapes import MSO_SHAPE  # noqa: E402
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN  # noqa: E402
from pptx.util import Emu, Inches, Pt  # noqa: E402

PROYECTO = Path(sys.argv[1]).resolve()
SALIDA = Path(sys.argv[2])
TOTAL = 19

NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
A = "{%s}" % NS_A
AZUL = RGBColor(0x1F, 0x4E, 0x79)
TINTA = RGBColor(0x1A, 0x1A, 0x1A)
GRIS = RGBColor(0x6B, 0x6B, 0x6B)
FUENTE = "Calibri"
MONO = "Consolas"
NB = "\u00a0"

FIG = [PROYECTO / "analisis/figuras/diapositivas", PROYECTO / "presentacion/figuras", PROYECTO / "articulo/figuras"]

# ------------------------------------------------------------------ cifras y notas (desde el .tex)


def cifras_tex():
    valores = {}
    texto = (PROYECTO / "articulo/tablas/cifras.tex").read_text(encoding="utf-8")
    for m in re.finditer(r"\\newcommand\{\\(cifra\w+)\}\{(.*)\}\s*$", texto, re.M):
        valores[m.group(1)] = m.group(2).replace("{,}", ",").replace("--", "–")
    return valores


def notas_tex():
    tex = (PROYECTO / "presentacion/presentacion.tex").read_text(encoding="utf-8")
    notas, i = [], 0
    while True:
        i = tex.find("\\note{", i)
        if i < 0:
            break
        j, prof = i + 6, 1
        while prof:
            prof += {"{": 1, "}": -1}.get(tex[j], 0)
            j += 1
        notas.append(tex[i + 6:j - 1])
        i = j
    return notas


def nota_a_runs(s, cifras):
    """Convierte el LaTeX de una nota en [(texto, negrita, cursiva)]."""
    s = re.sub(r"\\(cifra\w+)\\ ", lambda m: cifras[m.group(1)] + " ", s)
    s = re.sub(r"\\(cifra\w+)", lambda m: cifras[m.group(1)], s)
    s = s.replace("\\,", "\u202f").replace("\\%", "%").replace("--", "–").replace("\\ ", " ")
    runs, pos = [], 0
    for m in re.finditer(r"\\textbf\{([^}]*)\}|\\emph\{([^}]*)\}|\$([^$]*)\$", s):
        if m.start() > pos:
            runs.append((s[pos:m.start()], False, False))
        if m.group(1) is not None:
            runs.append((m.group(1), True, False))
        elif m.group(2) is not None:
            runs.append((m.group(2), False, True))
        else:
            runs.append((m.group(3).replace("\\to", "→"), False, True))
        pos = m.end()
    runs.append((s[pos:], False, False))
    return [(t, b, i) for t, b, i in runs if t]


CIF = cifras_tex()


def c(nombre):
    return CIF["cifra" + nombre]


# ------------------------------------------------------------------ texto
# Marcado mínimo dentro de un párrafo: <b>..</b>, <i>..</i>, <sub>..</sub>
TAG = re.compile(r"<(/?)(b|i|sub)>")


def runs_de(texto):
    est = {"b": False, "i": False, "sub": False}
    pos, salida = 0, []
    for m in TAG.finditer(texto):
        if m.start() > pos:
            salida.append((texto[pos:m.start()], dict(est)))
        est[m.group(2)] = m.group(1) == ""
        pos = m.end()
    if pos < len(texto):
        salida.append((texto[pos:], dict(est)))
    return salida


def llenar_parrafo(p, texto, size, color=TINTA, bold=False, font=FUENTE, italic=False):
    for t, est in runs_de(texto):
        r = p.add_run()
        r.text = t
        f = r.font
        f.name = font
        f.size = Pt(size)
        f.bold = bold or est["b"]
        f.italic = italic or est["i"]
        f.color.rgb = color
        rpr = r._r.get_or_add_rPr()
        rpr.set("lang", "es-CO")
        if est["sub"]:
            rpr.set("baseline", "-25000")


def formato_parrafo(p, vineta=None, antes=0, interlineado=1.0, nivel_sangria=0.32, align=None):
    """vineta: None, "punto" o "num"."""
    pPr = p._p.get_or_add_pPr()
    for hijo in list(pPr):
        pPr.remove(hijo)
    p.line_spacing = interlineado
    p.space_before = Pt(antes)
    p.space_after = Pt(0)
    if align:
        p.alignment = align
    if vineta:
        pPr.set("marL", str(int(Inches(nivel_sangria))))
        pPr.set("indent", str(-int(Inches(nivel_sangria))))
        bu_clr = etree.SubElement(pPr, A + "buClr")
        etree.SubElement(bu_clr, A + "srgbClr").set("val", "1A1A1A")
        etree.SubElement(pPr, A + "buFont").set("typeface", FUENTE if vineta == "num" else "Arial")
        if vineta == "num":
            etree.SubElement(pPr, A + "buAutoNum").set("type", "arabicPeriod")
        else:
            etree.SubElement(pPr, A + "buChar").set("char", "•")
    else:
        pPr.set("marL", "0")
        pPr.set("indent", "0")
        etree.SubElement(pPr, A + "buNone")


def caja_texto(slide, x, y, w, h, items, size=20, nombre=None, color=TINTA, anchor=MSO_ANCHOR.TOP, font=FUENTE):
    """items: lista de textos o de dicts {t, vineta, b, size, color, antes, align, italic}."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if nombre:
        tb.name = nombre
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    primero = True
    for it in items:
        if isinstance(it, str):
            it = {"t": it}
        p = tf.paragraphs[0] if primero else tf.add_paragraph()
        formato_parrafo(p, it.get("vineta"), 0 if primero else it.get("antes", 8), it.get("ls", 1.0),
                        align=it.get("align"))
        llenar_parrafo(p, it["t"], it.get("size", size), it.get("color", color), it.get("b", False),
                       it.get("font", font), it.get("italic", False))
        primero = False
    return tb


def vinetas(textos, **kw):
    return [{"t": t, "vineta": "punto", "antes": 0 if i == 0 else 10} for i, t in enumerate(textos)]


def numeradas(textos):
    return [{"t": t, "vineta": "num", "antes": 0 if i == 0 else 10} for i, t in enumerate(textos)]


def imagen(slide, nombre, x, y, w=None, h=None, alt=""):
    ruta = next(d / nombre for d in FIG if (d / nombre).exists())
    kw = {}
    if w:
        kw["width"] = Inches(w)
    if h:
        kw["height"] = Inches(h)
    pic = slide.shapes.add_picture(str(ruta), Inches(x), Inches(y), **kw)
    pic.name = nombre
    pic._element.nvPicPr.cNvPr.set("descr", alt)
    return pic


def pie_fuente(slide, texto):
    caja_texto(slide, 0.6, 6.5, 12.1, 0.3, [{"t": texto, "size": 11, "color": GRIS}], nombre="Fuente")


# ------------------------------------------------------------------ estructura de las diapositivas
prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
LAYOUT = prs.slide_layouts[5]  # "Solo el título"


def nueva(titulo, n, pie=True):
    s = prs.slides.add_slide(LAYOUT)
    t = s.shapes.title
    t.left, t.top, t.width, t.height = Inches(0.6), Inches(0.4), Inches(12.1), Inches(0.8)
    tf = t.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    llenar_parrafo(p, titulo, 28, AZUL, bold=True)
    if pie:
        caja_texto(s, 0.6, 6.95, 8, 0.3, [{"t": "Simulación Computacional, Universidad de los Llanos", "size": 10,
                                          "color": GRIS}], nombre="Pie")
        caja_texto(s, 10.7, 6.95, 2.0, 0.3, [{"t": f"{n} / {TOTAL}", "size": 10, "color": GRIS,
                                             "align": PP_ALIGN.RIGHT}], nombre="Número de diapositiva")
    return s


def formula_png(destino):
    fig = plt.figure(figsize=(6.4, 0.9), dpi=300)
    fig.patch.set_alpha(0)
    fig.text(0.5, 0.5, r"$P_i = 1 - (1 - p\,a_t)\,(1 - q\,f_i)$", ha="center", va="center", fontsize=34,
             color="#1A1A1A", math_fontfamily="stix")
    fig.savefig(destino, transparent=True, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)


# ------------------------------------------------------------------ 1. portada
s = prs.slides.add_slide(LAYOUT)
t = s.shapes.title
t.left, t.top, t.width, t.height = Inches(0.6), Inches(1.9), Inches(7.4), Inches(1.7)
t.text_frame.word_wrap = True
t.text_frame.vertical_anchor = MSO_ANCHOR.TOP
t.text_frame.margin_left = t.text_frame.margin_right = t.text_frame.margin_top = t.text_frame.margin_bottom = 0
p = t.text_frame.paragraphs[0]
p.alignment = PP_ALIGN.LEFT
llenar_parrafo(p, "Publicidad y redes sociales en la difusión de innovaciones", 36, AZUL, bold=True)
caja_texto(s, 0.6, 1.35, 7.4, 0.4, [{"t": "Simulación Computacional, proyecto 14", "size": 18, "color": GRIS}], nombre="Curso")
caja_texto(s, 0.6, 3.75, 7.4, 0.9, [{"t": "Un modelo basado en agentes de la PS5 y del lanzamiento de GTA" + NB + "6", "size": 22,
                                      "color": TINTA}], nombre="Subtítulo")
caja_texto(s, 0.6, 4.85, 7.4, 1.0, ["Jesus Gregorio Delgado", {"t": "David Andres Monroy Aguiar", "antes": 2},
                                    {"t": "Duvan Felipe Baquero Cerquera", "antes": 2}], size=18, nombre="Autores")
caja_texto(s, 0.6, 6.0, 7.4, 0.8, [{"t": "Ingeniería de Sistemas, Universidad de los Llanos", "size": 16, "color": GRIS},
                                   {"t": "17 de noviembre de 2026", "size": 16, "color": GRIS, "antes": 2}],
           nombre="Programa y fecha")
imagen(s, "portada_red.png", 8.5, 1.35, w=4.4, alt="Red social de agentes: nodos conectados, unos que ya adoptaron el producto y otros que no")

# ------------------------------------------------------------------ 2. motivación
s = nueva("Motivación", 2)
caja_texto(s, 0.6, 1.5, 12.1, 4.8, vinetas([
    f"La PS5 lleva {c('PsUnidadesFin')} millones de unidades vendidas entre noviembre de 2020 y septiembre de 2026.",
    "GTA 6 sale el 19 de noviembre de 2026, solo para las consolas de esta generación. Su primer tráiler tuvo 90 millones de vistas en 24 horas.",
    "Según Bass, un producto se difunde por publicidad (influencia externa) y por imitación (voz a voz).",
    "La PS5 creció sobre todo por imitación. Un gran estreno vende casi todo al salir.",
]), size=22, nombre="Motivación")
pie_fuente(s, "Sony Interactive Entertainment, Business Data & Sales; Guinness World Records (2023).")

# ------------------------------------------------------------------ 3. problema
s = nueva("Problema", 3)
imagen(s, "mezcla_vs_red.png", 0.6, 1.8, w=6.9,
       alt="Dos redes: a la izquierda todos influyen sobre todos (modelo de Bass); a la derecha solo los contactos (red social)")
caja_texto(s, 7.9, 1.8, 4.8, 4.6, [{"t": "Bass: todos influyen sobre todos. En la realidad, solo los contactos.", "antes": 0}] +
           [dict(v, antes=14 if i == 0 else 10) for i, v in enumerate(vinetas([
               "¿Qué pasa sin publicidad?", "¿Importa la densidad o la forma de la red?",
               "¿Cuánto se pierde con una campaña corta?", "¿Responden igual una consola y un videojuego?"]))],
           size=20, nombre="Preguntas")

# ------------------------------------------------------------------ 4. justificación
s = nueva("Justificación", 4)
caja_texto(s, 0.6, 1.5, 12.1, 4.8, vinetas([
    "Cada persona es un agente con sus contactos y una regla de decisión.",
    "Se pueden probar escenarios que no se observan en la realidad: lanzar sin publicidad, cambiar la red o acortar la campaña.",
    "La PS5 se calibra y se evalúa con ventas oficiales. GTA 6 todavía no tiene ventas y se parametriza por analogía con GTA V.",
    "NetLogo es libre, guarda el modelo completo en un archivo y BehaviorSpace repite cada escenario 30 veces.",
]), size=22, nombre="Justificación")

# ------------------------------------------------------------------ 5. objetivos
s = nueva("Objetivos", 5)
caja_texto(s, 0.6, 1.5, 12.1, 5.0, [
    {"t": "Objetivo general", "b": True, "size": 22},
    {"t": "Medir el efecto de la publicidad y de la red sobre la adopción final, en la PS5 y en GTA" + NB + "6.", "antes": 6},
    {"t": "Objetivos específicos", "b": True, "size": 22, "antes": 26},
] + [dict(v, antes=6 if i == 0 else 8) for i, v in enumerate(numeradas([
    "Implementar en NetLogo el modelo de Bass en red, con tres tipos de red.",
    "Calibrar con la PS5 (entrenamiento, validación, prueba) y parametrizar GTA" + NB + "6 por analogía.",
    "Evaluar con 30 réplicas publicidad, densidad, topología y duración.",
    "Verificar con una reimplementación en Python."]))], size=20, nombre="Objetivos")

# ------------------------------------------------------------------ 6. regla de adopción
s = nueva("Metodología: regla de adopción", 6)
tmp = Path(tempfile.mkdtemp())
formula_png(tmp / "formula.png")
pic = s.shapes.add_picture(str(tmp / "formula.png"), 0, Inches(1.45), height=Inches(0.95))
pic.left = int((prs.slide_width - pic.width) / 2)
pic.name = "Fórmula"
pic._element.nvPicPr.cNvPr.set("descr", "P sub i igual a 1 menos (1 menos p por a sub t) por (1 menos q por f sub i)")
caja_texto(s, 0.6, 2.9, 6.0, 3.6, [
    {"t": "publicidad", "b": True, "size": 22},
    {"t": "<i>p</i>: probabilidad mensual de que la campaña convenza; <i>a</i><sub>t</sub> = 1 mientras está activa.", "antes": 4},
    {"t": "imitación", "b": True, "size": 22, "antes": 24},
    {"t": "<i>q</i> por <i>f</i><sub>i</sub>, la fracción de vecinos que ya adoptó.", "antes": 4},
], size=20, nombre="Términos de la fórmula")
caja_texto(s, 7.2, 2.9, 5.5, 3.6, vinetas([
    "Adoptar es irreversible; todos deciden a la vez.",
    "Red completa = Bass: la diferencia es el efecto de la red.",
    "Redes aleatoria, mundo pequeño y libre de escala."]), size=20, nombre="Supuestos")

# ------------------------------------------------------------------ 7. esquema
s = nueva("Metodología: esquema del sistema", 7)
img = imagen(s, "esquema_sistema.png", 0.6, 1.4, w=12.1,
             alt="Esquema: datos de Sony y Take-Two, calibración, modelo en NetLogo, escenarios en BehaviorSpace y análisis en Python; "
                 "dentro del modelo, la campaña y la red social alimentan la regla de adopción, que decide el estado de cada agente")
if img.height > Inches(5.3):  # no pasar del pie
    esc = Inches(5.3) / img.height
    img.height, img.width = int(img.height * esc), int(img.width * esc)
    img.left = int((prs.slide_width - img.width) / 2)

# ------------------------------------------------------------------ 8. implementación
s = nueva("Metodología: implementación en NetLogo", 8)
imagen(s, "netlogo_ps5.png", 0.6, 1.6, w=6.0, alt="Interfaz del modelo en NetLogo: caso PS5, red libre de escala, mes 30")
caja_texto(s, 0.6, 1.6 + 6.0 * 446 / 650 + 0.1, 6.0, 0.5, [{"t": "Interfaz del modelo (configuración de demostración: caso PS5, red libre de escala, mes 30).",
                                                         "size": 11, "color": GRIS}], nombre="Pie de la interfaz")
codigo = """to decidir
  let p p-efectivo
  ask turtles with
      [susceptible? and not adoptante?] [
    let vecinos link-neighbors
    let f 0
    if any? vecinos [
      set f count vecinos with [adoptante?]
        / count vecinos ]
    let prob 1 - (1 - p) * (1 - q-imitacion * f)
    set decide-adoptar? random-float 1 < prob ]
end"""
caja_texto(s, 7.0, 1.6, 5.8, 3.6, [{"t": ln if ln else " ", "antes": 0, "font": MONO, "size": 14} for ln in codigo.split("\n")],
           nombre="Código NetLogo")
caja_texto(s, 7.0, 5.35, 5.8, 1.3, [{"t": "<i>actualizar</i> aplica todas las decisiones a la vez. La extensión nw genera las redes; "
                                          "el selector de caso carga PS5, GTA" + NB + "6 o libre.", "size": 16, "color": GRIS}],
           nombre="Nota del código")

# ------------------------------------------------------------------ 9. datos PS5
s = nueva("Conjunto de datos: ventas de la PS5", 9)
imagen(s, "serie_ps5.png", 0.6, 1.5, w=7.4, alt="Serie trimestral de unidades acumuladas de PS5 vendidas, de diciembre de 2020 a septiembre de 2026")
caja_texto(s, 8.4, 1.5, 4.3, 4.8, vinetas([
    f"{c('Trimestres')} trimestres de ventas oficiales de Sony.",
    f"{c('PsUnidadesIni')} a {c('PsUnidadesFin')} millones acumulados, dic.{NB}2020 a sep.{NB}2026.",
    f"Adopción = acumulado / base de PS4 ({c('Universo')}{NB}M), fijada antes de ver la prueba.",
    f"Simulación: {c('Corridas')} corridas de 1000 agentes."]), size=18, nombre="Datos de la PS5")
pie_fuente(s, "Sony Interactive Entertainment, Business Data & Sales (unidades vendidas a tiendas).")

# ------------------------------------------------------------------ 10. analogía GTA V
s = nueva("Conjunto de datos: GTA V como análogo de GTA 6", 10)
imagen(s, "analogia_gtav.png", 0.6, 1.5, w=6.2, alt="Ventas de GTA V en sus primeras semanas y ajuste del modelo de Bass usado como análogo de GTA 6")
caja_texto(s, 7.2, 1.5, 5.5, 4.8, vinetas([
    "GTA" + NB + "6 aún no tiene ventas: se parametriza con GTA" + NB + "V.",
    f"GTA{NB}V: {c('GtavSeisSemanas')}{NB}M en seis semanas y {c('GtavMeseta')}{NB}M al año, sobre {c('GtaBase')}{NB}M de consolas.",
    f"Mismo ajuste de Bass: publicidad de {c('GtaP')} al mes, unas {c('GtaRazonPQ')} veces la imitación.",
    f"GTA{NB}6 entre dueños de PS5: potencial {c('GtaM')}{NB}%, {c('GtaIniciales')}{NB}% el primer día, {c('GtaHorizonte')} meses."]),
           size=18, nombre="Análogo GTA V")
pie_fuente(s, "Take-Two Interactive, resultados trimestrales 2013 a 2014; primer día: Guinness World Records (2013).")

# ------------------------------------------------------------------ 11. diseño experimental
s = nueva("Diseño experimental", 11)
x0, y0, h0 = 0.6, 1.5, 0.95
anchos = [5.0, 3.0, 4.1]
colores = [RGBColor(0x1F, 0x4E, 0x79), RGBColor(0x5B, 0x84, 0xAD), RGBColor(0xA9, 0xC1, 0xD9)]
textos = [f"Entrenamiento: dic.{NB}2020 a dic.{NB}2023, {c('ObsEnt')} trimestres",
          f"Validación: 2024, {c('ObsVal')} trimestres", f"Prueba: 2025 a 2026, {c('ObsPru')} trimestres"]
subt = ["ajusta p y q", "elige m y la red", "solo evalúa"]
x = x0
for w, col, tx, sb in zip(anchos, colores, textos, subt):
    r = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y0), Inches(w - 0.06), Inches(h0))
    r.name = tx.split(":")[0]
    r.fill.solid()
    r.fill.fore_color.rgb = col
    r.line.fill.background()
    r.shadow.inherit = False
    tf = r.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Inches(0.1)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    llenar_parrafo(p, tx, 16, RGBColor(0xFF, 0xFF, 0xFF) if col != colores[2] else TINTA)
    caja_texto(s, x, y0 + h0 + 0.05, w - 0.06, 0.3, [{"t": sb, "size": 14, "color": GRIS, "align": PP_ALIGN.CENTER}],
               nombre="Función de " + tx.split(":")[0].lower())
    x += w

filas = [("", "Factores (E1 a E3 para ambos casos: PS5 y GTA" + NB + "6)", "Corridas"),
         ("E1", f"publicidad {{sin, con}} × densidad k = 2, 4, 6, 8, 12, 16", "720"),
         ("E2", "publicidad × topología {aleatoria, mundo pequeño, libre de escala}", "360"),
         ("E3", "duración de la campaña {0, 1, 3, 6, 12, 24 meses, permanente}", "420"),
         ("E4", "calibración PS5: 3 topologías × k = 4, 8, 16", "270")]
gf = s.shapes.add_table(5, 3, Inches(0.6), Inches(3.55), Inches(12.1), Inches(2.7))
gf.name = "Tabla de experimentos"
tabla = gf.table
tpr = tabla._tbl.tblPr
tpr.set("firstRow", "0")
tpr.set("bandRow", "0")
sid = tpr.find(A + "tableStyleId")
if sid is None:
    sid = etree.SubElement(tpr, A + "tableStyleId")
sid.text = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"  # sin estilo y sin cuadrícula
for j, w in enumerate([0.9, 9.5, 1.7]):
    tabla.columns[j].width = Inches(w)


def borde(celda, lado, grosor_pt):
    tcPr = celda._tc.get_or_add_tcPr()
    ln = etree.SubElement(tcPr, A + lado, w=str(int(grosor_pt * 12700)), cap="flat", cmpd="sng", algn="ctr")
    sf = etree.SubElement(ln, A + "solidFill")
    etree.SubElement(sf, A + "srgbClr").set("val", "1A1A1A")
    etree.SubElement(ln, A + "prstDash").set("val", "solid")


for i, fila in enumerate(filas):
    tabla.rows[i].height = Inches(0.54)
    for j, tx in enumerate(fila):
        cel = tabla.cell(i, j)
        cel.margin_left = cel.margin_right = Inches(0.05)
        cel.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = cel.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.RIGHT if j == 2 else PP_ALIGN.LEFT
        llenar_parrafo(p, tx, 16, TINTA, bold=(i == 0 or j == 0))
        if i == 0:
            borde(cel, "lnT", 1.5)
            borde(cel, "lnB", 0.75)
        if i == 4:
            borde(cel, "lnB", 1.5)
        # los bordes deben ir antes del relleno en tcPr
        tcPr = cel._tc.get_or_add_tcPr()
        for nf in tcPr.findall(A + "noFill"):
            tcPr.remove(nf)
        etree.SubElement(tcPr, A + "noFill")

# ------------------------------------------------------------------ 12. medidas
s = nueva("Medidas de desempeño", 12)
caja_texto(s, 0.6, 1.5, 6.0, 4.8, [{"t": "Escenarios", "b": True, "size": 22}] + [dict(v, antes=12 if i == 0 else 10) for i, v in enumerate(vinetas([
    f"<b>Adopción final</b>: % de la población que adoptó al final del período (PS5: {c('HorizontePs')} meses; GTA{NB}6: {c('HorizonteGta')}).",
    f"Mes del 50{NB}% y mes del pico de compras.",
    f"Media e IC del 95{NB}% con 30 réplicas."]))], size=19, nombre="Escenarios")
caja_texto(s, 7.0, 1.5, 5.7, 4.8, [{"t": "Ajuste a la serie real", "b": True, "size": 22}] + [dict(v, antes=12 if i == 0 else 10) for i, v in enumerate(vinetas([
    "RMSE: raíz del error cuadrático medio, en puntos porcentuales.",
    "MAPE: error porcentual absoluto medio.",
    "Por partición: entrenamiento, validación y prueba."]))], size=19, nombre="Ajuste")

# ------------------------------------------------------------------ 13. calibración
s = nueva("Resultados: calibración y prueba con la PS5", 13)
imagen(s, "fig_calibracion.png", 0.6, 1.5, w=7.6, alt="Serie real de la PS5 frente al modelo de agentes y al modelo de Bass, con las particiones de entrenamiento, validación y prueba")
caja_texto(s, 8.6, 1.6, 4.1, 4.8, vinetas([
    f"Error en prueba del modelo de agentes: {c('AbmRmsePru')} puntos porcentuales (Bass: {c('BassRmsePru')}).",
    f"Bass anual: <i>p</i> = {c('BassP')} y <i>q</i> = {c('BassQ')}. La imitación pesa {c('BassRazonQP')} veces más que la publicidad.",
    f"Red elegida en validación: {c('AbmSelRedNombre')} con <i>k</i> = {c('AbmSelK')}."]), size=18, nombre="Resultados de calibración")

# ------------------------------------------------------------------ 14. publicidad
s = nueva("Resultados: adopción con y sin publicidad", 14)
caja_texto(s, 0.6, 1.4, 12.1, 0.5, [{"t": "Sin publicidad, ninguno de los dos llega lejos.", "size": 20}], nombre="Mensaje")
imagen(s, "publicidad_casos.png", 1.1, 2.05, w=11.1,
       alt="Adopción en el tiempo de la PS5 y de GTA 6, con y sin campaña de publicidad")
pie_fuente(s, "Red de mundo pequeño con k = 2 (discontinua) y 16 (continua).")

# ------------------------------------------------------------------ 15. densidad y topología
s = nueva("Resultados: densidad de la red", 15)
imagen(s, "densidad.png", 0.6, 1.6, w=8.3, alt="Adopción final según la densidad de la red k, con y sin campaña, para la PS5 y GTA 6")
caja_texto(s, 9.3, 1.7, 3.4, 4.8, vinetas([
    f"Sin campaña, pasar de <i>k</i> = 2 a <i>k</i> = 16 multiplica la adopción de la PS5 por {c('PsSinRazon')}.",
    f"Con campaña, la misma diferencia solo la multiplica por {c('PsConRazon')}.",
    "Sin campaña, la red de mundo pequeño es la topología más lenta."]), size=18, nombre="Resultados de densidad")

# ------------------------------------------------------------------ 16. duración
s = nueva("Resultados: duración de la campaña", 16)
imagen(s, "fraccion_duracion.png", 0.6, 1.5, w=7.4, alt="Fracción del efecto de una campaña permanente que se logra según la duración de la campaña, en GTA 6 y en la PS5")
caja_texto(s, 8.4, 1.7, 4.3, 4.8, vinetas([
    f"GTA{NB}6: un mes de campaña logra el {c('FraccionGtaDUno')}{NB}% del efecto de una campaña permanente.",
    f"PS5: un año logra el {c('FraccionPsDDoce')}{NB}% y dos años el {c('FraccionPsDVeinticuatro')}{NB}%."]), size=20,
           nombre="Resultados de duración")

# ------------------------------------------------------------------ 17. demostración
s = nueva("Demostración en NetLogo", 17)
imagen(s, "netlogo_gta6.png", 0.6, 1.6, w=4.6, alt="Interfaz de NetLogo con el caso GTA 6: las compras se concentran en el primer mes")
caja_texto(s, 0.6, 1.6 + 4.6 * 360 / 385 + 0.1, 4.6, 0.4, [{"t": "Caso GTA" + NB + "6: compras concentradas en el primer mes.", "size": 11,
                                                          "color": GRIS}], nombre="Pie de la captura")
caja_texto(s, 5.8, 1.6, 6.9, 3.6, numeradas([
    "Caso <b>GTA" + NB + "6</b> → configurar → simular: el pico llega en el primer mes.",
    f"Campaña apagada: la adopción apenas pasa del {c('GtaIniciales')}{NB}%.",
    "Caso <b>PS5</b>: curva en S frente a la de Bass."]), size=20, nombre="Pasos de la demostración")
caja_texto(s, 5.8, 5.4, 6.9, 0.9, [{"t": "Si sobra tiempo: PS5 sin campaña y <i>k</i> de 16 a 2; Herramientas → BehaviorSpace.", "size": 16,
                                    "color": GRIS}], nombre="Si sobra tiempo")

# ------------------------------------------------------------------ 18. conclusiones
s = nueva("Conclusiones", 18)
caja_texto(s, 0.6, 1.5, 12.1, 4.0, numeradas([
    f"PS5: sin campaña, a lo sumo {c('PsSinMaxGlobal')}{NB}%; con campaña, al menos {c('PsConMin')}{NB}%.",
    f"GTA{NB}6: un mes de campaña logra el {c('FraccionGtaDUno')}{NB}% del efecto.",
    "La red pesa sobre todo cuando no hay publicidad.",
    f"Error en prueba: {c('AbmRmsePru')} pp; la reimplementación en Python coincide."]), size=22, nombre="Conclusiones")
caja_texto(s, 0.6, 5.6, 12.1, 0.8, [{"t": "Limitaciones: coeficientes iguales para todos, red fija, unidades vendidas a tiendas y parámetros de GTA" + NB +
                                        "6 hipotéticos.", "size": 16, "color": GRIS}], nombre="Limitaciones")

# ------------------------------------------------------------------ 19. referencias
s = nueva("Referencias", 19)
refs = ["Bass, F. M. (1969). A new product growth model for consumer durables. <i>Management Science</i>, 15(5), 215–227.",
        "Goldenberg, J., Libai, B. y Muller, E. (2001). Talk of the network. <i>Marketing Letters</i>, 12(3), 211–223.",
        "Rogers, E. M. (2003). <i>Diffusion of Innovations</i> (5.ª ed.). Free Press.",
        "Thomas, R. J. (1985). Estimating market growth for new products: an analogical diffusion model approach. <i>Journal of Product Innovation Management</i>, 2(1), 45–55.",
        "Watts, D. J. y Strogatz, S. H. (1998). Collective dynamics of ‘small-world’ networks. <i>Nature</i>, 393, 440–442.",
        "Wilensky, U. (1999). NetLogo. Northwestern University.",
        "Sony Interactive Entertainment (2026). Business Data & Sales.",
        "Take-Two Interactive (2013–2014). Resultados trimestrales, años fiscales 2014 y 2015.",
        "Guinness World Records (2013, 2023). Récords de ventas de GTA" + NB + "V y de vistas del tráiler de GTA" + NB + "6."]
caja_texto(s, 0.6, 1.45, 12.1, 5.3, [{"t": r, "antes": 0 if i == 0 else 9} for i, r in enumerate(refs)], size=16, nombre="Referencias")

# ------------------------------------------------------------------ notas del orador y propiedades
assert len(prs.slides) == TOTAL, len(prs.slides)
notas = notas_tex()
assert len(notas) == TOTAL, f"{len(notas)} notas en presentacion.tex"
for slide, nt in zip(prs.slides, notas):
    p = slide.notes_slide.notes_text_frame.paragraphs[0]
    for t, b, i in nota_a_runs(nt, CIF):
        r = p.add_run()
        r.text = t
        r.font.name, r.font.size, r.font.bold, r.font.italic = FUENTE, Pt(12), b, i

cp = prs.core_properties
cp.title = "Publicidad y redes sociales en la difusión de innovaciones"
cp.subject = "Proyecto 14, Simulación Computacional, PS5 y GTA 6"
cp.author = "Jesus Gregorio Delgado, David Andres Monroy Aguiar, Duvan Felipe Baquero Cerquera"
cp.last_modified_by = "Duvan Felipe Baquero Cerquera"
cp.keywords = "difusión de innovaciones; modelo de Bass; NetLogo; PS5; GTA 6"
cp.comments = ""
cp.created = cp.modified = datetime.now()
cp.revision = 1
prs.save(SALIDA)
print("guardado", SALIDA, len(prs.slides), "diapositivas")
