"""Análisis de los experimentos BehaviorSpace del modelo de difusión.

Lee las tablas CSV que exporta NetLogo (datos/resultados/*.csv), calcula las
medidas de desempeño por escenario y genera las figuras y tablas que usan el
artículo y la presentación:

  analisis/figuras/fig_curvas.{pdf,png}        curvas de adopción con y sin campaña
  analisis/figuras/fig_densidad.{pdf,png}      adopción final frente al grado promedio
  analisis/figuras/fig_topologia.{pdf,png}     adopción final por topología
  analisis/figuras/fig_duracion.{pdf,png}      adopción final frente a la duración de la campaña
  analisis/figuras/fig_calibracion.{pdf,png}   ABM y Bass frente a la serie real
  articulo/tablas/*.tex                        tablas en LaTeX (booktabs)
  analisis/resumen_resultados.json             cifras citadas en el texto
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from scipy import stats

RAIZ = Path(__file__).resolve().parents[1]
RES = RAIZ / "datos" / (sys.argv[1] if len(sys.argv) > 1 else "resultados")
FIG = RAIZ / "analisis" / "figuras"
TAB = RAIZ / "articulo" / "tablas"
FIG.mkdir(parents=True, exist_ok=True)
TAB.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------- estilo
TINTA, SECUNDARIO, REJILLA = "#23313F", "#5B6672", "#E3E7EB"
ESCALA = 1.0  # factor de tamaño de las figuras (la presentación usa uno mayor)
ALTO = 1.0    # factor adicional de altura (la presentación usa figuras más altas)
TEAL, NARANJA, VIOLETA, GRIS = "#0E9C98", "#D96C1A", "#6250D6", "#8A97A3"
COLOR_CAMPANA = {True: TEAL, False: NARANJA}
NOMBRE_CAMPANA = {True: "con campaña", False: "sin campaña"}
COLOR_TOPO = {"aleatoria": NARANJA, "mundo pequeño": TEAL, "libre de escala": VIOLETA}
ORDEN_TOPO = ["aleatoria", "mundo pequeño", "libre de escala"]
NOMBRE_Q = {0.02: "imitación calibrada (q = 0,020)", 0.032: "imitación de la literatura (q = 0,032)"}

if any("Inter" == f.name for f in font_manager.fontManager.ttflist):
    plt.rcParams["font.family"] = "Inter"
plt.rcParams.update({
    "font.size": 9, "axes.titlesize": 9.5, "axes.labelsize": 9, "legend.fontsize": 8,
    "xtick.labelsize": 8, "ytick.labelsize": 8,
    "axes.edgecolor": REJILLA, "axes.labelcolor": TINTA, "text.color": TINTA,
    "xtick.color": SECUNDARIO, "ytick.color": SECUNDARIO,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": REJILLA, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "legend.frameon": False, "figure.dpi": 150, "savefig.bbox": "tight", "savefig.pad_inches": 0.03,
    "axes.formatter.use_locale": False,
})


def coma(x, dec=1):
    """Formato numérico con coma decimal (texto en español)."""
    return f"{x:.{dec}f}".replace(".", ",")


def guardar(fig, nombre):
    fig.savefig(FIG / f"{nombre}.pdf")
    fig.savefig(FIG / f"{nombre}.png", dpi=300)
    plt.close(fig)


# ----------------------------------------------------------------- lectura
def leer(nombre):
    """Tabla BehaviorSpace: seis líneas de encabezado y luego la tabla."""
    df = pd.read_csv(RES / f"{nombre}.csv", skiprows=6, low_memory=False)
    df = df.rename(columns={"[run number]": "corrida", "[step]": "mes"})
    for col in ("campaña?", "dibujar-red?"):
        if col in df and df[col].dtype == object:
            df[col] = df[col].map({"true": True, "false": False})
    if "tipo-red" in df:
        df["tipo-red"] = df["tipo-red"].str.strip('"')
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
    """Una fila por corrida con el estado al último mes."""
    ult = df.loc[df.groupby("corrida")["mes"].idxmax()].copy()
    ult["alcanza-50"] = ult["mes-50"] >= 0
    ult.loc[~ult["alcanza-50"], "mes-50"] = np.nan
    return ult[["corrida", *factores, "mes", "porcentaje-adopcion", "mes-50", "alcanza-50", "pico-nuevos", "mes-pico"]]


def resumen(ult, factores):
    g = ult.groupby(factores)
    out = g["porcentaje-adopcion"].agg(media="mean", ic=ic95, de="std", n="count")
    out["t50_mediana"] = g["mes-50"].median()
    out["prop_alcanza_50"] = g["alcanza-50"].mean()
    out["pico_media"] = g["pico-nuevos"].mean()
    out["mes_pico_mediana"] = g["mes-pico"].median()
    return out.reset_index()


def curva_media(df, factores):
    g = df.groupby([*factores, "mes"])["porcentaje-adopcion"]
    out = g.agg(media="mean", ic=ic95).reset_index()
    return out


# ----------------------------------------------------------------- figuras
def fig_curvas(df):
    """Curvas de adopción: dos paneles (nivel de q), campaña × densidad (k = 4 y 12)."""
    sub = df[df["grado-promedio"].isin([4, 12])]
    cur = curva_media(sub, ["q-imitacion", "campaña?", "grado-promedio"])
    fig, ejes = plt.subplots(1, 2, figsize=(6.6 * ESCALA, 2.6 * ESCALA * ALTO), sharey=True)
    for eje, q in zip(ejes, sorted(cur["q-imitacion"].unique())):
        for camp in (True, False):
            for k, estilo in ((12, "-"), (4, (0, (4, 2)))):
                c = cur[(cur["q-imitacion"] == q) & (cur["campaña?"] == camp) & (cur["grado-promedio"] == k)]
                eje.fill_between(c["mes"], c["media"] - c["ic"], c["media"] + c["ic"], color=COLOR_CAMPANA[camp], alpha=0.18, lw=0)
                eje.plot(c["mes"], c["media"], ls=estilo, color=COLOR_CAMPANA[camp], lw=1.6,
                         label=f"{NOMBRE_CAMPANA[camp]}, k = {k}")
                if not camp:
                    eje.annotate(f"k = {k}", (c["mes"].iloc[-1], c["media"].iloc[-1]), xytext=(3, 0),
                                 textcoords="offset points", fontsize=7, color=COLOR_CAMPANA[camp], va="center")
        eje.set_title(NOMBRE_Q[q], loc="left", color=SECUNDARIO)
        eje.set_xlabel("mes")
        eje.set_xlim(0, 132)
        eje.set_ylim(0, 100)
    ejes[0].set_ylabel("adopción (% de la población)")
    manijas, etiquetas = ejes[0].get_legend_handles_labels()
    fig.legend(manijas, etiquetas, loc="lower center", bbox_to_anchor=(0.5, -0.12 - 0.4 * (ESCALA - 1)), ncol=4, handlelength=2.2, columnspacing=1.2)
    guardar(fig, "fig_curvas")


def fig_escenarios(df, res_dur):
    """Figura combinada para el artículo: curvas de E1 (dos paneles) y duración de campaña (E3)."""
    sub = df[df["grado-promedio"].isin([4, 12])]
    cur = curva_media(sub, ["q-imitacion", "campaña?", "grado-promedio"])
    fig, ejes = plt.subplots(1, 3, figsize=(7.0 * ESCALA, 2.3 * ESCALA * ALTO), gridspec_kw={"width_ratios": [1.15, 1.15, 1]})
    for eje, q in zip(ejes[:2], sorted(cur["q-imitacion"].unique())):
        for camp in (True, False):
            for k, estilo in ((12, "-"), (4, (0, (4, 2)))):
                c = cur[(cur["q-imitacion"] == q) & (cur["campaña?"] == camp) & (cur["grado-promedio"] == k)]
                eje.fill_between(c["mes"], c["media"] - c["ic"], c["media"] + c["ic"], color=COLOR_CAMPANA[camp], alpha=0.18, lw=0)
                eje.plot(c["mes"], c["media"], ls=estilo, color=COLOR_CAMPANA[camp], lw=1.5, label=f"{NOMBRE_CAMPANA[camp]}, k = {k}")
                if not camp:
                    eje.annotate(f"k = {k}", (c["mes"].iloc[-1], c["media"].iloc[-1]), xytext=(2, 0),
                                 textcoords="offset points", fontsize=6.5, color=COLOR_CAMPANA[camp], va="center")
        eje.set_title(("(a) " if q == 0.02 else "(b) ") + NOMBRE_Q[q].replace(" (", "\n("), loc="left", color=SECUNDARIO, fontsize=8)
        eje.set_xlabel("mes")
        eje.set_xlim(0, 134)
        eje.set_ylim(0, 100)
    ejes[0].set_ylabel("adopción (% de la población)")
    ejes[0].legend(loc="upper left", handlelength=2.0, fontsize=6.8, labelspacing=0.3)
    ejes[1].tick_params(labelleft=False)
    eje = ejes[2]
    estilos = {0.02: (TEAL, "o", "-"), 0.032: (VIOLETA, "s", (0, (4, 2)))}
    for q in sorted(res_dur["q-imitacion"].unique()):
        r = res_dur[res_dur["q-imitacion"] == q].sort_values("duracion-campaña")
        color, marcador, estilo = estilos[q]
        eje.errorbar(r["duracion-campaña"], r["media"], yerr=r["ic"], color=color, marker=marcador, ms=4, ls=estilo, lw=1.5,
                     capsize=2, label=f"q = {coma(q, 3)}")
    eje.set_title("(c) duración de la campaña\n(mundo pequeño, k = 6)", loc="left", color=SECUNDARIO, fontsize=8)
    eje.set_xlabel("meses de campaña")
    eje.set_xticks([0, 12, 24, 60, 120])
    eje.set_ylim(0, 100)
    eje.tick_params(labelleft=False)
    eje.legend(loc="lower right", fontsize=6.8)
    fig.subplots_adjust(wspace=0.12)
    guardar(fig, "fig_escenarios")


def fig_densidad(res):
    """Adopción final frente al grado promedio, con y sin campaña, por nivel de q."""
    fig, ejes = plt.subplots(1, 2, figsize=(6.6 * ESCALA, 2.5 * ESCALA * ALTO), sharey=True)
    for eje, q in zip(ejes, sorted(res["q-imitacion"].unique())):
        for camp in (True, False):
            r = res[(res["q-imitacion"] == q) & (res["campaña?"] == camp)].sort_values("grado-promedio")
            eje.errorbar(r["grado-promedio"], r["media"], yerr=r["ic"], color=COLOR_CAMPANA[camp], lw=1.6,
                         marker="o", ms=4.5, capsize=2.5, label=NOMBRE_CAMPANA[camp])
            eje.annotate(NOMBRE_CAMPANA[camp], (r["grado-promedio"].iloc[-1], r["media"].iloc[-1]),
                         xytext=(5, 0), textcoords="offset points", fontsize=7.5, color=COLOR_CAMPANA[camp], va="center")
        eje.set_title(NOMBRE_Q[q], loc="left", color=SECUNDARIO)
        eje.set_xlabel("grado promedio de la red (k)")
        eje.set_xticks([2, 4, 6, 8, 12, 16])
        eje.set_xlim(1, 20.5)
        eje.set_ylim(0, 100)
    ejes[0].set_ylabel("adopción final a 120 meses (%)")
    ejes[0].legend(loc="center left")
    guardar(fig, "fig_densidad")


def fig_topologia(res):
    """Adopción final por topología (puntos con IC 95 %), con y sin campaña, por nivel de q."""
    fig, ejes = plt.subplots(1, 2, figsize=(6.6 * ESCALA, 2.4 * ESCALA * ALTO), sharey=True)
    y = np.arange(len(ORDEN_TOPO))
    for eje, q in zip(ejes, sorted(res["q-imitacion"].unique())):
        for camp, dy in ((False, 0.16), (True, -0.16)):
            r = res[(res["q-imitacion"] == q) & (res["campaña?"] == camp)].set_index("tipo-red").loc[ORDEN_TOPO]
            eje.errorbar(r["media"], y + dy, xerr=r["ic"], fmt="o", ms=5, color=COLOR_CAMPANA[camp],
                         capsize=2.5, lw=1.4, label=NOMBRE_CAMPANA[camp])
            for yi, v in zip(y + dy, r["media"]):
                eje.annotate(coma(v), (v, yi), xytext=(6, 0), textcoords="offset points", fontsize=7.5,
                             va="center", color=TINTA)
        eje.set_yticks(y)
        eje.set_yticklabels(ORDEN_TOPO)
        eje.set_xlim(0, 100)
        eje.set_xlabel("adopción final a 120 meses (%)")
        eje.set_title(NOMBRE_Q[q], loc="left", color=SECUNDARIO)
        eje.grid(axis="y", visible=False)
    ejes[0].invert_yaxis()
    manijas, etiquetas = ejes[1].get_legend_handles_labels()
    fig.legend(manijas, etiquetas, loc="lower center", bbox_to_anchor=(0.5, -0.16), ncol=2)
    guardar(fig, "fig_topologia")


def fig_duracion(res):
    """Adopción final frente a la duración de la campaña, por nivel de q."""
    fig, eje = plt.subplots(figsize=(3.6 * ESCALA, 2.5 * ESCALA * ALTO))
    estilos = {0.02: (TEAL, "o", "-"), 0.032: (VIOLETA, "s", (0, (4, 2)))}
    for q in sorted(res["q-imitacion"].unique()):
        r = res[res["q-imitacion"] == q].sort_values("duracion-campaña")
        color, marcador, estilo = estilos[q]
        eje.errorbar(r["duracion-campaña"], r["media"], yerr=r["ic"], color=color, marker=marcador, ms=4.5,
                     ls=estilo, lw=1.6, capsize=2.5, label=f"q = {coma(q, 3)}")
    eje.set_xlabel("duración de la campaña (meses)")
    eje.set_ylabel("adopción final a 120 meses (%)")
    eje.set_xticks([0, 6, 12, 24, 60, 120])
    eje.set_ylim(0, 100)
    eje.legend(loc="lower right")
    guardar(fig, "fig_duracion")


def fig_calibracion(df, datos, parametros, seleccion):
    """Serie real (por partición), curva de Bass ajustada y ABM con la estructura seleccionada."""
    t0 = parametros["origen_temporal"]
    p, q, m = (parametros["anual"][k] for k in "pqm")
    fig, eje = plt.subplots(figsize=(6.6 * ESCALA, 2.7 * ESCALA * ALTO))
    anios = np.linspace(t0, 2027, 400)
    e = np.exp(-(p + q) * (anios - t0))
    eje.plot(anios, 100 * m * (1 - e) / (1 + (q / p) * e), color=GRIS, lw=1.4, ls=(0, (4, 2)), label="modelo agregado de Bass")
    sel = df[(df["tipo-red"] == seleccion["tipo-red"]) & (df["grado-promedio"] == seleccion["grado-promedio"])]
    c = curva_media(sel, []).sort_values("mes")
    x = t0 + c["mes"] / 12
    eje.fill_between(x, c["media"] - c["ic"], c["media"] + c["ic"], color=TEAL, alpha=0.2, lw=0)
    eje.plot(x, c["media"], color=TEAL, lw=1.8, label=f"ABM ({seleccion['tipo-red']}, k = {seleccion['grado-promedio']})")
    marcas = {"entrenamiento": ("o", TINTA, "full"), "validacion": ("s", TINTA, "none"), "prueba": ("^", TINTA, "none")}
    etiquetas = {"entrenamiento": "datos: entrenamiento", "validacion": "datos: validación", "prueba": "datos: prueba"}
    for nombre, (mk, col, relleno) in marcas.items():
        a, b = parametros["particion"][nombre]["inicio"], parametros["particion"][nombre]["fin"]
        d = datos[(datos.anio_decimal >= a) & (datos.anio_decimal < b)]
        eje.plot(d.anio_decimal, d.adopcion_pct, mk, ms=4.5, color=col, fillstyle=relleno, mew=1.1, ls="none", label=etiquetas[nombre])
    rotulos = {"entrenamiento": "entrenamiento", "validacion": "validación", "prueba": "prueba"}
    for nombre, (a, b) in ((k, (v["inicio"], v["fin"])) for k, v in parametros["particion"].items()):
        b = min(b, 2027)
        if nombre != "entrenamiento":
            eje.axvspan(a, b, color=REJILLA, alpha=0.4, lw=0)
        eje.text((a + b) / 2, 98, rotulos[nombre], ha="center", va="top", fontsize=7.5, color=SECUNDARIO)
    eje.set_xlim(t0, 2027)
    eje.set_xticks(range(2008, 2027, 2))
    eje.set_ylim(0, 100)
    eje.set_ylabel("adultos con smartphone (%)")
    eje.set_xlabel("año")
    eje.legend(loc="lower right", ncol=2, framealpha=0.9, frameon=True, edgecolor=REJILLA)
    guardar(fig, "fig_calibracion")


# ----------------------------------------------------------------- tablas
def tabla_latex(nombre, encabezado, filas, caption, label, alineacion, pequena=False):
    cuerpo = " \\\\\n".join(" & ".join(f) for f in filas)
    texto = (
        "\\begin{table}[tb]\n\\centering\n"
        f"\\caption{{{caption}}}\n\\label{{{label}}}\n" + ("\\small\n" if pequena else "")
        + ("\\setlength{\\tabcolsep}{4pt}\n" if pequena else "") + f"\\begin{{tabular}}{{{alineacion}}}\n\\toprule\n"
        + " & ".join(encabezado) + " \\\\\n\\midrule\n" + cuerpo + " \\\\\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    )
    (TAB / f"{nombre}.tex").write_text(texto, encoding="utf-8")


PALABRA = {2: "Dos", 4: "Cuatro", 6: "Seis", 8: "Ocho", 12: "Doce", 16: "Dieciseis", 0: "Cero", 24: "Veinticuatro",
           60: "Sesenta", 120: "Cientoveinte"}
NIVEL_Q = {0.02: "Cal", 0.032: "Lit"}
TOPO_MACRO = {"aleatoria": "Aleatoria", "mundo pequeño": "Mundo", "libre de escala": "Escala"}


def escribir_cifras(parametros, r1, r2, r3, errores, seleccion, est):
    """Macros LaTeX con las cifras citadas en el texto del artículo (articulo/tablas/cifras.tex)."""
    m = {}
    an, me = parametros["anual"], parametros["mensual"]
    m["BassP"], m["BassQ"], m["BassM"] = coma(an["p"], 3), coma(an["q"], 3), coma(100 * an["m"], 0)
    m["BassPmes"], m["BassQmes"] = coma(me["p"], 4), coma(me["q"], 4)
    m["BassPico"] = coma(parametros["tiempo_pico_anios"], 1)
    for part, abrev in (("entrenamiento", "Ent"), ("validacion", "Val"), ("prueba", "Pru")):
        m[f"BassRmse{abrev}"] = coma(parametros["desempeno_bass"][part]["RMSE_pct"], 2)
        m[f"BassMape{abrev}"] = coma(parametros["desempeno_bass"][part]["MAPE_pct"], 2)
    sel = errores[(errores["tipo-red"] == seleccion["tipo-red"]) & (errores["grado-promedio"] == seleccion["grado-promedio"])].iloc[0]
    m["AbmSelRed"], m["AbmSelK"] = seleccion["tipo-red"], str(seleccion["grado-promedio"])
    m["AbmRmseEnt"], m["AbmRmseVal"], m["AbmRmsePru"] = coma(sel["rmse_entrenamiento"], 2), coma(sel["rmse_validacion"], 2), coma(sel["rmse_prueba"], 2)
    m["AbmMapePru"], m["AbmFinal"] = coma(sel["mape_prueba"], 2), coma(sel["final_media"], 1)
    m["AbmRmseValMax"], m["AbmRmsePruMax"] = coma(errores["rmse_validacion"].max(), 2), coma(errores["rmse_prueba"].max(), 2)
    peor = errores.sort_values("rmse_validacion").iloc[-1]
    m["AbmPeorRed"], m["AbmPeorK"] = peor["tipo-red"], str(int(peor["grado-promedio"]))
    for _, r in r1.iterrows():
        clave = f"{'Con' if r['campaña?'] else 'Sin'}{NIVEL_Q[round(r['q-imitacion'], 3)]}K{PALABRA[int(r['grado-promedio'])]}"
        m[clave] = coma(r["media"]); m[clave + "Ic"] = coma(r["ic"])
        m["Tcincuenta" + clave] = "--" if r["prop_alcanza_50"] < 0.5 else coma(r["t50_mediana"], 0)
    con = r1[r1["campaña?"]].set_index(["q-imitacion", "grado-promedio"])["media"]
    sin = r1[~r1["campaña?"]].set_index(["q-imitacion", "grado-promedio"])["media"]
    m["DensidadGananciaCon"] = coma(np.mean([con[(q, 16)] - con[(q, 2)] for q in NIVEL_Q]), 0)
    m["DensidadRazonSinCal"] = coma(sin[(0.02, 16)] / sin[(0.02, 2)], 1)
    m["DensidadRazonSinLit"] = coma(sin[(0.032, 16)] / sin[(0.032, 2)], 1)
    for _, r in r2.iterrows():
        clave = f"Topo{'Con' if r['campaña?'] else 'Sin'}{NIVEL_Q[round(r['q-imitacion'], 3)]}{TOPO_MACRO[r['tipo-red']]}"
        m[clave] = coma(r["media"]); m[clave + "Ic"] = coma(r["ic"]); m[clave + "De"] = coma(r["de"])
        m[clave + "Prop"] = coma(100 * r["prop_alcanza_50"], 0)
    for _, r in r3.iterrows():
        clave = f"Dur{NIVEL_Q[round(r['q-imitacion'], 3)]}D{PALABRA[int(r['duracion-campaña'])]}"
        m[clave] = coma(r["media"]); m[clave + "Ic"] = coma(r["ic"])
        m["Tcincuenta" + clave] = "--" if r["prop_alcanza_50"] < 0.5 else coma(r["t50_mediana"], 0)
    for topo, fila in est.iterrows():
        m[f"Est{TOPO_MACRO[topo]}C"] = coma(fila["agrupamiento"], 3)
        m[f"Est{TOPO_MACRO[topo]}L"] = coma(fila["camino-medio"], 1) if not np.isnan(fila["camino-medio"]) else "no conexa"
    lineas = [f"\\newcommand{{\\cifra{k}}}{{{v}}}" for k, v in m.items()]
    (TAB / "cifras.tex").write_text("% generado por analisis_resultados.py\n" + "\n".join(lineas) + "\n", encoding="utf-8")


def main():
    parametros = json.loads((RAIZ / "analisis" / "parametros_calibrados.json").read_text())
    datos = pd.read_csv(RAIZ / "datos" / "pew_smartphone_eeuu.csv")
    cifras = {}

    # ---- experimento 1: publicidad × densidad
    e1 = leer("publicidad_x_densidad")
    f1 = ["q-imitacion", "campaña?", "grado-promedio"]
    r1 = resumen(finales(e1, f1), f1)
    fig_curvas(e1)
    fig_densidad(r1)
    filas = []
    for k in sorted(r1["grado-promedio"].unique()):
        fila = [str(k)]
        for q in sorted(r1["q-imitacion"].unique()):
            for camp in (False, True):
                r = r1[(r1["q-imitacion"] == q) & (r1["grado-promedio"] == k) & (r1["campaña?"] == camp)].iloc[0]
                celda = f"{coma(r['media'])} $\\pm$ {coma(r['ic'])}"
                if camp:
                    celda += " (" + ("--" if r["prop_alcanza_50"] < 0.5 else coma(r["t50_mediana"], 0)) + ")"
                fila.append(celda)
        filas.append(fila)
    tabla_latex("tabla_densidad", ["$k$", "sin, $q$=0,020", "con, $q$=0,020 ($T_{50}$)", "sin, $q$=0,032", "con, $q$=0,032 ($T_{50}$)"], filas,
                "Adopción final a 120 meses (media $\\pm$ IC 95\\,\\%, 30 réplicas) sin y con campaña según el grado promedio $k$ de la red de "
                "mundo pequeño y el coeficiente de imitación $q$; entre paréntesis, mes en que se alcanza el 50\\,\\% ($T_{50}$, mediana). "
                "Sin campaña, ninguna configuración alcanza el 50\\,\\% en la mayoría de las réplicas.",
                "tab:densidad", "lrrrr", pequena=True)
    cifras["densidad"] = r1.to_dict(orient="records")

    # ---- experimento 2: topología × publicidad
    e2 = leer("topologia_x_publicidad")
    f2 = ["q-imitacion", "campaña?", "tipo-red"]
    u2 = finales(e2, f2)
    r2 = resumen(u2, f2)
    fig_topologia(r2)
    est = e2.loc[e2.groupby("corrida")["mes"].idxmax()].groupby("tipo-red")[["grado-medio", "agrupamiento", "camino-medio"]].mean()
    filas = []
    for topo in ORDEN_TOPO:
        fila = [topo, coma(est.loc[topo, "grado-medio"]), coma(est.loc[topo, "agrupamiento"], 3),
                coma(est.loc[topo, "camino-medio"]) if not np.isnan(est.loc[topo, "camino-medio"]) else "no conexa"]
        for q in sorted(r2["q-imitacion"].unique()):
            for camp in (False, True):
                r = r2[(r2["q-imitacion"] == q) & (r2["tipo-red"] == topo) & (r2["campaña?"] == camp)].iloc[0]
                fila.append(f"{coma(r['media'])} $\\pm$ {coma(r['ic'])}")
        filas.append(fila)
    for fila in filas:
        del fila[1]  # el grado medio es el mismo (k = 6) en las tres redes
    tabla_latex("tabla_topologia",
                ["red", "$C$", "$\\ell$", "sin, $q$=0,020", "con, $q$=0,020", "sin, $q$=0,032", "con, $q$=0,032"],
                filas,
                "Propiedades estructurales de las redes generadas ($N=1000$, $k=6$; $C$: coeficiente de agrupamiento, $\\ell$: longitud media de camino) "
                "y adopción final a 120 meses (media $\\pm$ IC 95\\,\\%) sin y con campaña, por topología.",
                "tab:topologia", "lrrrrrr", pequena=True)
    cifras["topologia"] = r2.to_dict(orient="records")
    cifras["estructura"] = est.reset_index().to_dict(orient="records")

    # ---- experimento 3: duración de la campaña
    e3 = leer("duracion_campana")
    f3 = ["q-imitacion", "duracion-campaña"]
    r3 = resumen(finales(e3, f3), f3)
    fig_duracion(r3)
    fig_escenarios(e1, r3)
    cifras["duracion"] = r3.to_dict(orient="records")

    # ---- experimento 4: calibración frente a datos reales
    e4 = leer("calibracion_pew")
    t0 = parametros["origen_temporal"]
    e4["anio"] = t0 + e4["mes"] / 12

    def error_particion(curva, nombre):
        a, b = parametros["particion"][nombre]["inicio"], parametros["particion"][nombre]["fin"]
        d = datos[(datos.anio_decimal >= a) & (datos.anio_decimal < b)]
        yhat = np.interp(d.anio_decimal, curva["anio"], curva["media"])
        return (float(np.sqrt(np.mean((d.adopcion_pct - yhat) ** 2))),
                float(np.mean(np.abs((d.adopcion_pct - yhat) / d.adopcion_pct)) * 100))

    filas_cal, errores = [], []
    for topo in ORDEN_TOPO:
        for k in sorted(e4["grado-promedio"].unique()):
            sub = e4[(e4["tipo-red"] == topo) & (e4["grado-promedio"] == k)]
            c = curva_media(sub, []).sort_values("mes")
            c["anio"] = t0 + c["mes"] / 12
            err = {n: error_particion(c, n) for n in ("entrenamiento", "validacion", "prueba")}
            final = sub.loc[sub.groupby("corrida")["mes"].idxmax(), "porcentaje-adopcion"]
            errores.append({"tipo-red": topo, "grado-promedio": int(k), **{f"rmse_{n}": e[0] for n, e in err.items()},
                            **{f"mape_{n}": e[1] for n, e in err.items()}, "final_media": float(final.mean())})
    errores = pd.DataFrame(errores)
    sel = errores.sort_values("rmse_validacion").iloc[0]
    seleccion = {"tipo-red": sel["tipo-red"], "grado-promedio": int(sel["grado-promedio"])}
    fig_calibracion(e4, datos, parametros, seleccion)
    bass = parametros["desempeno_bass"]
    ks = sorted(int(k) for k in errores["grado-promedio"].unique())
    for topo in ORDEN_TOPO:
        fila = [f"ABM {topo}"]
        for k in ks:
            r = errores[(errores["tipo-red"] == topo) & (errores["grado-promedio"] == k)].iloc[0]
            marca = "$\\star$" if (topo == seleccion["tipo-red"] and k == seleccion["grado-promedio"]) else ""
            fila.append(f"{coma(r['rmse_validacion'], 2)} / {coma(r['rmse_prueba'], 2)}{marca}")
        filas_cal.append(fila)
    tabla_latex("tabla_calibracion",
                ["modelo", *[f"$k={k}$" for k in ks]], filas_cal,
                "RMSE del ABM (puntos porcentuales) frente a la serie real en validación / prueba, por topología y grado promedio. "
                "La estructura se elige por el menor RMSE en validación ($\\star$); la partición de prueba no interviene en ninguna decisión. "
                f"El modelo agregado de Bass obtiene {coma(bass['validacion']['RMSE_pct'], 2)} / {coma(bass['prueba']['RMSE_pct'], 2)}.",
                "tab:calibracion", "lrrr", pequena=True)
    cifras["calibracion"] = {"errores": errores.to_dict(orient="records"), "seleccion": seleccion, "bass": bass}

    (RAIZ / "analisis" / "resumen_resultados.json").write_text(json.dumps(cifras, indent=2, ensure_ascii=False, default=float), encoding="utf-8")
    escribir_cifras(parametros, r1, r2, r3, errores, seleccion, est)
    print("selección por validación:", seleccion)
    print(r1.round(1).to_string())
    print(r2.round(1).to_string())
    print(r3.round(1).to_string())
    print(errores.round(2).to_string())


if __name__ == "__main__":
    main()
