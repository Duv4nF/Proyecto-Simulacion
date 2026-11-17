"""Análisis de los experimentos BehaviorSpace: PS5 (tecnología) y GTA 6 (innovación).

Lee las tablas CSV que exporta NetLogo (datos/resultados/*.csv), calcula las medidas
de desempeño por escenario y genera las figuras, tablas y cifras que usan el artículo,
las diapositivas y la guía de estudio:

  analisis/figuras/fig_calibracion.{pdf,png}   ABM y Bass frente a la serie real de PS5
  analisis/figuras/fig_escenarios.{pdf,png}    curvas con y sin campaña (ambos casos) y duración de la campaña
  analisis/figuras/fig_densidad.{pdf,png}      adopción final frente al grado promedio
  analisis/figuras/fig_topologia.{pdf,png}     adopción final por topología
  analisis/figuras/fig_duracion.{pdf,png}      adopción final frente a la duración de la campaña
  articulo/tablas/*.tex                        tablas (booktabs) y cifras.tex (macros \\cifra...)
  analisis/resumen_resultados.json             todas las cifras en un solo archivo

Uso:  python analisis_resultados.py [carpeta_de_resultados]   (por defecto datos/resultados)
"""
import json
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from scipy import stats  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import datos_ps5 as dp  # noqa: E402

RAIZ = dp.RAIZ
RES = RAIZ / "datos" / (sys.argv[1] if len(sys.argv) > 1 and __name__ == "__main__" else "resultados")
FIG = RAIZ / "analisis" / "figuras"
TAB = RAIZ / "articulo" / "tablas"
FIG.mkdir(parents=True, exist_ok=True)
TAB.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------- estilo
TINTA, SECUNDARIO, REJILLA, PAPEL = "#1F2933", "#5E6670", "#E6E3DC", "#FFFFFF"
AZUL, TERRACOTA, CIRUELA, GRIS = "#1E66A8", "#C2502A", "#7B4FA0", "#8C8A85"
ESCALA = 1.0  # factor de tamaño (las diapositivas usan uno mayor)
ALTO = 1.0    # factor adicional de altura
# mismo código que el modelo y las diapositivas: terracota = publicidad, azul = imitación (sin campaña solo hay imitación)
COLOR_CAMPANA = {True: TERRACOTA, False: AZUL}
NOMBRE_CAMPANA = {True: "con campaña", False: "sin campaña"}
ORDEN_TOPO = ["aleatoria", "mundo pequeño", "libre de escala"]
NOMBRE_RED = {"aleatoria": "red aleatoria", "mundo pequeño": "red de mundo pequeño", "libre de escala": "red libre de escala"}
PS5, GTA = "PS5 (tecnología)", "GTA 6 (innovación)"
CASOS = [PS5, GTA]
CORTO = {PS5: "PS5", GTA: "GTA 6"}
MACRO = {PS5: "Ps", GTA: "Gta"}
ESTILO_CASO = {PS5: (TINTA, "o", "-"), GTA: (CIRUELA, "s", (0, (4, 2)))}

# IBM Plex Sans (SIL OFL) viene en analisis/fuentes para que las figuras salgan iguales en cualquier equipo
for ttf in (RAIZ / "analisis" / "fuentes").glob("*.ttf"):
    font_manager.fontManager.addfont(str(ttf))
if any(f.name == "IBM Plex Sans" for f in font_manager.fontManager.ttflist):
    plt.rcParams["font.family"] = "IBM Plex Sans"
plt.rcParams.update({
    "font.size": 9, "axes.titlesize": 9, "axes.labelsize": 9, "legend.fontsize": 8,
    "xtick.labelsize": 8, "ytick.labelsize": 8,
    "axes.edgecolor": REJILLA, "axes.labelcolor": TINTA, "text.color": TINTA,
    "xtick.color": SECUNDARIO, "ytick.color": SECUNDARIO,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": REJILLA, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "legend.frameon": False, "figure.dpi": 150, "savefig.bbox": "tight", "savefig.pad_inches": 0.03,
    "axes.formatter.use_locale": False, "pdf.fonttype": 42, "ps.fonttype": 42,
    "figure.facecolor": PAPEL, "axes.facecolor": PAPEL, "savefig.facecolor": PAPEL,
})


def coma(x, dec=1):
    """Formato numérico con coma decimal (texto en español)."""
    return f"{x:.{dec}f}".replace(".", ",")


def guardar(fig, nombre):
    fig.savefig(FIG / f"{nombre}.pdf")
    fig.savefig(FIG / f"{nombre}.png", dpi=300)
    plt.close(fig)


def titulo_panel(eje, texto, **kw):
    eje.set_title(texto, loc="left", color=SECUNDARIO, fontsize=kw.pop("fontsize", plt.rcParams["axes.titlesize"]), **kw)


# ----------------------------------------------------------------- lectura y medidas
def leer(nombre, carpeta=None):
    """Tabla BehaviorSpace: seis líneas de encabezado y luego la tabla."""
    df = pd.read_csv((carpeta or RES) / f"{nombre}.csv", skiprows=6, low_memory=False)
    df = df.rename(columns={"[run number]": "corrida", "[step]": "mes"})
    for col in ("campaña?", "dibujar-red?"):
        if col in df and df[col].dtype == object:
            df[col] = df[col].map({"true": True, "false": False})
    for col in ("tipo-red", "caso"):
        if col in df:
            df[col] = df[col].astype(str).str.strip('"')
    if "camino-medio" in df:
        df["camino-medio"] = pd.to_numeric(df["camino-medio"], errors="coerce")
    return df


def ic95(x):
    """Semiancho del intervalo de confianza del 95 % para la media (t de Student)."""
    x = np.asarray(x, dtype=float)
    if len(x) < 2:
        return 0.0
    return float(stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x)))


def finales(df, factores):
    """Una fila por corrida con el estado al último mes (el horizonte de su caso)."""
    ult = df.loc[df.groupby("corrida")["mes"].idxmax()].copy()
    ult["alcanza-50"] = ult["mes-50"] >= 0
    ult.loc[~ult["alcanza-50"], "mes-50"] = np.nan
    return ult[["corrida", *factores, "mes", "porcentaje-adopcion", "mes-50", "alcanza-50", "pico-nuevos", "mes-pico"]]


def resumen(ult, factores):
    g = ult.groupby(factores)
    out = g["porcentaje-adopcion"].agg(media="mean", ic=ic95, de="std", n="count")
    out["horizonte"] = g["mes"].max()
    out["t50_mediana"] = g["mes-50"].median()
    out["prop_alcanza_50"] = g["alcanza-50"].mean()
    out["pico_media"] = g["pico-nuevos"].mean()
    out["mes_pico_mediana"] = g["mes-pico"].median()
    return out.reset_index()


def curva_media(df, factores):
    g = df.groupby([*factores, "mes"])["porcentaje-adopcion"]
    return g.agg(media="mean", ic=ic95).reset_index()


EXPERIMENTOS = {
    "publicidad_x_densidad": ["caso", "campaña?", "grado-promedio"],
    "topologia_x_publicidad": ["caso", "campaña?", "tipo-red"],
    "duracion_campana": ["caso", "duracion-campaña"],
    "calibracion_ps5": ["tipo-red", "grado-promedio"],
}


def comparar_implementaciones(alfa=0.05):
    """Verificación: adopción final de cada escenario en NetLogo (datos/resultados) frente a la réplica
    independiente en Python (datos/resultados_python), con la prueba t de Welch y la corrección de Holm.
    Devuelve None si falta alguna de las dos carpetas o si algún experimento no está completo en ambas
    (mismo número de corridas por escenario): así una corrida a medias nunca llega a las cifras."""
    carpetas = [RAIZ / "datos" / c for c in ("resultados", "resultados_python")]
    if not all((c / f"{n}.csv").exists() for c in carpetas for n in EXPERIMENTOS):
        return None
    difs, pvals = [], []
    for nombre, factores in EXPERIMENTOS.items():
        nl, py = (leer(nombre, c) for c in carpetas)
        nl, py = (d.loc[d.groupby("corrida")["mes"].idxmax()] for d in (nl, py))
        tam_nl, tam_py = nl.groupby(factores).size(), py.groupby(factores).size()
        if len(tam_nl) != len(tam_py) or tam_nl.min() < tam_py.max():
            print(f"verificación omitida: {nombre} incompleto en NetLogo ({tam_nl.min()} de {tam_py.max()} corridas)")
            return None
        grupos_py = dict(tuple(py.groupby(factores)))
        for clave, a in nl.groupby(factores):
            a, b = a["porcentaje-adopcion"], grupos_py[clave]["porcentaje-adopcion"]
            difs.append(a.mean() - b.mean())
            p = stats.ttest_ind(a, b, equal_var=False).pvalue
            pvals.append(1.0 if np.isnan(p) else p)   # varianza nula en ambos grupos y medias iguales
    difs, pvals = np.abs(np.array(difs)), np.array(pvals)
    n = len(pvals)
    holm = np.minimum(1, np.maximum.accumulate(np.sort(pvals) * (n - np.arange(n))))
    return {"escenarios": n, "dif_media": float(difs.mean()), "dif_max": float(difs.max()),
            "significativas": int((pvals < alfa).sum()), "significativas_holm": int((holm < alfa).sum())}


# ----------------------------------------------------------------- figuras
def _curvas_caso(eje, cur, caso, ks=(4, 16), etiquetas=True):
    for camp in (True, False):
        for k, estilo in ((max(ks), "-"), (min(ks), (0, (4, 2)))):
            c = cur[(cur["caso"] == caso) & (cur["campaña?"] == camp) & (cur["grado-promedio"] == k)]
            eje.fill_between(c["mes"], c["media"] - c["ic"], c["media"] + c["ic"], color=COLOR_CAMPANA[camp], alpha=0.16, lw=0)
            eje.plot(c["mes"], c["media"], ls=estilo, color=COLOR_CAMPANA[camp], lw=1.5, label=f"{NOMBRE_CAMPANA[camp]}, k = {k}")


def fig_escenarios(e1, r3):
    """Figura del artículo: (a) PS5 y (b) GTA 6 con y sin campaña en redes dispersa y densa; (c) duración de la campaña."""
    cur = curva_media(e1[e1["grado-promedio"].isin([2, 16])], ["caso", "campaña?", "grado-promedio"])
    # tamaño cercano al final en el artículo (ancho de texto LNCS ~ 4,8 in): la letra queda en ~7 pt
    fig, ejes = plt.subplots(1, 3, figsize=(6.0 * ESCALA, 2.12 * ESCALA * ALTO), gridspec_kw={"width_ratios": [1.25, 1.0, 1.05]})
    for eje, caso, letra in ((ejes[0], PS5, "(a)"), (ejes[1], GTA, "(b)")):
        _curvas_caso(eje, cur, caso, ks=(2, 16))
        horizonte = int(cur[cur["caso"] == caso]["mes"].max())
        titulo_panel(eje, f"{letra} {CORTO[caso]}", fontsize=8)
        eje.set_xlabel("meses desde el lanzamiento")
        eje.set_ylabel("adopción acumulada (%)", fontsize=8)
        eje.set_xlim(0, horizonte)
        eje.set_xticks(range(0, horizonte + 1, 12 if horizonte > 30 else 6))
    ejes[0].set_ylim(0, 100)
    ejes[1].set_ylim(0, 25)
    ejes[0].legend(loc="upper left", handlelength=2.0, fontsize=6.6, labelspacing=0.3,
                   frameon=True, facecolor=PAPEL, edgecolor="none", framealpha=0.92)
    dibujar_fraccion(ejes[2], r3, ms=3.5)
    titulo_panel(ejes[2], "(c) duración de la campaña", fontsize=8)
    ejes[2].set_ylabel("% del efecto permanente", fontsize=8)
    ejes[2].legend(loc="lower right", fontsize=7)
    fig.subplots_adjust(wspace=0.55)
    guardar(fig, "fig_escenarios")


def fraccion_efecto(r3, caso):
    """(A_d - A_0) / (A_perm - A_0) en %, para d = 0, 1, 3, 6, 12, 24 meses."""
    r = r3[r3["caso"] == caso].set_index("duracion-campaña").sort_index()
    base, perm = r.loc[0, "media"], r.loc[240, "media"]
    r = r.drop(index=240)
    return r.index.values, 100 * (r["media"].values - base) / (perm - base)


def dibujar_fraccion(eje, r3, ms=4, etiquetas=False):
    """Duraciones a distancias iguales y la campaña permanente como referencia (100 %)."""
    eje.axhline(100, color=GRIS, lw=1, ls=(0, (4, 2)))
    eje.annotate("campaña permanente", (0, 100), xytext=(0, 3), textcoords="offset points", fontsize=6.5, color=SECUNDARIO)
    for caso in CASOS:
        meses, frac = fraccion_efecto(r3, caso)
        color, marcador, estilo = ESTILO_CASO[caso]
        eje.plot(np.arange(len(meses)), frac, color=color, marker=marcador, ms=ms, ls=estilo, lw=1.4, label=CORTO[caso])
        if etiquetas:
            eje.annotate(CORTO[caso], (1, frac[1]), xytext=(8, -7 if caso == PS5 else 2), textcoords="offset points",
                         fontsize=8, color=color, va="center")
    eje.set_xticks(np.arange(6))
    eje.set_xticklabels(["0", "1", "3", "6", "12", "24"])
    eje.set_xlabel("meses de campaña")
    eje.set_ylim(-3, 112)


def fig_curvas(e1, caso, nombre):
    """Curvas de adopción de un caso (diapositivas)."""
    cur = curva_media(e1[e1["grado-promedio"].isin([4, 16])], ["caso", "campaña?", "grado-promedio"])
    fig, eje = plt.subplots(figsize=(6.4 * ESCALA, 3.2 * ESCALA * ALTO))
    _curvas_caso(eje, cur, caso)
    horizonte = int(cur[cur["caso"] == caso]["mes"].max())
    eje.set_xlim(0, horizonte)
    eje.set_xticks(range(0, horizonte + 1, 12 if horizonte > 30 else 6))
    eje.set_ylim(0, 100 if caso == PS5 else 25)
    eje.set_xlabel("meses desde el lanzamiento")
    eje.set_ylabel("adopción (%)")
    eje.legend(loc="upper left", ncol=2 if caso == GTA else 1, handlelength=2.0)
    guardar(fig, nombre)


def fig_densidad(r1):
    """Adopción final frente al grado promedio, con y sin campaña, por caso."""
    fig, ejes = plt.subplots(1, 2, figsize=(6.6 * ESCALA, 2.5 * ESCALA * ALTO))
    for eje, caso in zip(ejes, CASOS):
        for camp in (True, False):
            r = r1[(r1["caso"] == caso) & (r1["campaña?"] == camp)].sort_values("grado-promedio")
            eje.errorbar(r["grado-promedio"], r["media"], yerr=r["ic"], color=COLOR_CAMPANA[camp], lw=1.5,
                         marker="o", ms=4, capsize=2.5, label=NOMBRE_CAMPANA[camp])
            eje.annotate(NOMBRE_CAMPANA[camp], (r["grado-promedio"].iloc[-1], r["media"].iloc[-1]),
                         xytext=(6, 0), textcoords="offset points", fontsize=7.5, color=SECUNDARIO, va="center")
        horizonte = int(r1[r1["caso"] == caso]["horizonte"].max())
        titulo_panel(eje, f"{CORTO[caso]} (adopción a {horizonte} meses)")
        eje.set_xlabel("grado promedio de la red (k)")
        eje.set_xticks([2, 4, 6, 8, 12, 16])
        eje.set_xlim(1, 22)
        eje.set_ylim(0, 100 if caso == PS5 else 25)
    ejes[0].set_ylabel("adopción final (%)")
    guardar(fig, "fig_densidad")


def fig_topologia(r2):
    """Adopción final por topología (k = 16), con y sin campaña, por caso."""
    fig, ejes = plt.subplots(1, 2, figsize=(6.6 * ESCALA, 2.3 * ESCALA * ALTO), sharey=True)
    y = np.arange(len(ORDEN_TOPO))
    for eje, caso in zip(ejes, CASOS):
        for camp, dy in ((False, 0.15), (True, -0.15)):
            r = r2[(r2["caso"] == caso) & (r2["campaña?"] == camp)].set_index("tipo-red").loc[ORDEN_TOPO]
            eje.errorbar(r["media"], y + dy, xerr=r["ic"], fmt="o", ms=5, color=COLOR_CAMPANA[camp],
                         capsize=2.5, lw=1.4, label=NOMBRE_CAMPANA[camp])
            for yi, v in zip(y + dy, r["media"]):
                eje.annotate(coma(v), (v, yi), xytext=(6, 0), textcoords="offset points", fontsize=7.5, va="center", color=TINTA)
        horizonte = int(r2[r2["caso"] == caso]["horizonte"].max())
        eje.set_yticks(y)
        eje.set_yticklabels(ORDEN_TOPO)
        eje.set_xlim(0, 100 if caso == PS5 else 25)
        eje.set_xlabel(f"adopción final a {horizonte} meses (%)")
        titulo_panel(eje, CORTO[caso])
        eje.grid(axis="y", visible=False)
    ejes[0].invert_yaxis()
    manijas, etiquetas = ejes[1].get_legend_handles_labels()
    fig.legend(manijas, etiquetas, loc="lower center", bbox_to_anchor=(0.5, -0.12 - 0.2 * (ESCALA - 1)), ncol=2)
    guardar(fig, "fig_topologia")


def fig_duracion(r3):
    """Adopción final frente a la duración de la campaña, por caso (dos paneles, escalas propias)."""
    fig, ejes = plt.subplots(1, 2, figsize=(6.6 * ESCALA, 2.5 * ESCALA * ALTO))
    posiciones = np.arange(7)
    for eje, caso in zip(ejes, CASOS):
        r = r3[r3["caso"] == caso].sort_values("duracion-campaña")
        color, marcador, estilo = ESTILO_CASO[caso]
        eje.errorbar(posiciones, r["media"], yerr=r["ic"], color=color, marker=marcador, ms=4.5, ls=estilo, lw=1.5, capsize=2.5)
        horizonte = int(r["horizonte"].max())
        titulo_panel(eje, f"{CORTO[caso]} (adopción a {horizonte} meses)")
        eje.set_xticks(posiciones)
        eje.set_xticklabels(["0", "1", "3", "6", "12", "24", "perm."])
        eje.set_xlabel("meses de campaña")
        eje.set_ylim(0, 100 if caso == PS5 else 25)
    ejes[0].set_ylabel("adopción final (%)")
    guardar(fig, "fig_duracion")


def fig_calibracion(df, datos, parametros, seleccion, ancho=4.9, alto=1.95, diapositiva=False):
    """Serie real de PS5 por partición, curva de Bass ajustada y ABM con la estructura seleccionada.
    Se dibuja cerca de su tamaño final (artículo: 0,8 del ancho de texto). En la versión para diapositiva
    el control de Sony va en la leyenda en lugar de rotulado sobre la figura."""
    p, q, m = (parametros["anual"][k] for k in "pqm")
    fig, eje = plt.subplots(figsize=(ancho, alto))
    limite = pd.Timestamp("2027-01-31")
    for nombre, (a, b) in dp.PARTICION.items():
        a = dp.LANZAMIENTO if nombre == "entrenamiento" else pd.Timestamp(a) - pd.Timedelta(days=45)
        b = limite if nombre == "prueba" else pd.Timestamp(b) + pd.Timedelta(days=45)
        if nombre != "entrenamiento":
            eje.axvspan(a, b, color=REJILLA, alpha=0.5, lw=0)
        if nombre == "prueba" and not diapositiva:  # alineada a la izquierda para no chocar con la anotación del control
            eje.text(a + pd.Timedelta(days=20), 98, dp.NOMBRE_PARTICION[nombre], ha="left", va="top", fontsize=7.5, color=SECUNDARIO)
        else:
            eje.text(a + (b - a) / 2, 98, dp.NOMBRE_PARTICION[nombre], ha="center", va="top", fontsize=7.5, color=SECUNDARIO)
    fechas = pd.date_range(dp.LANZAMIENTO, limite, freq="7D")
    t = np.asarray((fechas - dp.LANZAMIENTO).days / 365.25)
    e = np.exp(-(p + q) * t)
    eje.plot(fechas, 100 * m * (1 - e) / (1 + (q / p) * e), color=GRIS, lw=1.4, ls=(0, (4, 2)), label="Bass (agregado)" if diapositiva else "modelo agregado de Bass")
    sel = df[(df["tipo-red"] == seleccion["tipo-red"]) & (df["grado-promedio"] == seleccion["grado-promedio"])]
    c = curva_media(sel, []).sort_values("mes")
    x = dp.LANZAMIENTO + pd.to_timedelta(c["mes"] * dp.DIAS_MES, unit="D")
    eje.fill_between(x, c["media"] - c["ic"], c["media"] + c["ic"], color=AZUL, alpha=0.18, lw=0)
    red = NOMBRE_RED[seleccion['tipo-red']]
    if diapositiva:  # etiqueta corta: la leyenda va dentro del eje, en la zona sin datos
        red = red.replace("red de ", "").replace("red ", "")
    eje.plot(x, c["media"], color=AZUL, lw=1.8,
             label=f"{'agentes' if diapositiva else 'modelo de agentes'} ({red}, k = {seleccion['grado-promedio']})")
    marcas = {"entrenamiento": ("o", "full"), "validacion": ("s", "none"), "prueba": ("^", "none")}
    for nombre, (mk, relleno) in marcas.items():
        d = dp.subconjunto(datos, nombre)
        eje.plot(d.fecha_cierre, d.adopcion_pct, mk, ms=4.3, color=TINTA, fillstyle=relleno, mew=1.1, ls="none",
                 label=f"Sony: {dp.NOMBRE_PARTICION[nombre]}")
    control = 100 * dp.CONTROL["minimo_M"] / dp.UNIVERSO_M
    eje.plot(dp.CONTROL["fecha"], control, marker="_", ms=10, mew=1.8, color=TERRACOTA, ls="none",
             label="Sony: más de 100 M (nov. 2026)" if diapositiva else None)
    if not diapositiva:
        eje.annotate("más de 100 M\n(10-nov-2026)", (dp.CONTROL["fecha"], control), xytext=(14, 7), textcoords="offset points",
                     ha="right", va="bottom", fontsize=6.6, color=SECUNDARIO)
    eje.set_xlim(dp.LANZAMIENTO, limite)
    eje.set_ylim(0, 100)
    eje.xaxis.set_major_locator(mdates.YearLocator())
    eje.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    eje.set_ylabel(f"PS5 vendidas (% de la base\nde PS4: {coma(dp.UNIVERSO_M, 0)} millones)")
    if diapositiva:
        # abajo a la derecha: bajo las curvas no hay datos desde 2024
        eje.legend(loc="lower right", bbox_to_anchor=(1.0, 0.0), ncol=1, frameon=False, fontsize=6.3, handlelength=1.6,
                   labelspacing=0.25)
    else:
        # leyenda debajo del eje, en dos columnas: no tapa ningún dato
        eje.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2, frameon=False, fontsize=6.8,
                   columnspacing=1.6, handlelength=1.8)
    guardar(fig, "fig_calibracion")


# ----------------------------------------------------------------- tablas y cifras
def tabla_latex(nombre, encabezado, filas, caption, label, alineacion, pequena=False):
    cuerpo = " \\\\\n".join(" & ".join(f) for f in filas)
    texto = (
        "\\begin{table}[htb]\n\\centering\n"
        f"\\caption{{{caption}}}\n\\label{{{label}}}\n" + ("\\small\n" if pequena else "")
        + ("\\setlength{\\tabcolsep}{4pt}\n" if pequena else "") + f"\\begin{{tabular}}{{{alineacion}}}\n\\toprule\n"
        + " & ".join(encabezado) + " \\\\\n\\midrule\n" + cuerpo + " \\\\\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    )
    (TAB / f"{nombre}.tex").write_text(texto, encoding="utf-8")


PALABRA = {0: "Cero", 1: "Uno", 2: "Dos", 3: "Tres", 4: "Cuatro", 6: "Seis", 8: "Ocho", 12: "Doce", 16: "Dieciseis",
           24: "Veinticuatro", 240: "Permanente"}
TOPO_MACRO = {"aleatoria": "Aleatoria", "mundo pequeño": "Mundo", "libre de escala": "Escala"}


MESES_ES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def tabla_datos(datos):
    """Ejemplos de la serie real (diciembre de años alternos, diciembre de 2025 y el último), para la sección de datos."""
    filas = []
    diciembre = datos["fecha_cierre"].dt.month == 12
    anio = datos["fecha_cierre"].dt.year
    elegidos = datos[(diciembre & ((anio % 2 == 0) | (anio == 2025))) | (datos.index == datos.index[-1])]
    for _, r in elegidos.iterrows():
        f = r["fecha_cierre"]
        filas.append([r["trimestre_fiscal"].replace(" ", "~"), f"{f.day}-{MESES_ES[f.month - 1]}-{f.year}",
                      coma(r["unidades_trimestre_M"]), coma(r["unidades_acumuladas_M"]), coma(r["adopcion_pct"]),
                      dp.NOMBRE_PARTICION[r["particion"]]])
    tabla_latex("tabla_datos", ["trimestre", "cierre", "unidades", "acumulado", "\\% base PS4", "partición"], filas,
                f"Cinco de los {len(datos)} trimestres de la serie real: unidades de PS5 vendidas a tiendas (millones), acumulado "
                f"y porcentaje de la base de PS4 ({coma(dp.UNIVERSO_M, 0)} M).",
                "tab:datos", "llrrrl", pequena=True)


def escribir_cifras(m):
    # coma decimal entre llaves: en modo matemático evita el espacio de puntuación ("0, 69"); en texto no cambia nada
    lineas = [f"\\newcommand{{\\cifra{k}}}{{{re.sub(r'(\d),(\d)', r'\1{,}\2', v)}}}" for k, v in m.items()]
    (TAB / "cifras.tex").write_text("% generado por analisis/analisis_resultados.py: no editar a mano\n" + "\n".join(lineas) + "\n",
                                    encoding="utf-8")


def cifras_calibracion(m, parametros, datos, errores, seleccion, control_abm):
    an, me = parametros["anual"], parametros["mensual"]
    m["BassP"], m["BassQ"], m["BassM"] = coma(an["p"], 3), coma(an["q"], 3), coma(100 * an["m"], 0)
    m["BassPmes"], m["BassQmes"] = coma(round(me["p"], 4), 4), coma(round(me["q"], 4), 4)
    m["BassRazonQP"] = coma(an["q"] / an["p"], 1)
    m["BassPico"] = coma(parametros["tiempo_pico_anios"], 1)
    m["BassMLibre"] = coma(100 * parametros["ajuste_libre_toda_la_serie"]["m"], 0)
    m["BassMLibreM"] = coma(dp.UNIVERSO_M * parametros["ajuste_libre_toda_la_serie"]["m"], 0)
    for part, abrev in (("entrenamiento", "Ent"), ("validacion", "Val"), ("prueba", "Pru")):
        m[f"BassRmse{abrev}"] = coma(parametros["desempeno_bass"][part]["RMSE_pct"], 2)
        m[f"BassMape{abrev}"] = coma(parametros["desempeno_bass"][part]["MAPE_pct"], 1)
        m[f"Obs{abrev}"] = str(parametros["n_observaciones"][part])
    m["Universo"] = coma(dp.UNIVERSO_M, 0)
    m["Trimestres"] = str(len(datos))
    m["PsUnidadesIni"], m["PsUnidadesFin"] = coma(datos["unidades_acumuladas_M"].iloc[0]), coma(datos["unidades_acumuladas_M"].iloc[-1])
    m["PsPctFin"] = coma(datos["adopcion_pct"].iloc[-1])
    m["ControlReal"] = coma(parametros["control"]["real_minimo_pct"])
    m["ControlBass"] = coma(parametros["control"]["bass_pct"])
    m["ControlAbm"] = coma(control_abm)
    sel = errores[(errores["tipo-red"] == seleccion["tipo-red"]) & (errores["grado-promedio"] == seleccion["grado-promedio"])].iloc[0]
    m["AbmSelRed"], m["AbmSelK"] = seleccion["tipo-red"], str(seleccion["grado-promedio"])
    for part, abrev in (("entrenamiento", "Ent"), ("validacion", "Val"), ("prueba", "Pru")):
        m[f"AbmRmse{abrev}"] = coma(sel[f"rmse_{part}"], 2)
        m[f"AbmMape{abrev}"] = coma(sel[f"mape_{part}"], 1)
    peor = errores.sort_values("rmse_validacion").iloc[-1]
    m["AbmPeorRed"], m["AbmPeorK"] = peor["tipo-red"], str(int(peor["grado-promedio"]))
    m["AbmRmseValMax"], m["AbmRmsePruMax"] = coma(peor["rmse_validacion"], 2), coma(peor["rmse_prueba"], 2)
    segunda = errores.sort_values("rmse_validacion").iloc[1]
    m["AbmSegundaRed"], m["AbmSegundaK"] = segunda["tipo-red"], str(int(segunda["grado-promedio"]))
    m["AbmSegundaRmseVal"] = coma(segunda["rmse_validacion"], 2)
    # nombres con concordancia para el texto: "la red de mundo pequeño", "la red aleatoria"
    m["AbmSelRedNombre"] = NOMBRE_RED[seleccion["tipo-red"]]
    m["AbmPeorRedNombre"] = NOMBRE_RED[peor["tipo-red"]]
    m["AbmSegundaRedNombre"] = NOMBRE_RED[segunda["tipo-red"]]


def cifras_gta(m, gta):
    a, g = gta["ajuste"], gta["gta6"]
    m["GtaP"] = coma(g["p_mes"], 2)
    m["GtaQ"] = coma(g["q_mes"][0], 4)
    m["GtaM"] = str(g["potencial_mercado_pct"])
    m["GtaIniciales"] = str(g["adoptantes_iniciales_pct"])
    m["GtaHorizonte"] = str(g["horizonte_meses"])
    m["GtaRmse"] = coma(a["rmse_pp"], 2)
    m["GtaBase"] = coma(sum(gta["base_instalada_M"].values()), 0)
    m["GtaRazonPQ"] = coma(g["p_mes"] / g["q_mes"][0], 0)
    obs = {o["fecha"]: o for o in gta["observaciones"]}
    m["GtavDiaUno"] = coma(obs["2013-09-17"]["unidades_M"], 2)
    m["GtavSeisSemanas"] = coma(obs["2013-10-29"]["unidades_M"], 0)
    m["GtavMeseta"] = coma(max(o["unidades_M"] for o in gta["observaciones"]), 0)
    m["GtavMesetaPct"] = coma(100 * a["m"], 1)
    valores = [coma(o["unidades_M"]) for o in sorted(gta["observaciones"], key=lambda o: o["fecha"])]
    m["GtavSerie"] = "; ".join(valores[:-1]) + " y " + valores[-1]


def main():
    parametros = json.loads((RAIZ / "analisis" / "parametros_calibrados.json").read_text(encoding="utf-8"))
    gta = json.loads((RAIZ / "analisis" / "parametros_gta6.json").read_text(encoding="utf-8"))
    datos = dp.cargar()
    cifras, m = {}, {}

    # ---- E1: publicidad × densidad (ambos casos)
    e1 = leer("publicidad_x_densidad")
    f1 = ["caso", "campaña?", "grado-promedio"]
    r1 = resumen(finales(e1, f1), f1)
    fig_densidad(r1)
    filas = []
    for k in sorted(r1["grado-promedio"].unique()):
        fila = [str(k)]
        for caso in CASOS:
            for camp in (False, True):
                r = r1[(r1["caso"] == caso) & (r1["grado-promedio"] == k) & (r1["campaña?"] == camp)].iloc[0]
                fila.append(f"{coma(r['media'])} $\\pm$ {coma(r['ic'])}")
        filas.append(fila)
    tabla_latex("tabla_densidad", ["$k$", "PS5 sin", "PS5 con", "GTA 6 sin", "GTA 6 con"], filas,
                "Adopción final (\\%, media $\\pm$ IC 95\\,\\%, 30 réplicas) sin y con campaña según el grado promedio $k$ de la red "
                "de mundo pequeño: PS5 a 72 meses y GTA 6 a 24 meses.",
                "tab:densidad", "lrrrr", pequena=True)
    for _, r in r1.iterrows():
        clave = f"{MACRO[r['caso']]}{'Con' if r['campaña?'] else 'Sin'}K{PALABRA[int(r['grado-promedio'])]}"
        m[clave], m[clave + "Ic"] = coma(r["media"]), coma(r["ic"])
        m["Tcincuenta" + clave] = "--" if r["prop_alcanza_50"] < 0.5 else coma(r["t50_mediana"], 0)
        m["MesPico" + clave] = coma(r["mes_pico_mediana"], 0)
    for (caso, camp), g in r1.groupby(["caso", "campaña?"]):
        clave = f"{MACRO[caso]}{'Con' if camp else 'Sin'}"
        m[clave + "Min"], m[clave + "Max"] = coma(g["media"].min()), coma(g["media"].max())
        s = g.set_index("grado-promedio")["media"]
        m[clave + "Razon"] = coma(s[16] / s[2], 1)
        m[clave + "Ganancia"] = coma(s[16] - s[2], 1)
    for caso in CASOS:
        m[f"Horizonte{MACRO[caso]}"] = str(int(r1[r1["caso"] == caso]["horizonte"].max()))
    cifras["densidad"] = r1.to_dict(orient="records")

    # ---- E2: topología × publicidad (k = 16)
    e2 = leer("topologia_x_publicidad")
    f2 = ["caso", "campaña?", "tipo-red"]
    r2 = resumen(finales(e2, f2), f2)
    fig_topologia(r2)
    est = e2.loc[e2.groupby("corrida")["mes"].idxmax()].groupby("tipo-red")[["grado-medio", "agrupamiento", "camino-medio"]].mean()
    for _, r in r2.iterrows():
        clave = f"Topo{MACRO[r['caso']]}{'Con' if r['campaña?'] else 'Sin'}{TOPO_MACRO[r['tipo-red']]}"
        m[clave], m[clave + "Ic"], m[clave + "De"] = coma(r["media"]), coma(r["ic"]), coma(r["de"])
    for (caso, camp), g in r2.groupby(["caso", "campaña?"]):
        clave = f"Topo{MACRO[caso]}{'Con' if camp else 'Sin'}"
        m[clave + "Min"], m[clave + "Max"] = coma(g["media"].min()), coma(g["media"].max())
    for topo, fila in est.iterrows():
        m[f"Est{TOPO_MACRO[topo]}C"] = coma(fila["agrupamiento"], 3)
        m[f"Est{TOPO_MACRO[topo]}L"] = coma(fila["camino-medio"], 2) if not np.isnan(fila["camino-medio"]) else "no conexa"
    cifras["topologia"] = r2.to_dict(orient="records")
    cifras["estructura"] = est.reset_index().to_dict(orient="records")

    # ---- E3: duración de la campaña
    e3 = leer("duracion_campana")
    f3 = ["caso", "duracion-campaña"]
    r3 = resumen(finales(e3, f3), f3)
    fig_duracion(r3)
    fig_escenarios(e1, r3)
    dur = r3.set_index(["caso", "duracion-campaña"])["media"]
    for _, r in r3.iterrows():
        clave = f"Dur{MACRO[r['caso']]}D{PALABRA[int(r['duracion-campaña'])]}"
        m[clave], m[clave + "Ic"] = coma(r["media"]), coma(r["ic"])
    for caso in CASOS:
        base, perm = dur[(caso, 0)], dur[(caso, 240)]
        for d in (1, 3, 6, 12, 24):
            m[f"Fraccion{MACRO[caso]}D{PALABRA[d]}"] = coma(100 * (dur[(caso, d)] - base) / (perm - base), 0)
    # máximo de la PS5 sin campaña en todos los experimentos (E1, E2 y E3 sin campaña): el "como máximo" del texto
    sin_ps5 = [r1[(r1["caso"] == PS5) & ~r1["campaña?"]]["media"].max(), r2[(r2["caso"] == PS5) & ~r2["campaña?"]]["media"].max(),
               dur[(PS5, 0)]]
    m["PsSinMaxGlobal"] = coma(max(sin_ps5))
    cifras["duracion"] = r3.to_dict(orient="records")

    # ---- E4: calibración frente a la serie real de PS5
    e4 = leer("calibracion_ps5")

    def errores_particion(curva, nombre):
        d = dp.subconjunto(datos, nombre)
        yhat = np.interp(d.t_meses, curva["mes"], curva["media"])
        return (float(np.sqrt(np.mean((d.adopcion_pct - yhat) ** 2))),
                float(np.mean(np.abs((d.adopcion_pct - yhat) / d.adopcion_pct)) * 100))

    errores, curvas = [], {}
    for topo in ORDEN_TOPO:
        for k in sorted(e4["grado-promedio"].unique()):
            sub = e4[(e4["tipo-red"] == topo) & (e4["grado-promedio"] == k)]
            c = curva_media(sub, []).sort_values("mes")
            curvas[(topo, int(k))] = c
            err = {n: errores_particion(c, n) for n in dp.PARTICION}
            errores.append({"tipo-red": topo, "grado-promedio": int(k), **{f"rmse_{n}": e[0] for n, e in err.items()},
                            **{f"mape_{n}": e[1] for n, e in err.items()}})
    errores = pd.DataFrame(errores)
    sel = errores.sort_values("rmse_validacion").iloc[0]
    seleccion = {"tipo-red": sel["tipo-red"], "grado-promedio": int(sel["grado-promedio"])}
    c_sel = curvas[(seleccion["tipo-red"], seleccion["grado-promedio"])]
    t_ctrl = (dp.CONTROL["fecha"] - dp.LANZAMIENTO).days / dp.DIAS_MES
    control_abm = float(np.interp(t_ctrl, c_sel["mes"], c_sel["media"]))
    fig_calibracion(e4, datos, parametros, seleccion)
    bass = parametros["desempeno_bass"]
    filas_cal = []
    ks = sorted(int(k) for k in errores["grado-promedio"].unique())
    for topo in ORDEN_TOPO:
        fila = [topo]
        for k in ks:
            r = errores[(errores["tipo-red"] == topo) & (errores["grado-promedio"] == k)].iloc[0]
            marca = "$^\\star$" if (topo == seleccion["tipo-red"] and k == seleccion["grado-promedio"]) else ""
            fila.append(f"{coma(r['rmse_validacion'], 2)} / {coma(r['rmse_prueba'], 2)}{marca}")
        filas_cal.append(fila)
    tabla_latex("tabla_calibracion", ["red", *[f"$k={k}$" for k in ks]], filas_cal,
                "RMSE (puntos) del modelo de agentes en validación / prueba, por topología y $k$; $\\star$: elegida en validación. "
                f"Bass: {coma(bass['validacion']['RMSE_pct'], 2)} / {coma(bass['prueba']['RMSE_pct'], 2)}.",
                "tab:calibracion", "lrrr", pequena=True)
    cifras_calibracion(m, parametros, datos, errores, seleccion, control_abm)
    cifras_gta(m, gta)
    tabla_datos(datos)
    cifras["calibracion"] = {"errores": errores.to_dict(orient="records"), "seleccion": seleccion, "bass": bass,
                             "control_abm_pct": control_abm}

    # ---- tamaño de los datos generados
    corridas = filas_tot = 0
    for nombre in EXPERIMENTOS:
        df = leer(nombre)
        corridas += df["corrida"].nunique()
        filas_tot += len(df)
    m["Corridas"], m["Filas"] = str(corridas), f"{filas_tot:,}".replace(",", "\\,")
    cifras["datos_generados"] = {"corridas": corridas, "filas": filas_tot}

    # ---- verificación: NetLogo frente a la réplica en Python
    verif = comparar_implementaciones()
    cifras["verificacion"] = verif
    if verif:
        h = verif["significativas_holm"]
        m["VerifEscenarios"] = str(verif["escenarios"])
        m["VerifDifMedia"], m["VerifDifMax"] = coma(verif["dif_media"], 2), coma(verif["dif_max"], 1)
        m["VerifSignif"] = str(verif["significativas"])
        m["VerifHolm"] = ("ninguna diferencia es significativa" if h == 0 else
                          "una diferencia es significativa" if h == 1 else f"{h} diferencias son significativas")
    else:
        for k in ("VerifEscenarios", "VerifDifMedia", "VerifDifMax", "VerifSignif", "VerifHolm"):
            m[k] = "--"

    # ---- verificación analítica: red completa frente a Bass (analisis/verificacion_python.py)
    vb = RAIZ / "analisis" / "verificacion_bass.json"
    if vb.exists():
        v = json.loads(vb.read_text(encoding="utf-8"))
        m["VerifBassMax"] = coma(max(x["diferencia_maxima_pp"] for x in v.values()), 1)
        cifras["verificacion_bass"] = v

    # ---- análisis de sensibilidad (analisis/sensibilidad.py)
    sens = RAIZ / "analisis" / "sensibilidad.json"
    if sens.exists():
        s = json.loads(sens.read_text(encoding="utf-8"))
        d = s["gta_doble"]
        m["SensDobleM"], m["SensDobleIniciales"] = str(d["potencial_pct"]), str(d["iniciales_pct"])
        m["SensDobleSin"], m["SensDobleCon"] = coma(d["sin_k16"]), coma(d["con_k16"])
        m["SensDobleFraccion"] = coma(d["fraccion_un_mes"], 0)
        m["SensQdobleSin"], m["SensQdobleCon"] = coma(s["gta_q_doble"]["sin_k16"]), coma(s["gta_q_doble"]["con_k16"])
        for semilla, nombre in (("1", "Uno"), ("2.5", "Base"), ("5", "Cinco")):
            m[f"SensSemilla{nombre}Sin"] = coma(s["ps5_semilla"][semilla]["sin"])
            m[f"SensSemilla{nombre}Con"] = coma(s["ps5_semilla"][semilla]["con"])
        cifras["sensibilidad"] = s

    (RAIZ / "analisis" / "resumen_resultados.json").write_text(
        json.dumps({**cifras, "macros": m}, indent=2, ensure_ascii=False, default=float), encoding="utf-8")
    escribir_cifras(m)
    print("selección por validación:", seleccion)
    print("verificación NetLogo frente a Python:", verif)
    print(r1.round(1).to_string())
    print(r2.round(1).to_string())
    print(r3.round(1).to_string())
    print(errores.round(2).to_string())


if __name__ == "__main__":
    main()
