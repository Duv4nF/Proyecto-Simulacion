"""Figuras para las diapositivas (Beamer 16:9, 160 x 90 mm).

Cada figura se dibuja al tamaño físico con que se proyecta (en pulgadas, para el ancho de
columna que ocupa en presentacion/presentacion.tex), así la letra queda legible y del
mismo tamaño en todas. Fondo transparente: se funden con el papel de las diapositivas.
Se escriben en analisis/figuras/diapositivas/.

Uso:  python figuras_diapositivas.py [carpeta_resultados]
"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import networkx as nx  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analisis_resultados as ar  # noqa: E402
import analogia_gtav  # noqa: E402
import datos_ps5 as dp  # noqa: E402

RAIZ = dp.RAIZ
SALIDA = RAIZ / "analisis" / "figuras" / "diapositivas"
SALIDA.mkdir(parents=True, exist_ok=True)
ar.FIG = SALIDA

plt.rcParams.update({
    "font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8, "legend.fontsize": 7,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "savefig.transparent": True,
    "figure.facecolor": "none", "axes.facecolor": "none", "savefig.facecolor": "none",
    "lines.linewidth": 1.6, "savefig.pad_inches": 0.02,
})

NODO, ENLACE = "#B4AEA3", "#C9C3B8"


def guardar_png(fig, nombre, dpi=300):
    fig.savefig(SALIDA / f"{nombre}.png", dpi=dpi, transparent=True)
    plt.close(fig)


def red(tipo, n, k, semilla):
    s = int(np.random.default_rng(semilla).integers(1 << 31))
    if tipo == "aleatoria":
        return nx.gnp_random_graph(n, k / (n - 1), seed=s)
    if tipo == "mundo pequeño":
        return nx.watts_strogatz_graph(n, k, 0.1, seed=s)
    return nx.barabasi_albert_graph(n, k // 2, seed=s)


def dibujar_red(eje, tipo, n=140, k=6, semilla=3, fraccion=0.22, titulo=None, tam=1.0):
    """Red pequeña con los colores del proyecto: adoptantes en azul, nuevos en terracota."""
    g = red(tipo, n, k, semilla)
    pos = nx.circular_layout(g) if tipo == "mundo pequeño" else nx.spring_layout(g, seed=semilla, k=1.4 / np.sqrt(n))
    grados = dict(g.degree())
    inicio = max(grados, key=grados.get) if tipo == "libre de escala" else int(np.random.default_rng(semilla).integers(n))
    orden = list(nx.bfs_tree(g, inicio)) if nx.is_connected(g) else list(g.nodes)
    adoptantes = set(orden[: int(fraccion * n)])
    nuevos = set(orden[int(fraccion * n): int(fraccion * n) + max(2, n // 40)])
    colores = [ar.TERRACOTA if v in nuevos else ar.AZUL if v in adoptantes else NODO for v in g.nodes]
    nx.draw_networkx_edges(g, pos, ax=eje, edge_color=ENLACE, width=0.6 * tam)
    nx.draw_networkx_nodes(g, pos, ax=eje, node_color=colores, node_size=[tam * (10 + 4 * grados[v]) for v in g.nodes], linewidths=0)
    eje.set_axis_off()
    if titulo:
        eje.set_title(titulo, color=ar.TINTA, fontsize=8, pad=4)


def fig_portada():
    fig, eje = plt.subplots(figsize=(3.0, 3.0))
    dibujar_red(eje, "libre de escala", n=220, k=4, semilla=11, fraccion=0.3, tam=0.9)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    guardar_png(fig, "portada_red")


def fig_mezcla_vs_red():
    """Mezcla perfecta (Bass) frente a red social, para la diapositiva del problema (columna de 70 mm)."""
    fig, ejes = plt.subplots(1, 2, figsize=(2.9, 1.55))
    n = 18
    g = nx.complete_graph(n)
    pos = nx.circular_layout(g)
    nx.draw_networkx_edges(g, pos, ax=ejes[0], edge_color="#B9B3A8", width=0.35)
    nx.draw_networkx_nodes(g, pos, ax=ejes[0], node_color=[ar.AZUL if i < 5 else NODO for i in range(n)], node_size=22, linewidths=0)
    ejes[0].set_axis_off()
    ejes[0].set_title("Bass: todos con todos", color=ar.TINTA, fontsize=7.5, pad=3)
    g2 = nx.watts_strogatz_graph(n, 4, 0.15, seed=4)
    pos2 = nx.circular_layout(g2)
    adop = {0, 1, 2, 17, 9}
    nx.draw_networkx_edges(g2, pos2, ax=ejes[1], edge_color="#9C968B", width=0.6)
    nx.draw_networkx_nodes(g2, pos2, ax=ejes[1], node_color=[ar.AZUL if i in adop else NODO for i in range(n)], node_size=22, linewidths=0)
    ejes[1].set_axis_off()
    ejes[1].set_title("agentes: solo los vecinos", color=ar.TINTA, fontsize=7.5, pad=3)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.86, bottom=0.02, wspace=0.12)
    guardar_png(fig, "mezcla_vs_red")


def fig_serie_ps5(datos):
    """Serie real por partición (diapositiva del conjunto de datos; columna de 83 mm)."""
    fig, eje = plt.subplots(figsize=(3.3, 2.25))
    limite = pd.Timestamp("2027-01-31")
    marcas = {"entrenamiento": ("o", "full"), "validacion": ("s", "none"), "prueba": ("^", "none")}
    for nombre, (mk, relleno) in marcas.items():
        d = dp.subconjunto(datos, nombre)
        a, b = dp.PARTICION[nombre]
        eje.plot(d.fecha_cierre, d.unidades_acumuladas_M, mk, ms=4, color=ar.TINTA, fillstyle=relleno, mew=1, ls="none",
                 label=f"{dp.NOMBRE_PARTICION[nombre]} ({len(d)})")
        if nombre != "entrenamiento":
            eje.axvspan(pd.Timestamp(a) - pd.Timedelta(days=45), limite if nombre == "prueba" else pd.Timestamp(b) + pd.Timedelta(days=45),
                        color=ar.REJILLA, alpha=0.6, lw=0)
    eje.axhline(dp.UNIVERSO_M, color=ar.GRIS, lw=1, ls=(0, (4, 2)))
    eje.annotate(f"base de PS4: {ar.coma(dp.UNIVERSO_M, 0)} M", (pd.Timestamp("2020-12-15"), dp.UNIVERSO_M), xytext=(0, 3),
                 textcoords="offset points", fontsize=7, color=ar.SECUNDARIO)
    eje.set_xlim(dp.LANZAMIENTO, limite)
    eje.set_ylim(0, 128)
    eje.xaxis.set_major_locator(mdates.YearLocator())
    eje.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    eje.set_ylabel("PS5 acumuladas (millones)")
    eje.legend(loc="upper left", bbox_to_anchor=(0.0, 0.9), title="trimestres", title_fontsize=7, handletextpad=0.3)
    guardar_png(fig, "serie_ps5")


def fig_analogia(gta):
    """GTA V: cifras oficiales y la recursión de Bass ajustada (columna de 75 mm)."""
    a = gta["ajuste"]
    base = sum(gta["base_instalada_M"].values())
    curva = analogia_gtav.recursion(a["F0"], a["p_mes"], a["q_mes"], a["m"], 14)
    fig, eje = plt.subplots(figsize=(2.95, 2.15))
    eje.plot(np.arange(15), 100 * curva, color=ar.CIRUELA, lw=1.8, label=f"Bass ajustado (p = {ar.coma(a['p_mes'], 2)})")
    obs = pd.DataFrame(gta["observaciones"])
    dia1, resto = obs[obs["tipo"] == "primeras 24 horas"], obs[obs["tipo"] == "sell-in"]
    eje.plot(resto["t_meses"], 100 * resto["fraccion_base"], "o", ms=4.5, color=ar.TINTA, label="Take-Two")
    eje.plot(dia1["t_meses"], 100 * dia1["fraccion_base"], "D", ms=4, color=ar.TINTA, fillstyle="none", mew=1, label="primer día (Guinness)")
    eje.set_xlim(-0.3, 14)
    eje.set_xticks([0, 3, 6, 9, 12])
    eje.set_ylim(0, 25)
    eje.set_xlabel("meses desde el lanzamiento de GTA V")
    eje.set_ylabel(f"% de la base PS3 + X360 ({ar.coma(base, 0)} M)")
    eje.legend(loc="center right")
    guardar_png(fig, "analogia_gtav")


def fig_publicidad(e1):
    """Curvas con y sin campaña en la red más dispersa y la más densa (k = 2 y 16), PS5 y GTA 6 (ancho completo)."""
    cur = ar.curva_media(e1[e1["grado-promedio"].isin([2, 16])], ["caso", "campaña?", "grado-promedio"])
    fig, ejes = plt.subplots(1, 2, figsize=(5.2, 1.95))
    for eje, caso in zip(ejes, ar.CASOS):
        ar._curvas_caso(eje, cur, caso, ks=(2, 16))
        horizonte = int(cur[cur["caso"] == caso]["mes"].max())
        eje.set_xlim(0, horizonte)
        eje.set_xticks(range(0, horizonte + 1, 12 if horizonte > 30 else 6))
        eje.set_ylim(0, 100 if caso == ar.PS5 else 25)
        eje.set_xlabel("meses desde el lanzamiento")
        ar.titulo_panel(eje, f"{ar.CORTO[caso]} ({'curva en S' if caso == ar.PS5 else 'ventas en el lanzamiento'})", fontsize=8)
    ejes[0].set_ylabel("adopción (%)")
    manijas, etiquetas = ejes[0].get_legend_handles_labels()
    fig.legend(manijas, etiquetas, loc="lower center", bbox_to_anchor=(0.5, -0.06), ncol=4, handlelength=2.0, columnspacing=1.0)
    fig.subplots_adjust(wspace=0.22, bottom=0.3)
    guardar_png(fig, "publicidad_casos")


def fig_densidad(r1):
    """Adopción final frente al grado promedio (ancho de 112 mm)."""
    fig, ejes = plt.subplots(1, 2, figsize=(4.4, 1.95))
    for eje, caso in zip(ejes, ar.CASOS):
        for camp in (True, False):
            r = r1[(r1["caso"] == caso) & (r1["campaña?"] == camp)].sort_values("grado-promedio")
            eje.errorbar(r["grado-promedio"], r["media"], yerr=r["ic"], color=ar.COLOR_CAMPANA[camp], lw=1.4,
                         marker="o", ms=3, capsize=2, label=ar.NOMBRE_CAMPANA[camp])
        horizonte = int(r1[r1["caso"] == caso]["horizonte"].max())
        ar.titulo_panel(eje, f"{ar.CORTO[caso]} (a {horizonte} meses)", fontsize=8)
        eje.set_xlabel("grado promedio (k)")
        eje.set_xticks([2, 4, 6, 8, 12, 16])
        eje.set_ylim(0, 100 if caso == ar.PS5 else 25)
    ejes[0].set_ylabel("adopción final (%)")
    ejes[1].legend(loc="lower right")
    fig.subplots_adjust(wspace=0.3)
    guardar_png(fig, "densidad")


def fig_fraccion_duracion(r3):
    """Efecto de una campaña de d meses como % del de una permanente (columna de 78 mm)."""
    fig, eje = plt.subplots(figsize=(3.05, 2.0))
    ar.dibujar_fraccion(eje, r3, ms=4, etiquetas=True)
    eje.set_ylabel("% del efecto de la\ncampaña permanente", fontsize=7.5)
    guardar_png(fig, "fraccion_duracion")


def main():
    carpeta = sys.argv[1] if len(sys.argv) > 1 else "resultados"
    ar.RES = RAIZ / "datos" / carpeta
    parametros = json.loads((RAIZ / "analisis" / "parametros_calibrados.json").read_text(encoding="utf-8"))
    gta = json.loads((RAIZ / "analisis" / "parametros_gta6.json").read_text(encoding="utf-8"))
    cifras = json.loads((RAIZ / "analisis" / "resumen_resultados.json").read_text(encoding="utf-8"))
    datos = dp.cargar()

    fig_portada()
    fig_mezcla_vs_red()
    fig_serie_ps5(datos)
    fig_analogia(gta)

    e1 = ar.leer("publicidad_x_densidad")
    f1 = ["caso", "campaña?", "grado-promedio"]
    r1 = ar.resumen(ar.finales(e1, f1), f1)
    fig_publicidad(e1)
    fig_densidad(r1)
    e3 = ar.leer("duracion_campana")
    f3 = ["caso", "duracion-campaña"]
    fig_fraccion_duracion(ar.resumen(ar.finales(e3, f3), f3))

    # calibración: la función del análisis, al tamaño de la columna (86 mm de ancho)
    e4 = ar.leer("calibracion_ps5")
    ar.fig_calibracion(e4, datos, parametros, cifras["calibracion"]["seleccion"], ancho=3.43, alto=2.62, diapositiva=True)
    (SALIDA / "fig_calibracion.pdf").unlink(missing_ok=True)
    for viejo in ("fig_curvas", "curvas_ps5", "curvas_gta6", "fig_densidad", "fig_topologia", "fig_duracion", "fig_escenarios",
                  "redes", "pew", "mezcla_vs_red_vieja"):
        for ext in ("png", "pdf"):
            (SALIDA / f"{viejo}.{ext}").unlink(missing_ok=True)
    print("figuras de diapositivas en", SALIDA)


if __name__ == "__main__":
    main()
