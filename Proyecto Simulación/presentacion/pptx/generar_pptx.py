"""Genera presentacion.pptx: la misma presentación de Beamer, elemento por elemento, en PowerPoint.

Las posiciones salen de presentacion.pdf (en mm de la página de Beamer, 160 x 90) y se escalan a una
diapositiva de 16:9 (338,67 x 190,5 mm). El texto es editable: cajas de texto, viñetas y numeración de
PowerPoint, tablas nativas, formas y conectores para el esquema. Las figuras son las mismas PNG.

Fuentes: IBM Plex Sans (Regular y Medium), LM Mono 8/9 (código) y LM Formulas (letras de las fórmulas
en la cursiva matemática de TeX y el cuadrado de las viñetas).

Uso: python generar_pptx.py <carpeta del proyecto> <salida.pptx>
"""
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from lxml import etree
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.opc.constants import RELATIONSHIP_TYPE as RT

sys.path.insert(0, str(Path(__file__).parent))
from metricas import Fuente  # noqa: E402

PROYECTO = Path(sys.argv[1])
SALIDA = Path(sys.argv[2])

# ------------------------------------------------------------------ escala
EMU_MM = 76200          # 1 mm de Beamer = 76200 EMU (160 mm -> 12 192 000 EMU)
K = 12192000 / 12700 / (160 / 25.4 * 72)  # factor de escala de los puntos tipográficos (2,1167)
BASE = 0.75             # PowerPoint: renglón de alto H con la línea base al 75 % (medido)


def E(mm):
    return int(round(mm * EMU_MM))


def hp(pt):
    """Tamaño en pt de Beamer -> centésimas de pt en PowerPoint."""
    return int(round(pt * K * 100))


def mm_a_pt(mm):
    return mm / 25.4 * 72


# ------------------------------------------------------------------ paleta y fuentes
PAPEL, TINTA, SECUNDARIO, TENUE = "FBFAF6", "1F2933", "5E6670", "8C8A85"
BORDE, CLARO, AZUL, AZULCLARO = "B9B4AA", "F1EEE7", "1E66A8", "8DB3D6"
AZULFONDO, TERRACOTA, TERRACOTAFONDO, BLANCO = "E4EDF6", "C2502A", "F7E6DE", "FFFFFF"
COLORES = {"t": TERRACOTA, "a": AZUL, "s": SECUNDARIO, "k": TINTA, "w": BLANCO, "e": TENUE}

REG, MED, MONO8, MONO9, MAT = "IBM Plex Sans", "IBM Plex Sans Medm", "LM Mono 8", "LM Mono 9", "LM Formulas"
OBL = "Sans Oblicua Diapositivas"   # Plex Regular inclinada 0,18, como la cursiva de Beamer (FakeSlant)

# tamaños de Beamer (pt) tal como salen en el PDF
T_SCRIPT, T_FOOT, T_SMALL, T_NORMAL = 7.97, 8.966, 9.963, 10.909
T_LARGE, T_PORTADA, T_CIFRA, T_TINY, T_CODIGO = 14.346, 20.921, 23.91, 5.978, 7.173
SUB = {14.346: 9.963, 9.963: 6.974, 8.966: 5.978, 7.97: 5.978}  # tamaño de los subíndices de TeX

# interlineados (mm de Beamer) medidos en el PDF
L_NORMAL, L_SMALL, L_FOOT, L_SCRIPT, L_TITULO = 4.78, 4.217, 3.866, 3.34, 6.35

# espacios: ¦ = \, de TeX (1/6 em). En las fórmulas: \u2009 fino, \u205f medio, \u2004 grueso
FINO = "\u2006"
NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"')


# ------------------------------------------------------------------ texto con marcas
# ⟨códigos|texto⟩  t a s k w e = color; M = Plex Medium; R = Plex Regular; m = fórmula; _ = subíndice;
# c = código (LM Mono 9); i = cursiva; b = negrita.  \n = salto de línea dentro del párrafo.
MARCA = re.compile(r"⟨([^|⟩]*)\|([^⟩]*)⟩")
MEDIDAS = {}  # anchos y kerning de cada fuente (se llena en construir)


def trozos(texto, base):
    salida, pos = [], 0
    for m in MARCA.finditer(texto):
        if m.start() > pos:
            salida.append((texto[pos:m.start()], dict(base)))
        est = dict(base)
        codigos = m.group(1)
        if "@" in codigos:
            codigos, ancla = codigos.split("@")
            est["ancla"] = float(ancla)
        for c in codigos:
            if c in COLORES:
                est["color"] = COLORES[c]
            elif c == "M":
                est["font"] = MED
            elif c == "R":
                est["font"] = REG
            elif c == "m":
                est["font"] = MAT
            elif c == "_":
                est["font"] = MAT
                est["sub"] = True
            elif c == "c":
                est["font"] = MONO9
            elif c == "i":
                est["font"] = OBL
            elif c == "b":
                est["bold"] = True
        salida.append((m.group(2), est))
        pos = m.end()
    if pos < len(texto):
        salida.append((texto[pos:], dict(base)))
    return [(t.replace("¦", FINO), e) for t, e in salida]


def tam_real(est):
    return SUB.get(round(est["size"], 3), est["size"] * 0.7) if est.get("sub") else est["size"]


def rpr(est, etiqueta="a:rPr", spc=None):
    tam = est["size"]
    attrs = [f'lang="{est.get("lang", "es-CO")}"']
    if est.get("sub"):
        # PowerPoint dibuja el subíndice a 2/3 del tamaño escrito (y escala igual su spc); la bajada es un
        # porcentaje del tamaño escrito. TeX baja el subíndice ~0,15 em del texto base.
        caida = est.get("caida", 0.15) * tam
        tam = SUB.get(round(tam, 3), tam * 0.7) * 1.5
        attrs.append(f'baseline="{-int(round(caida / tam * 100000))}"')
        if spc:
            spc = int(round(spc * 1.5))
    attrs.insert(0, f'sz="{hp(tam)}"')
    if est.get("italic"):
        attrs.append('i="1"')
    if est.get("bold"):
        attrs.append('b="1"')
    if spc or (spc is not None and est.get("spc_explicito")):
        attrs.append(f'spc="{spc}"')
    attrs.append('kern="0"')
    attrs.append('dirty="0"')
    f = est["font"]
    return (f'<{etiqueta} {" ".join(attrs)}><a:solidFill><a:srgbClr val="{est["color"]}"/></a:solidFill>'
            f'<a:latin typeface="{f}"/><a:cs typeface="{f}"/></{etiqueta}>')


def runs_xml(texto, base, x0=None):
    """Texto -> runs de DrawingML. Reproduce el espaciado de XeTeX: kerning de Plex, espaciado entre letras
    (est["ls"], en em), ancho fijo de los espacios (est["espacio"], en mm) y anclas ⟨@x|...⟩ que llevan el
    trozo a la x del PDF. Todo se escribe como espaciado de carácter (spc) en el glifo anterior."""
    items = []
    for t, est in trozos(texto, base):
        for j, c in enumerate(t):
            items.append({"c": c, "est": est, "extra": 0.0, "nuevo": j == 0})
    for i, it in enumerate(items):
        if it["c"] == "\n":
            continue
        est = it["est"]
        fuente = MEDIDAS[est["font"]]
        em = tam_real(est) * 25.4 / 72
        sig = items[i + 1] if i + 1 < len(items) else None
        if sig and not sig["nuevo"] and sig["c"] != "\n":
            if est["font"] in (REG, MED, OBL):
                it["extra"] += fuente.kern(it["c"], sig["c"]) / 1000 * em
            if est.get("ls") and sig["c"] != " ":
                it["extra"] += est["ls"] * em
        if it["c"] == " " and est.get("espacio"):
            it["extra"] += est["espacio"] - fuente.avance(" ") / 1000 * em
        if est.get("track"):
            it["extra"] += est["track"] * em
    if x0 is not None:
        x, prev = x0, None
        for it in items:
            if it["c"] == "\n":
                x, prev = x0, None
                continue
            est = it["est"]
            if it["nuevo"] and "ancla" in est:
                if prev is not None:
                    prev["extra"] += est["ancla"] - x
                x = est["ancla"]
            x += MEDIDAS[est["font"]].avance(it["c"]) / 1000 * tam_real(est) * 25.4 / 72 + it["extra"]
            prev = it
    partes, actual = [], None

    def cerrar():
        if actual:
            partes.append(f'<a:r>{rpr(actual[1], spc=actual[2])}<a:t>{escape(actual[0])}</a:t></a:r>')

    for it in items:
        if it["c"] == "\n":
            cerrar()
            actual = None
            partes.append(f'<a:br>{rpr(it["est"])}</a:br>')
            continue
        spc = int(round(mm_a_pt(it["extra"]) * K * 100))
        if actual and actual[1] is it["est"] and actual[2] == spc:
            actual[0] += it["c"]
        else:
            cerrar()
            actual = [it["c"], it["est"], spc]
    cerrar()
    return "".join(partes)


def parrafo_xml(texto, base, L, antes_pt=0, algn="l", marL=0.0, indent=0.0, vineta=None, x0=None):
    """L: interlineado en mm de Beamer (o el xml de a:lnSpc ya calculado); antes_pt: puntos enteros."""
    ppr = [f'marL="{E(marL)}"', f'indent="{E(indent)}"', f'algn="{algn}"']
    hijos = L if isinstance(L, str) else alto_linea(L, base["size"])[0]
    hijos += f'<a:spcBef><a:spcPts val="{int(antes_pt) * 100}"/></a:spcBef>'
    hijos += '<a:spcAft><a:spcPts val="0"/></a:spcAft>'
    if vineta == "cuadro":
        hijos += (f'<a:buClr><a:srgbClr val="{TERRACOTA}"/></a:buClr><a:buSzPct val="100000"/>'
                  f'<a:buFont typeface="{MAT}"/><a:buChar char="&#9632;"/>')
    elif isinstance(vineta, int):
        hijos += (f'<a:buClr><a:srgbClr val="{TERRACOTA}"/></a:buClr><a:buSzPct val="100000"/>'
                  f'<a:buFont typeface="{MED}"/><a:buAutoNum type="arabicPeriod" startAt="{vineta}"/>')
    else:
        hijos += '<a:buNone/>'
    fin = rpr(dict(base), "a:endParaRPr")
    return f'<a:p><a:pPr {" ".join(ppr)}>{hijos}</a:pPr>{runs_xml(texto, base, x0)}{fin}</a:p>'


def alto_linea(L, size):
    """Interlineado de PowerPoint más cercano a L (mm de Beamer) para texto de `size` pt de Beamer.
    PowerPoint redondea el interlineado exacto a puntos enteros y el porcentual a pasos de 1 % (de 1,2 em);
    por encima del 100 % ambos se comportan igual: renglón de alto H con la línea base al 75 %.
    Devuelve (xml de a:lnSpc, H en mm de Beamer)."""
    L_pt = mm_a_pt(L) * K
    tam = size * K
    H_exacto = round(L_pt)
    p = max(1.01, round(L_pt / (1.2 * tam), 2))
    H_pct = 1.2 * p * tam
    if abs(H_pct - L_pt) < abs(H_exacto - L_pt):
        return f'<a:lnSpc><a:spcPct val="{int(round(p * 100)) * 1000}"/></a:lnSpc>', H_pct / K / 72 * 25.4
    return f'<a:lnSpc><a:spcPts val="{H_exacto * 100}"/></a:lnSpc>', H_exacto / K / 72 * 25.4


def cuerpo_xml(parrafos, base, L, algn="l", marL=0.0, indent=0.0, vineta=None, x_texto=None):
    """parrafos: lista de (línea base de la primera línea, texto) o (base, texto, opciones).
    Devuelve (xml, borde superior, alto total). El espacio antes de cada párrafo (puntos enteros, como lo
    redondea PowerPoint) se calcula desde la posición real del párrafo anterior, para que el error no se acumule."""
    xml, real_ultima, prev_H, primera = [], None, None, None
    for k, par in enumerate(parrafos):
        b, texto = par[0], par[1]
        op = par[2] if len(par) > 2 else {}
        est = dict(base, **op.get("estilo", {}))
        lnspc, H = alto_linea(op.get("L", L), est["size"])
        frac = BASE
        if op.get("pct100"):
            # interlineado sencillo (100 %): renglón de 1,194 em con la línea base a 0,918 em (medido en
            # PowerPoint con LM Mono); se usa en el código porque el exacto se redondea a 18 pt
            em = est["size"] * 25.4 / 72
            lnspc, H, frac = '<a:lnSpc><a:spcPct val="100000"/></a:lnSpc>', 1.194 * em, 0.918 / 1.194
        n = texto.count("\n") + 1
        antes_pt = 0
        if real_ultima is None:
            primera = b - frac * H
            real = b
        else:
            hueco = (b - real_ultima) - (1 - BASE) * prev_H - BASE * H
            antes_pt = round(mm_a_pt(hueco) * K)
            if hueco < -0.1:
                raise ValueError(f"espacio negativo antes de {texto[:30]!r}: {hueco:.3f} mm")
            antes_pt = max(0, antes_pt)
            real = real_ultima + (1 - BASE) * prev_H + antes_pt / K / 72 * 25.4 + BASE * H
        vin = op.get("vineta", vineta)
        if isinstance(vineta, int) and "vineta" not in op:
            vin = vineta + k
        al, ml = op.get("algn", algn), op.get("marL", marL)
        x0 = x_texto + ml if (x_texto is not None and al == "l") else None
        xml.append(parrafo_xml(texto, est, lnspc, antes_pt, al, ml, op.get("indent", indent), vin, x0))
        real_ultima, prev_H = real + (n - 1) * H, H
    fondo = real_ultima + (1 - BASE) * prev_H
    return "".join(xml), primera, fondo - primera


# ------------------------------------------------------------------ formas
class Lienzo:
    def __init__(self, slide):
        self.slide = slide
        self.arbol = slide.shapes._spTree

    def _id(self):
        return self.slide.shapes._next_shape_id

    def _agregar(self, xml):
        el = etree.fromstring(xml)
        self.arbol.append(el)
        return el

    def texto(self, nombre, x, w, parrafos, size, color=TINTA, font=REG, L=None, algn="l", marL=0.0,
              indent=0.0, vineta=None, holgura=2.0, estilo=None):
        base = {"font": font, "size": size, "color": color}
        base.update(estilo or {})
        cuerpo, top, alto = cuerpo_xml(parrafos, base, L, algn, marL, indent, vineta, x)
        i = self._id()
        if algn == "r":
            x, w = x - holgura, w + holgura
        elif algn == "ctr":
            x, w = x - holgura / 2, w + holgura
        else:
            w = w + holgura
        xml = (f'<p:sp {NS}><p:nvSpPr><p:cNvPr id="{i}" name="{escape(nombre)}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
               f'<p:spPr><a:xfrm><a:off x="{E(x)}" y="{E(top)}"/><a:ext cx="{E(w)}" cy="{E(alto)}"/></a:xfrm>'
               f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
               f'<p:txBody><a:bodyPr wrap="square" lIns="0" tIns="0" rIns="0" bIns="0" rtlCol="0" anchor="t"><a:noAutofit/></a:bodyPr>'
               f'<a:lstStyle/>{cuerpo}</p:txBody></p:sp>')
        return self._agregar(xml)

    def caja(self, nombre, x0, y0, x1, y1, relleno=None, linea=None, ancho_pt=0.5, radio_pt=0.0, guion=None,
             parrafos=None, size=None, color=TINTA, font=MED, L=None, algn="ctr", lins=0.0, estilo=None, ajuste="square"):
        """Rectángulo (redondeado si radio_pt > 0) con texto opcional; la línea base del texto es exacta."""
        i = self._id()
        w, h = x1 - x0, y1 - y0
        adentro = 0.0
        if radio_pt > 0:
            adj = int(round(radio_pt * 25.4 / 72 / min(w, h) * 100000))
            adentro = 0.29289 * radio_pt * 25.4 / 72
            geo = f'<a:prstGeom prst="roundRect"><a:avLst><a:gd name="adj" fmla="val {adj}"/></a:avLst></a:prstGeom>'
        else:
            geo = '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
        fill = f'<a:solidFill><a:srgbClr val="{relleno}"/></a:solidFill>' if relleno else '<a:noFill/>'
        if linea:
            dash = ''
            if guion:
                d = int(round(guion / ancho_pt * 100000))
                dash = f'<a:custDash><a:ds d="{d}" sp="{d}"/></a:custDash>'
            ln = (f'<a:ln w="{int(round(ancho_pt * K * 12700))}"><a:solidFill><a:srgbClr val="{linea}"/></a:solidFill>'
                  f'{dash}<a:round/></a:ln>')
        else:
            ln = '<a:ln><a:noFill/></a:ln>'
        tins, cuerpo = 0.0, '<a:p><a:endParaRPr lang="es-CO" dirty="0"/></a:p>'
        if parrafos:
            base = {"font": font, "size": size, "color": color}
            base.update(estilo or {})
            cuerpo, top, _ = cuerpo_xml(parrafos, base, L, algn, x_texto=x0 + max(lins, adentro))
            tins = top - y0 - adentro
            lins = max(0.0, lins - adentro)
        xml = (f'<p:sp {NS}><p:nvSpPr><p:cNvPr id="{i}" name="{escape(nombre)}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
               f'<p:spPr><a:xfrm><a:off x="{E(x0)}" y="{E(y0)}"/><a:ext cx="{E(w)}" cy="{E(h)}"/></a:xfrm>{geo}{fill}{ln}</p:spPr>'
               f'<p:txBody><a:bodyPr wrap="{ajuste}" lIns="{E(lins)}" tIns="{E(tins)}" rIns="{E(lins)}" bIns="0" rtlCol="0" anchor="t">'
               f'<a:noAutofit/></a:bodyPr><a:lstStyle/>{cuerpo}</p:txBody></p:sp>')
        return self._agregar(xml)

    def flecha(self, nombre, x0, y0, x1, y1, color=TINTA, ancho_pt=0.8, guion=None, desde=None, hasta=None,
               punta=True):
        i = self._id()
        x, y = min(x0, x1), min(y0, y1)
        w, h = abs(x1 - x0), abs(y1 - y0)
        flip = (' flipH="1"' if x1 < x0 else '') + (' flipV="1"' if y1 < y0 else '')
        dash = ''
        if guion:
            d = int(round(guion / ancho_pt * 100000))
            dash = f'<a:custDash><a:ds d="{d}" sp="{d}"/></a:custDash>'
        cola = '<a:tailEnd type="triangle" w="med" len="lg"/>' if punta else ''
        cx = ''
        if desde:
            cx += f'<a:stCxn id="{desde[0]}" idx="{desde[1]}"/>'
        if hasta:
            cx += f'<a:endCxn id="{hasta[0]}" idx="{hasta[1]}"/>'
        xml = (f'<p:cxnSp {NS}><p:nvCxnSpPr><p:cNvPr id="{i}" name="{escape(nombre)}"/><p:cNvCxnSpPr>{cx}</p:cNvCxnSpPr><p:nvPr/></p:nvCxnSpPr>'
               f'<p:spPr><a:xfrm{flip}><a:off x="{E(x)}" y="{E(y)}"/><a:ext cx="{E(w)}" cy="{E(h)}"/></a:xfrm>'
               f'<a:prstGeom prst="straightConnector1"><a:avLst/></a:prstGeom>'
               f'<a:ln w="{int(round(ancho_pt * K * 12700))}"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill>{dash}'
               f'<a:round/>{cola}</a:ln></p:spPr></p:cxnSp>')
        return self._agregar(xml)

    def linea(self, nombre, x0, y, x1, color=TINTA, ancho_mm=0.3):
        i = self._id()
        xml = (f'<p:cxnSp {NS}><p:nvCxnSpPr><p:cNvPr id="{i}" name="{escape(nombre)}"/><p:cNvCxnSpPr/><p:nvPr/></p:nvCxnSpPr>'
               f'<p:spPr><a:xfrm><a:off x="{E(x0)}" y="{E(y)}"/><a:ext cx="{E(x1 - x0)}" cy="0"/></a:xfrm>'
               f'<a:prstGeom prst="line"><a:avLst/></a:prstGeom>'
               f'<a:ln w="{int(round(ancho_mm * K * 36000))}" cap="flat"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill></a:ln>'
               f'</p:spPr></p:cxnSp>')
        return self._agregar(xml)

    def imagen(self, ruta, x0, y0, x1, y1, descripcion):
        pic = self.slide.shapes.add_picture(str(ruta), Emu(E(x0)), Emu(E(y0)), Emu(E(x1 - x0)), Emu(E(y1 - y0)))
        pic.name = Path(ruta).stem
        pic._element.nvPicPr.cNvPr.set("descr", descripcion)
        return pic


# ------------------------------------------------------------------ bloques que se repiten
def lista(lz, nombre, x_vineta, x_texto, w, items, size=T_NORMAL, L=L_NORMAL, color=TINTA):
    marL = x_texto - x_vineta
    return lz.texto(nombre, x_vineta, w + marL, items, size, color, L=L, marL=marL, indent=-marL, vineta="cuadro")


def numerada(lz, nombre, x_num, x_texto, w, items, size=T_NORMAL, L=L_NORMAL):
    marL = x_texto - x_num
    return lz.texto(nombre, x_num, w + marL, items, size, TINTA, L=L, marL=marL, indent=-marL, vineta=1)


def cifra(lz, nombre, x, w, b_num, numero, b_ley, leyenda, mas=None):
    """\\cifra de Beamer: número grande azul en Plex Medium y leyenda gris debajo (mismo cuadro)."""
    pars = [(b_num, numero, {"estilo": {"font": MED, "size": T_CIFRA, "color": AZUL}, "L": 7.6}),
            (b_ley, leyenda, {"L": L_SMALL})]
    for b, t in (mas or []):
        pars.append((b, t, {"estilo": {"size": T_FOOT}, "L": L_FOOT}))
    return lz.texto(nombre, x, w, pars, T_SMALL, SECUNDARIO, L=L_SMALL)


def nota(lz, nombre, x, w, pars):
    return lz.texto(nombre, x, w, pars, T_FOOT, SECUNDARIO, L=L_FOOT)


def fuente(lz, b, texto):
    return lz.texto("Fuente", 13.0, 134, [(b, texto)], T_TINY, TENUE, L=2.47)


# ------------------------------------------------------------------ plantilla: tema, patrón y diseños
def preparar(prs):
    prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)
    patron = prs.slide_master

    # tema: colores y fuentes de la presentación
    tema = patron.part.part_related_by(RT.THEME)
    raiz = etree.fromstring(tema.blob)
    a = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
    raiz.set("name", "Difusion PS5 GTA6")
    esquema = raiz.find(f"{a}themeElements/{a}clrScheme")
    esquema.set("name", "Difusion")
    valores = {"dk1": TINTA, "lt1": BLANCO, "dk2": SECUNDARIO, "lt2": PAPEL, "accent1": AZUL, "accent2": TERRACOTA,
               "accent3": AZULCLARO, "accent4": BORDE, "accent5": TENUE, "accent6": CLARO, "hlink": AZUL,
               "folHlink": SECUNDARIO}
    for hijo in esquema:
        nombre = etree.QName(hijo).localname
        for c in list(hijo):
            hijo.remove(c)
        etree.SubElement(hijo, f"{a}srgbClr", val=valores[nombre])
    fuentes = raiz.find(f"{a}themeElements/{a}fontScheme")
    fuentes.set("name", "IBM Plex Sans")
    fuentes.find(f"{a}majorFont/{a}latin").set("typeface", MED)
    fuentes.find(f"{a}minorFont/{a}latin").set("typeface", REG)
    tema._blob = etree.tostring(raiz, xml_declaration=True, encoding="UTF-8", standalone=True)

    # fondo papel en el patrón
    p = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
    csld = patron._element.find(f"{p}cSld")
    bg = csld.find(f"{p}bg")
    if bg is not None:
        csld.remove(bg)
    csld.insert(0, etree.fromstring(f'<p:bg {NS}><p:bgPr><a:solidFill><a:srgbClr val="{PAPEL}"/></a:solidFill>'
                                    f'<a:effectLst/></p:bgPr></p:bg>'))

    # solo dos diseños: Portada (en blanco) y Contenido (sección + título + pie)
    diseños = list(patron.slide_layouts)
    contenido, portada = diseños[5], diseños[6]
    for d in diseños:
        if d not in (contenido, portada):
            patron.slide_layouts.remove(d)
    portada._element.find(f"{p}cSld").set("name", "Portada")
    contenido._element.find(f"{p}cSld").set("name", "Contenido")
    for d in (portada, contenido):
        arbol = d.shapes._spTree
        for sp in list(arbol):
            ph = sp.find(f".//{p}ph")
            if ph is not None and ph.get("type") in ("dt", "ftr", "sldNum"):
                arbol.remove(sp)

    # título: Plex Medium 14,35 pt de Beamer, línea base a 19,65 mm
    titulo = next(ph for ph in contenido.placeholders if ph.placeholder_format.idx == 0)._element
    top = 19.65 - BASE * alto_linea(L_TITULO, T_LARGE)[1]
    lnspc = alto_linea(L_TITULO, T_LARGE)[0]
    sppr = titulo.find(f"{p}spPr")
    for c in list(sppr):
        sppr.remove(c)
    sppr.append(etree.fromstring(
        f'<a:xfrm {NS}><a:off x="{E(13)}" y="{E(top)}"/><a:ext cx="{E(136)}" cy="{E(L_TITULO)}"/></a:xfrm>'))
    tx = titulo.find(f"{p}txBody")
    for c in list(tx):
        tx.remove(c)
    tx.append(etree.fromstring(f'<a:bodyPr {NS} wrap="none" lIns="0" tIns="0" rIns="0" bIns="0" anchor="t"><a:noAutofit/></a:bodyPr>'))
    tx.append(etree.fromstring(
        f'<a:lstStyle {NS}><a:lvl1pPr algn="l">{lnspc}<a:spcBef><a:spcPts val="0"/></a:spcBef>'
        f'<a:buNone/><a:defRPr sz="{hp(T_LARGE)}" b="0" kern="100"><a:solidFill><a:srgbClr val="{TINTA}"/></a:solidFill>'
        f'<a:latin typeface="{MED}"/><a:cs typeface="{MED}"/></a:defRPr></a:lvl1pPr></a:lstStyle>'))
    tx.append(etree.fromstring(f'<a:p {NS}><a:r><a:rPr lang="es-CO"/><a:t>Título de la diapositiva</a:t></a:r></a:p>'))

    # sección (antetítulo): Plex 7,97 pt, terracota, versalitas espaciadas, línea base 12,33 mm
    arbol = contenido.shapes._spTree
    L_SEC = 3.34
    arbol.append(etree.fromstring(
        f'<p:sp {NS}><p:nvSpPr><p:cNvPr id="20" name="Sección"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
        f'<p:nvPr><p:ph type="body" sz="quarter" idx="13"/></p:nvPr></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="{E(13)}" y="{E(12.33 - BASE * alto_linea(L_SEC, T_SCRIPT)[1])}"/><a:ext cx="{E(110)}" cy="{E(L_SEC)}"/></a:xfrm></p:spPr>'
        f'<p:txBody><a:bodyPr wrap="none" lIns="0" tIns="0" rIns="0" bIns="0" anchor="t"><a:noAutofit/></a:bodyPr>'
        f'<a:lstStyle><a:lvl1pPr marL="0" indent="0" algn="l">{alto_linea(L_SEC, T_SCRIPT)[0]}'
        f'<a:spcBef><a:spcPts val="0"/></a:spcBef><a:buNone/>'
        f'<a:defRPr sz="{hp(T_SCRIPT)}" cap="all" spc="{int(round(0.12 * T_SCRIPT * K * 100))}" kern="0">'
        f'<a:solidFill><a:srgbClr val="{TERRACOTA}"/></a:solidFill><a:latin typeface="{REG}"/><a:cs typeface="{REG}"/></a:defRPr>'
        f'</a:lvl1pPr></a:lstStyle><a:p><a:r><a:rPr lang="es-CO"/><a:t>Sección</a:t></a:r></a:p></p:txBody></p:sp>'))

    # pie: autores y universidad a la izquierda, número de diapositiva a la derecha
    est = {"font": REG, "size": T_TINY, "color": TENUE}
    L_PIE = 2.47
    top = 85.55 - BASE * alto_linea(L_PIE, T_TINY)[1]
    izq = parrafo_xml("Delgado · Monroy · Baquero\u2003Universidad de los Llanos", est, L_PIE)
    arbol.append(etree.fromstring(
        f'<p:sp {NS}><p:nvSpPr><p:cNvPr id="21" name="Pie"/><p:cNvSpPr txBox="1"/><p:nvPr userDrawn="1"/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="{E(13)}" y="{E(top)}"/><a:ext cx="{E(80)}" cy="{E(L_PIE)}"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
        f'<p:txBody><a:bodyPr wrap="none" lIns="0" tIns="0" rIns="0" bIns="0" anchor="t"><a:noAutofit/></a:bodyPr><a:lstStyle/>{izq}</p:txBody></p:sp>'))
    num = parrafo_xml("", est, L_PIE, algn="r").replace(
        "<a:endParaRPr",
        f'<a:fld id="{{B6F15528-21DE-4FAA-801E-634DDDAF4B2B}}" type="slidenum">{rpr(est)}<a:t>‹#›</a:t></a:fld>'
        f'<a:r>{rpr(est)}<a:t>{FINO}/{FINO}19</a:t></a:r><a:endParaRPr', 1)
    arbol.append(etree.fromstring(
        f'<p:sp {NS}><p:nvSpPr><p:cNvPr id="22" name="Número de diapositiva"/><p:cNvSpPr txBox="1"/><p:nvPr userDrawn="1"/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="{E(127)}" y="{E(top)}"/><a:ext cx="{E(20)}" cy="{E(L_PIE)}"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
        f'<p:txBody><a:bodyPr wrap="none" lIns="0" tIns="0" rIns="0" bIns="0" anchor="t"><a:noAutofit/></a:bodyPr><a:lstStyle/>{num}</p:txBody></p:sp>'))

    # el título y el cuerpo del patrón, en proporción 16:9
    for sp in patron.placeholders:
        tipo = sp.placeholder_format.type
        if sp.placeholder_format.idx == 0:
            sp.left, sp.top, sp.width, sp.height = Emu(E(13)), Emu(E(19.65 - BASE * alto_linea(L_TITULO, T_LARGE)[1])), Emu(E(134)), Emu(E(L_TITULO))
        elif sp.placeholder_format.idx == 1:
            sp.left, sp.top, sp.width, sp.height = Emu(E(13)), Emu(E(26)), Emu(E(134)), Emu(E(52))
        else:
            sp._element.getparent().remove(sp._element)
    return portada, contenido


def nueva(prs, diseño, seccion, titulo):
    s = prs.slides.add_slide(diseño)
    if titulo is not None:
        llenar(s.shapes.title, titulo, {"font": MED, "size": T_LARGE, "color": TINTA}, L_TITULO)
        llenar(s.placeholders[13], seccion.upper(),
               {"font": REG, "size": T_SCRIPT, "color": TERRACOTA, "ls": 0.12, "spc_explicito": True}, 3.34)
    return s, Lienzo(s)


def llenar(ph, texto, est, L):
    """Escribe en un marcador de posición del diseño con el mismo motor de texto (kerning incluido)."""
    tx = ph._element.find("{http://schemas.openxmlformats.org/presentationml/2006/main}txBody")
    for par in tx.findall("{http://schemas.openxmlformats.org/drawingml/2006/main}p"):
        tx.remove(par)
    tx.append(etree.fromstring(parrafo_xml(texto, est, L, x0=13.0).replace("<a:p>", f"<a:p {NS}>", 1)))


# ------------------------------------------------------------------ notas del orador (desde el .tex)
def cifras_tex():
    valores = {}
    for m in re.finditer(r"\\newcommand\{\\(cifra\w+)\}\{(.*)\}\s*$", (PROYECTO / "articulo/tablas/cifras.tex").read_text(encoding="utf-8"), re.M):
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


def poner_nota(slide, runs):
    tf = slide.notes_slide.notes_text_frame
    p = tf.paragraphs[0]
    for t, b, i in runs:
        r = p.add_run()
        r.text = t
        r.font.name = REG
        r.font.size = Pt(12)
        r.font.bold = b
        r.font.italic = i


# ------------------------------------------------------------------ diapositivas
def construir():
    plex = PROYECTO / "analisis/fuentes"
    lm = Path(__file__).parent / "fuentes"
    MEDIDAS.update({REG: Fuente(plex / "IBMPlexSans-Regular.ttf"), MED: Fuente(plex / "IBMPlexSans-Medium.ttf"),
                    MAT: Fuente(lm / "LMFormulas-Regular.ttf"), OBL: Fuente(lm / "SansOblicuaDiapositivas-Regular.ttf"), MONO8: Fuente(lm / "LMMono8-Regular.ttf"),
                    MONO9: Fuente(lm / "LMMono9-Regular.ttf")})
    prs = Presentation()
    portada, contenido = preparar(prs)
    FIG = PROYECTO / "analisis/figuras/diapositivas"
    CAP = PROYECTO / "presentacion/figuras"

    # 1 · portada ---------------------------------------------------------------
    s, lz = nueva(prs, portada, None, None)
    lz.texto("Antetítulo", 13.0, 84, [(6.67, "PROYECTO 14 · SIMULACIÓN COMPUTACIONAL")], T_SCRIPT, TERRACOTA, L=3.34,
             estilo={"ls": 0.12})
    lz.texto("Título", 13.0, 83.1, [(20.80, "Publicidad y redes\nsociales en la difusión\nde innovaciones")], T_PORTADA,
             TINTA, MED, L=9.14)
    lz.texto("Subtítulo", 13.0, 83.1, [(46.86, "Un modelo basado en agentes de la PS5 y del\nlanzamiento de GTA¦6")],
             T_NORMAL, SECUNDARIO, L=L_NORMAL)
    lz.texto("Integrantes", 13.0, 83.1, [(63.86, "Jesus Gregorio Delgado\nDavid Andres Monroy Aguiar\nDuvan Felipe Baquero Cerquera")],
             T_SMALL, TINTA, L=L_SMALL)
    lz.texto("Institución y fecha", 13.0, 83.1, [(80.63, "Ingeniería de Sistemas · Universidad de los Llanos\n17 de noviembre de 2026")],
             T_SCRIPT, TENUE, L=3.34)
    lz.imagen(FIG / "portada_red.png", 98.76, 19.88, 147.00, 68.12, "Red social con nodos que ya adoptaron, en azul y terracota")

    # 2 · motivación -------------------------------------------------------------
    s, lz = nueva(prs, contenido, "Motivación", "Dos lanzamientos, dos maneras de difundirse")
    cifra(lz, "Cifra PS5", 13.00, 41.5, 36.96, "97,9¦M", 42.18, "PS5 vendidas de\nnoviembre de 2020 a\nseptiembre de 2026")
    cifra(lz, "Cifra lanzamiento", 59.23, 41.5, 36.96, "19 nov.", 42.18, "sale GTA¦6, solo para\nconsolas de esta\ngeneración")
    cifra(lz, "Cifra tráiler", 105.46, 41.5, 36.96, "90¦M", 42.18, "vistas del primer tráiler de\nGTA¦6 en 24 horas")
    lista(lz, "Viñetas", 14.49, 18.00, 129, [
        (63.76, "Bass: un producto se difunde por ⟨t|publicidad⟩ (externa) e ⟨a|imitación⟩ (voz a\nvoz)."),
        (74.38, "La PS5 crece por imitación; un gran estreno vende casi todo al salir.")])
    fuente(lz, 80.59, "Sony Interactive Entertainment, Business Data & Sales; Guinness World Records (2023).")

    # 3 · problema ----------------------------------------------------------------
    s, lz = nueva(prs, contenido, "Problema", "El modelo agregado no ve la red social")
    lz.imagen(FIG / "mezcla_vs_red.png", 13.00, 34.61, 82.68, 70.73,
              "A la izquierda, mezcla completa: todos conectados con todos; a la derecha, una red social")
    lz.texto("Texto", 88.04, 59.0, [(30.96, "Bass: todos influyen sobre todos.\nEn la realidad, solo los contactos.")],
             T_NORMAL, TINTA, L=L_NORMAL)
    lista(lz, "Preguntas", 89.53, 93.04, 54.0, [
        (44.57, "¿Qué pasa sin publicidad?"),
        (50.41, "¿Importa la densidad o la\nforma de la red?"),
        (61.02, "¿Cuánto se pierde con una\ncampaña corta?"),
        (71.64, "¿Responden igual una consola\ny un videojuego?")])

    # 4 · justificación -----------------------------------------------------------
    s, lz = nueva(prs, contenido, "Justificación", "Simular permite probar lo que no se puede observar")
    for x, cab, txt in ((13.00, "Individuos y red", "Cada persona es un agente\ncon sus contactos y una\nregla de decisión."),
                        (59.90, "Contrafactuales", "Lanzar sin publicidad,\ncambiar la red o acortar la\ncampaña: imposible de\nobservar en la realidad."),
                        (106.80, "Datos reales", "PS5: calibrada y evaluada\ncon ventas oficiales. GTA¦6,\nsin ventas aún: por analogía\ncon GTA¦V.")):
        lz.texto(cab, x, 40.2, [(38.54, cab, {"estilo": {"font": MED, "size": T_NORMAL, "color": AZUL}, "L": L_NORMAL}),
                                (44.41, txt)], T_FOOT, SECUNDARIO, L=L_FOOT)
    nota(lz, "Nota", 13.0, 134, [(68.73, "NetLogo: libre, el modelo completo en un archivo y BehaviorSpace para repetir cada escenario\n30 veces.")])

    # 5 · objetivos -----------------------------------------------------------------
    s, lz = nueva(prs, contenido, "Objetivos", "Qué nos propusimos")
    lz.texto("Objetivo general", 13.0, 134, [
        (32.18, "⟨M|General.⟩ Medir el efecto de la publicidad y de la red sobre la adopción final,\nen la PS5 y en GTA¦6."),
        (46.74, "⟨M|Específicos⟩")], T_NORMAL, TINTA, L=L_NORMAL)
    numerada(lz, "Objetivos específicos", 12.65, 18.00, 129, [
        (53.57, "Implementar en NetLogo el modelo de Bass en red, con tres tipos de red."),
        (59.41, "Calibrar con la PS5 (entrenamiento, validación, prueba) y parametrizar\nGTA¦6 por analogía."),
        (70.02, "Evaluar con 30 réplicas publicidad, densidad, topología y duración."),
        (75.86, "Verificar con una reimplementación en Python.")])

    # 6 · modelo ---------------------------------------------------------------------
    s, lz = nueva(prs, contenido, "Metodología", "Cada mes, cada persona decide: publicidad y vecinos")
    g, m_, f_ = "\u2004", "\u205f", "\u2009"
    formula = ("⟨m|P⟩⟨_@53.086|i⟩⟨m@55.878|=⟩⟨m@61.131|1⟩⟨m@64.74|−⟩⟨m@69.801|(⟩⟨m@71.725|1⟩⟨m@75.331|−⟩"
               "⟨mt@80.392|p⟩⟨mt@83.717|a⟩⟨_t@86.324|t⟩⟨m@87.769|)⟩⟨m@90.532|(⟩⟨m@92.456|1⟩⟨m@96.069|−⟩"
               "⟨ma@101.13|q⟩⟨ma@104.349|f⟩⟨_a@106.795|i⟩⟨m@108.181|)⟩")
    lz.texto("Fórmula", 49.891, 62, [(36.44, formula)], T_LARGE, TINTA, MAT, L=L_TITULO)
    lz.texto("Publicidad e imitación", 13.0, 61.6, [
        (50.26, "publicidad", {"estilo": {"font": MED, "size": T_NORMAL, "color": TERRACOTA}, "L": L_FOOT}),
        (54.13, "⟨m|p⟩⟨@14.63|: probabilidad mensual de que la campaña⟩\nconvenza; ⟨m@28.006|a⟩⟨_@29.728|t⟩⟨m@31.812|=⟩⟨m@35.241|1⟩⟨@36.86| mientras está activa.⟩"),
        (65.77, "imitación", {"estilo": {"font": MED, "size": T_NORMAL, "color": AZUL}, "L": L_FOOT}),
        (69.64, "⟨m|q⟩⟨@14.45| por ⟩⟨m@20.826|f⟩⟨_@22.404|i⟩⟨@23.52|, la fracción de vecinos que ya⟩\nadoptó.")], T_FOOT, SECUNDARIO, L=L_FOOT)
    lista(lz, "Supuestos", 84.31, 87.68, 61.0, [
        (48.94, "Adoptar es irreversible; todos\ndeciden a la vez."),
        (59.49, "Red completa = Bass: la diferencia es\nel efecto de la red."),
        (70.03, "Redes aleatoria, mundo pequeño y\nlibre de escala.")], T_SMALL, L_SMALL)

    # 7 · esquema --------------------------------------------------------------------
    s, lz = nueva(prs, contenido, "Metodología", "Del dato al escenario")
    lz.caja("Marco: cada mes", 23.609, 50.317, 144.891, 76.993, linea=AZUL, ancho_pt=0.4, radio_pt=3, guion=3)
    arriba = [("Datos", "Sony, Take-Two", 13.197, 31.42, CLARO, BORDE, 0.5),
              ("Calibración", "Bass, analogía", 40.997, 31.57, CLARO, BORDE, 0.5),
              ("Modelo", "NetLogo + nw", 68.797, 31.47, AZULFONDO, AZUL, 0.8),
              ("Escenarios", "BehaviorSpace", 96.597, 31.50, CLARO, BORDE, 0.5),
              ("Análisis", "Python", 124.397, 31.59, CLARO, BORDE, 0.5)]
    ids = []
    for cab, det, x0, b, fondo, borde, ancho in arriba:
        sp = lz.caja(cab, x0, 26.405, x0 + 22.406, 38.405, fondo, borde, ancho, 2,
                     parrafos=[(b, cab), (b + 3.865, det, {"estilo": {"size": T_SCRIPT, "color": SECUNDARIO}})],
                     size=T_SMALL, color=TINTA, font=MED, L=3.865, estilo={"espacio": 1.17})
        ids.append(int(sp.find(".//{http://schemas.openxmlformats.org/presentationml/2006/main}cNvPr").get("id")))
    for k, (x0, x1) in enumerate(((35.691, 40.33), (63.491, 68.077), (91.344, 95.93), (119.091, 123.73))):
        lz.flecha(f"Flecha {k + 1}", x0, 32.405, x1, 32.405, desde=(ids[k], 3), hasta=(ids[k + 1], 1))
    camp = lz.caja("Campaña", 26.197, 52.905, 54.603, 61.905, TERRACOTAFONDO, TERRACOTA, 0.5, 2,
                   parrafos=[(56.50, "Campaña"), (60.36, "⟨m|p⟩⟨m@40.014|a⟩⟨_@41.604|t⟩", {"estilo": {"size": T_SCRIPT}, "algn": "l", "marL": 38.015 - 26.404})],
                   size=T_SMALL, color=TINTA, font=MED, L=3.865, estilo={"espacio": 1.17})
    red = lz.caja("Red social", 26.197, 65.405, 54.603, 74.405, AZULFONDO, AZUL, 0.5, 2,
                  parrafos=[(69.01, "Red social"), (72.87, "⟨m|q⟩⟨m@40.087|f⟩⟨_@41.526|i⟩", {"estilo": {"size": T_SCRIPT}, "algn": "l", "marL": 38.159 - 26.404})],
                  size=T_SMALL, color=TINTA, font=MED, L=3.865, estilo={"espacio": 1.17})
    formula2 = ("⟨m|P⟩⟨_@68.285|i⟩⟨m@70.518|=⟩⟨m@74.31|1⟩⟨m@76.889|−⟩⟨m@80.438|(⟩⟨m@81.802|1⟩⟨m@84.378|−⟩"
                "⟨m@87.928|p⟩⟨m@90.279|a⟩⟨_@92.14|t⟩⟨m@93.377|)⟩⟨m@94.74|(⟩⟨m@96.104|1⟩⟨m@98.684|−⟩"
                "⟨m@102.233|q⟩⟨m@104.511|f⟩⟨_@106.235|i⟩⟨m@107.405|)⟩")
    regla = lz.caja("Regla de adopción", 64.697, 53.155, 110.103, 74.155, BLANCO, AZUL, 0.8, 2,
                    parrafos=[(61.80, "Regla de adopción"), (67.42, formula2, {"L": 4.5, "algn": "l"})], lins=66.028 - 64.697, estilo={"espacio": 1.17}, ajuste="none",
                    size=T_SMALL, color=TINTA, font=MED, L=3.865)
    estado = lz.caja("Estado", 118.897, 57.593, 142.303, 69.717, BLANCO, BORDE, 0.5, 2,
                     parrafos=[(60.90, "Estado", {"L": 2.7}), (64.76, "adopta y no\nvuelve atrás", {"estilo": {"size": T_SCRIPT}, "L": 4.22})],
                     size=T_SMALL, color=TINTA, font=MED, L=3.865, estilo={"espacio": 1.17})
    idc = lambda sp: int(sp.find(".//{http://schemas.openxmlformats.org/presentationml/2006/main}cNvPr").get("id"))
    lz.flecha("Flecha campaña", 54.691, 57.405, 63.977, 57.405, TERRACOTA, desde=(idc(camp), 3))
    lz.flecha("Flecha red", 54.691, 69.905, 63.977, 69.905, AZUL, desde=(idc(red), 3))
    lz.flecha("Flecha estado", 110.244, 63.655, 118.23, 63.655, desde=(idc(regla), 3), hasta=(idc(estado), 1))
    lz.flecha("Flecha al interior", 80.0, 38.546, 80.0, 49.667, AZUL, guion=3, desde=(ids[2], 2))
    lz.texto("Etiqueta: cada mes", 24.89, 40, [(48.52, "cada mes, dentro del modelo")], T_SCRIPT, AZUL, L=3.34)

    # 8 · implementación ----------------------------------------------------------------
    s, lz = nueva(prs, contenido, "Metodología", "Implementación en NetLogo")
    lz.imagen(CAP / "netlogo_ps5.png", 13.00, 25.53, 75.98, 68.75,
              "Interfaz del modelo en NetLogo con el caso PS5 en una red libre de escala")
    lz.texto("Pie de la captura", 13.0, 63.0, [(74.53, "Interfaz del modelo (configuración de demostración: caso PS5, red\nlibre de escala, mes 30).")],
             T_TINY, TENUE, L=L_NORMAL)
    codigo = ("⟨a|to⟩ decidir\n"
              "  ⟨a|let⟩ p p-efectivo\n"
              "  ⟨a|ask turtles with⟩\n"
              "      [susceptible? and ⟨a|not⟩ adoptante?] [\n"
              "    ⟨a|let⟩ vecinos link-neighbors\n"
              "    ⟨a|let⟩ f 0\n"
              "    ⟨a|if⟩ any? vecinos [\n"
              "      ⟨a|set⟩ f ⟨a|count⟩ vecinos ⟨a|with⟩ [adoptante?]\n"
              "        / ⟨a|count⟩ vecinos ]\n"
              "    ⟨a|let⟩ prob 1 - (1 - p) * (1 - q-imitacion * f)\n"
              "    ⟨a|set⟩ decide-adoptar? random-float 1 < prob ]\n"
              "⟨a|end⟩")
    # PowerPoint dibuja LM Mono a este tamaño con un avance 0,49 % de em más corto: se compensa letra por letra
    lz.texto("Código: decidir", 80.0, 67.0, [(29.32, codigo, {"pct100": True})], T_CODIGO, TINTA, MONO8, L=3.0225,
             estilo={"track": 0.0049})
    nota(lz, "Nota", 80.0, 63.0, [(70.43, "⟨c|actualizar⟩⟨@96.61| aplica todas las decisiones a la⟩\nvez. La extensión nw genera las redes; el\nselector de caso carga PS5, GTA¦6 o libre.")])

    # 9 · datos PS5 --------------------------------------------------------------------
    s, lz = nueva(prs, contenido, "Conjunto de datos", "La PS5: 24 trimestres de ventas oficiales de Sony")
    lz.imagen(FIG / "serie_ps5.png", 13.00, 24.27, 93.40, 74.74,
              "Serie de ventas acumuladas de la PS5 con la partición en entrenamiento, validación y prueba")
    lista(lz, "Viñetas", 100.39, 103.76, 44.0, [
        (35.42, "4,5 a 97,9 millones\nacumulados, dic.¦2020 a\nsep.¦2026."),
        (50.18, "Adopción = acumulado /\nbase de PS4 (117¦M), fijada\nantes de ver la prueba."),
        (64.95, "Simulación: 1770 corridas\nde 1000 agentes.")], T_SMALL, L_SMALL)
    fuente(lz, 78.48, "Sony Interactive Entertainment, Business Data & Sales (unidades vendidas a tiendas).")

    # 10 · analogía GTA V ---------------------------------------------------------------
    s, lz = nueva(prs, contenido, "Conjunto de datos", "GTA¦6 aún no tiene ventas: lo parametrizamos con GTA¦V")
    lz.imagen(FIG / "analogia_gtav.png", 13.00, 23.67, 81.02, 76.21,
              "Ventas de GTA V y la curva de Bass ajustada, que concentra las compras en el lanzamiento")
    lista(lz, "Viñetas", 92.35, 95.72, 52.0, [
        (33.89, "GTA¦V: 29¦M en seis semanas y\n34¦M al año, sobre 160¦M de\nconsolas."),
        (48.65, "Mismo ajuste de Bass:\npublicidad de ⟨t|0,69⟩ al mes, unas\n18 veces la imitación."),
        (63.41, "GTA¦6 entre dueños de PS5:\npotencial 21¦¦%, 7¦¦% el primer\ndía, 24 meses.")], T_SMALL, L_SMALL)
    fuente(lz, 79.39, "Take-Two Interactive, resultados trimestrales 2013–2014; primer día: Guinness World Records (2013).")

    # 11 · diseño experimental ----------------------------------------------------------
    s, lz = nueva(prs, contenido, "Diseño experimental", "Cuatro experimentos, 30 réplicas por escenario")
    for nombre, x0, x1, fondo, col, b, txt in (
            ("Entrenamiento", 13.0, 73.0, AZUL, BLANCO, 33.80, "entrenamiento\ndic.¦2020–dic.¦2023 · 13 trimestres"),
            ("Validación", 74.0, 104.999, AZULCLARO, TINTA, 33.85, "validación\n2024 · 4 trimestres"),
            ("Prueba", 105.999, 146.999, TERRACOTA, BLANCO, 33.80, "prueba\n2025–2026 · 7 trimestres")):
        lz.caja(nombre, x0, 29.443, x1, 39.443, fondo, None, parrafos=[(b, txt)], size=T_SCRIPT, color=col, font=REG, L=3.34)
    for c, b, txt in ((30.0, 43.20, "ajusta ⟨m|p⟩ y ⟨m|q⟩"), (76.5, 43.18, "elige ⟨m|m⟩ y la red"), (113.5, 43.52, "solo evalúa")):
        lz.texto("Uso: " + re.sub("⟨m\\|(.)⟩", r"\1", txt), c - 15, 30, [(b, txt)], T_SCRIPT, SECUNDARIO, L=3.34, algn="ctr")
    tabla_experimentos(s, lz)

    # 12 · medidas ----------------------------------------------------------------------
    s, lz = nueva(prs, contenido, "Medidas de desempeño", "Cómo medimos")
    lz.texto("Escenarios", 13.0, 63, [(38.20, "Escenarios")], T_NORMAL, AZUL, MED, L=L_NORMAL)
    lz.texto("Ajuste a la serie real", 84.02, 63, [(38.20, "Ajuste a la serie real")], T_NORMAL, AZUL, MED, L=L_NORMAL)
    lista(lz, "Medidas de escenarios", 14.63, 18.00, 59.0, [
        (45.53, "⟨t|Adopción final⟩:¦% de la población\nque adoptó al final del período (PS5:\n72 meses; GTA¦6: 24)."),
        (60.29, "Mes del 50¦¦% y mes del pico de\ncompras."),
        (70.83, "Media e IC del 95¦¦% con 30 réplicas.")], T_SMALL, L_SMALL)
    lista(lz, "Medidas de ajuste", 85.65, 89.02, 58.0, [
        (45.53, "RMSE: raíz del error cuadrático\nmedio, en puntos porcentuales."),
        (56.07, "MAPE: error porcentual absoluto\nmedio."),
        (66.62, "Por partición: entrenamiento,\nvalidación y prueba.")], T_SMALL, L_SMALL)

    # 13 · calibración -------------------------------------------------------------------
    s, lz = nueva(prs, contenido, "Resultados", "El modelo sigue la serie de prueba de la PS5")
    lz.imagen(FIG / "fig_calibracion.png", 13.00, 23.12, 98.76, 81.72,
              "Serie real de la PS5 frente a la curva de Bass y al modelo de agentes en las tres particiones")
    cifra(lz, "Cifra: error en prueba", 104.12, 42.9, 38.22, "4,91 pp", 43.86, "error en prueba del modelo\nde agentes (Bass: 3,22)",
          mas=[(56.51, "Bass anual: ⟨m@121.184|p⟩⟨@122.813|¦=¦0,097,⟩\n⟨m|q⟩⟨@105.571|¦=¦0,449; la imitación pesa⟩\n4,6 veces más. Red elegida en\nvalidación: red de mundo\npequeño, ⟨m@118.17|k⟩⟨@119.862|¦=¦16.⟩")])

    # 14 · publicidad --------------------------------------------------------------------
    s, lz = nueva(prs, contenido, "Resultados", "Sin publicidad, ninguno de los dos llega lejos")
    lz.imagen(FIG / "publicidad_casos.png", 19.70, 27.12, 140.30, 75.80,
              "Adopción con y sin campaña en la PS5 y en GTA 6, con densidad baja y alta")
    nota(lz, "Nota", 13.0, 134, [(79.83, "Red de mundo pequeño con ⟨m@53.46|k⟩⟨@55.152|¦=¦2 (discontinua) y 16 (continua).⟩")])

    # 15 · densidad y topología -----------------------------------------------------------
    s, lz = nueva(prs, contenido, "Resultados", "La red pesa sobre todo cuando no hay publicidad")
    lz.imagen(FIG / "densidad.png", 13.00, 27.78, 101.44, 74.64,
              "Adopción final según la densidad de la red y según la topología, con y sin campaña")
    cifra(lz, "Cifra: densidad", 106.80, 40.2, 35.94, "×¦2,5", 41.16, "adopción de la PS5 sin\ncampaña al pasar de\n⟨m|k⟩⟨@108.627|¦=¦2 a 16⟩",
          mas=[(56.33, "Con campaña, la misma\ndiferencia solo la multiplica\npor 1,1. Sin campaña, la red\nde mundo pequeño es la\ntopología más lenta.")])

    # 16 · duración --------------------------------------------------------------------------
    s, lz = nueva(prs, contenido, "Resultados", "GTA¦6: basta un mes; PS5: la campaña necesita tiempo")
    lz.imagen(FIG / "fraccion_duracion.png", 13.00, 26.18, 90.72, 77.03,
              "Fracción del efecto de una campaña permanente que se logra según la duración de la campaña")
    cifra(lz, "Cifra: un mes", 96.08, 50.9, 37.13, "71¦¦%", 42.34, "del efecto de una campaña\npermanente se logra con un\nmes en GTA¦6")
    cifra(lz, "Cifra: un año", 96.08, 50.9, 62.16, "55¦¦%", 67.38, "se logra con un año en la PS5\n(dos años: 75¦¦%)")

    # 17 · demostración --------------------------------------------------------------------
    s, lz = nueva(prs, contenido, "Demostración", "En vivo en NetLogo")
    lz.imagen(CAP / "netlogo_gta6.png", 13.00, 27.44, 59.10, 70.54, "Interfaz del modelo con el caso GTA 6")
    lz.texto("Pie de la captura", 13.0, 53.6, [(76.32, "Caso GTA¦6: compras concentradas en el primer mes.")], T_TINY, TENUE, L=2.47)
    numerada(lz, "Pasos de la demostración", 71.91, 76.96, 70.0, [
        (38.47, "Caso ⟨t|GTA¦6⟩ ⟨m@95.4|→⟩ ⟨@99.744|configurar⟩ ⟨m@116.558|→⟩ ⟨@120.902|simular: el pico⟩\nllega en el primer mes."),
        (49.02, "Campaña apagada: la adopción apenas pasa\ndel 7¦¦%."),
        (59.56, "Caso ⟨a|PS5⟩: curva en S frente a la de Bass.")], T_SMALL, L_SMALL)
    nota(lz, "Nota", 71.96, 75.0, [(67.53, "Si sobra tiempo: PS5 sin campaña y ⟨m@123.137|k⟩⟨@124.829| de 16 a 2;⟩\nHerramientas ⟨m@92.103|→⟩ ⟨@96.101|BehaviorSpace.⟩")])

    # 18 · conclusiones ----------------------------------------------------------------------
    s, lz = nueva(prs, contenido, "Conclusiones", "Publicidad primero, red después")
    numerada(lz, "Conclusiones", 12.65, 18.00, 129, [
        (38.24, "PS5: sin campaña, a lo sumo 23,5¦¦%; con campaña, al menos 73,3¦¦%."),
        (44.08, "GTA¦6: un mes de campaña logra el 71¦¦% del efecto."),
        (49.91, "La red pesa sobre todo cuando no hay publicidad."),
        (55.75, "Error en prueba: 4,91 pp; la reimplementación en Python coincide.")])
    nota(lz, "Limitaciones", 13.0, 134, [(65.67, "Limitaciones: coeficientes iguales para todos, red fija, unidades vendidas a tiendas y\nparámetros de GTA¦6 hipotéticos.")])

    # 19 · referencias ------------------------------------------------------------------------
    s, lz = nueva(prs, contenido, "Referencias", "Fuentes")
    refs = [(31.48, "Bass, F.¦M. (1969). A new product growth model for consumer durables. ⟨i|Management Science⟩, 15(5),\n215–227."),
            (39.33, "Goldenberg, J., Libai, B. y Muller, E. (2001). Talk of the network. ⟨i|Marketing Letters⟩, 12(3), 211–223."),
            (43.81, "Rogers, E.¦M. (2003). ⟨i|Diffusion of Innovations⟩ (5.ª ed.). Free Press."),
            (48.28, "Thomas, R.¦J. (1985). Estimating market growth for new products: an analogical diffusion model approach.\n⟨i|Journal of Product Innovation Management⟩, 2(1), 45–55."),
            (56.13, "Watts, D.¦J. y Strogatz, S.¦H. (1998). Collective dynamics of ‘small-world’ networks. ⟨i|Nature⟩, 393, 440–442."),
            (60.60, "Wilensky, U. (1999). NetLogo. Northwestern University."),
            (65.08, "Sony Interactive Entertainment (2026). Business Data & Sales."),
            (69.55, "Take-Two Interactive (2013–2014). Resultados trimestrales, años fiscales 2014 y 2015."),
            (74.02, "Guinness World Records (2013, 2023). Récords de ventas de GTA¦V y de vistas del tráiler de GTA¦6.")]
    lz.texto("Referencias", 13.0, 134, refs, T_SCRIPT, TINTA, L=3.387, marL=3.94, indent=-3.94,
             estilo={"lang": "en-US"})

    # notas del orador
    cif = cifras_tex()
    for slide, nota_tex in zip(prs.slides, notas_tex()):
        poner_nota(slide, nota_a_runs(nota_tex, cif))

    cp = prs.core_properties
    cp.title = "Publicidad y redes sociales en la difusión de innovaciones"
    cp.subject = "Proyecto 14 · Simulación Computacional · PS5 y GTA 6"
    cp.author = "Jesus Gregorio Delgado, David Andres Monroy Aguiar, Duvan Felipe Baquero Cerquera"
    cp.last_modified_by = "Duvan Felipe Baquero Cerquera"
    cp.keywords = "difusión de innovaciones; modelo de Bass; NetLogo; PS5; GTA 6"
    cp.comments = ""
    from datetime import datetime
    cp.created = cp.modified = datetime.now()
    cp.revision = 1
    # fuentes completas al incrustarlas (no solo los caracteres usados), para poder editar en otro equipo
    if "saveSubsetFonts" in prs._element.attrib:
        del prs._element.attrib["saveSubsetFonts"]
    prs.save(SALIDA)
    print("guardado", SALIDA, len(prs.slides), "diapositivas")


def tabla_experimentos(slide, lz):
    """Tabla tipo booktabs: filetes arriba, bajo el encabezado y al final; sin líneas verticales."""
    filas = [("", "factores (E1 a E3 para ambos casos: PS5 y GTA¦6)", "corridas"),
             ("E1", "publicidad {sin, con} ⟨m@50.354|×⟩⟨@52.882| densidad ⟩⟨m@67.433|k⟩⟨@69.126| = 2, 4, 6, 8, 12, 16⟩", "720"),
             ("E2", "publicidad ⟨m@36.563|×⟩⟨@39.091| topología {aleatoria, mundo pequeño, libre de escala}⟩", "360"),
             ("E3", "duración de la campaña {0, 1, 3, 6, 12, 24 meses, permanente}", "420"),
             ("E4", "calibración PS5: 3 topologías ⟨m@62.77|×⟩ ⟨m@66.045|k⟩⟨@67.737| = 4, 8, 16⟩", "270")]
    x0, x1 = 13.0, 135.858
    anchos = [20.96 - 13.0, 122.24 - 20.96, x1 - 122.24]
    L = L_FOOT
    arriba, medio, abajo = 51.569, 57.479, 74.988
    bases = [55.54, 61.39, 65.26, 69.12, 72.99]
    # alto de cada fila y margen superior para que cada línea base caiga donde en el PDF;
    # las filas 2 a 4 empiezan justo en su renglón (sin margen)
    lnspc, H = alto_linea(L, T_FOOT)
    tops = [arriba, medio] + [bases[k] - BASE * H for k in (2, 3, 4)]
    altos = [b - t for t, b in zip(tops, tops[1:] + [abajo])]
    margen_sup = [bases[k] - tops[k] - BASE * H for k in range(5)]
    gf = slide.shapes.add_table(5, 3, Emu(E(x0)), Emu(E(arriba)), Emu(E(x1 - x0)), Emu(E(abajo - arriba)))
    gf.name = "Tabla de experimentos"
    tabla = gf.table
    tbl = tabla._tbl
    tpr = tbl.tblPr
    tpr.set("firstRow", "0")
    tpr.set("bandRow", "0")
    estilo = tpr.find("{http://schemas.openxmlformats.org/drawingml/2006/main}tableStyleId")
    if estilo is None:
        estilo = etree.SubElement(tpr, "{http://schemas.openxmlformats.org/drawingml/2006/main}tableStyleId")
    estilo.text = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"   # sin estilo, sin cuadrícula
    for j, w in enumerate(anchos):
        tabla.columns[j].width = Emu(E(w))
    a = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
    grueso, fino = 0.308, 0.192
    for i, fila in enumerate(filas):
        tabla.rows[i].height = Emu(E(altos[i]))
        for j, texto in enumerate(fila):
            celda = tabla.cell(i, j)
            tc = celda._tc
            for hijo in list(tc):
                tc.remove(hijo)
            base = {"font": REG, "size": T_FOOT, "color": TINTA}
            p = parrafo_xml(texto, base, lnspc, algn="r" if j == 2 else "l", x0=None if j == 2 else x0 + sum(anchos[:j]))
            tc.append(etree.fromstring(f'<a:txBody {NS}><a:bodyPr/><a:lstStyle/>{p}</a:txBody>'))
            bordes = ""
            for lado in ("lnL", "lnR", "lnT", "lnB"):
                ancho = None
                if lado == "lnT" and i == 0:
                    ancho = grueso
                elif lado == "lnB" and i == 0:
                    ancho = fino
                elif lado == "lnT" and i == 1:
                    ancho = fino
                elif lado == "lnB" and i == 4:
                    ancho = grueso
                if ancho:
                    bordes += (f'<a:{lado} w="{int(round(ancho * K * 36000))}" cap="flat" cmpd="sng" algn="ctr">'
                               f'<a:solidFill><a:srgbClr val="{TINTA}"/></a:solidFill><a:prstDash val="solid"/></a:{lado}>')
                else:
                    bordes += f'<a:{lado} w="0"><a:noFill/></a:{lado}>'
            mb = altos[i] - margen_sup[i] - H
            tc.append(etree.fromstring(
                f'<a:tcPr {NS} marL="0" marR="0" marT="{E(margen_sup[i])}" marB="{E(max(0, mb))}" anchor="t">{bordes}<a:noFill/></a:tcPr>'))


if __name__ == "__main__":
    construir()
