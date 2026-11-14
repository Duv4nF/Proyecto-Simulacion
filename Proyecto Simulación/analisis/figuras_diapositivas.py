"""Figuras para la presentación: las mismas gráficas del artículo con tipografía
más grande, más ilustraciones de las redes del modelo (estilo NetLogo) y la
serie real por sí sola. Se escriben en analisis/figuras/diapositivas/.

Uso:  python3 figuras_diapositivas.py [carpeta_resultados]
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analisis_resultados as ar  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "analisis" / "figuras" / "diapositivas"
SALIDA.mkdir(parents=True, exist_ok=True)
ar.FIG = SALIDA  # las funciones de análisis guardan aquí
ar.ESCALA = 1.2
ar.ALTO = 1.3

plt.rcParams.update({
    "font.size": 14, "axes.titlesize": 14.5, "axes.labelsize": 14, "legend.fontsize": 12.5,
    "xtick.labelsize": 12.5, "ytick.labelsize": 12.5, "savefig.transparent": True,
})

NEGRO, NODO, ADOPTANTE, NUEVO, ENLACE = "#141A21", "#9AA5B1", "#1FC2BC", "#F08A3C", "#3A4653"


def red_estilo_netlogo(tipo, n=140, k=6, semilla=3, fraccion=0.22, ax=None, titulo=None):
    """Dibuja una red pequeña con la estética del modelo: fondo oscuro, adoptantes en turquesa."""
    rng = np.random.default_rng(semilla)
    g = ar_red(tipo, n, k, rng)
    if tipo == "mundo pequeño":
        pos = nx.circular_layout(g)
    else:
        pos = nx.spring_layout(g, seed=semilla, k=1.4 / np.sqrt(n))
    grados = dict(g.degree())
    # adoptantes: un grupo contiguo (como en una difusión real) más algunos aislados
    semilla_nodo = max(grados, key=grados.get) if tipo == "libre de escala" else int(rng.integers(n))
    orden = list(nx.bfs_tree(g, semilla_nodo)) if nx.is_connected(g) else list(g.nodes)
    adoptantes = set(orden[: int(fraccion * n)])
    nuevos = set(orden[int(fraccion * n): int(fraccion * n) + max(2, n // 40)])
    colores = [NUEVO if v in nuevos else ADOPTANTE if v in adoptantes else NODO for v in g.nodes]
    tam = [28 + 9 * grados[v] for v in g.nodes]
    ax = ax or plt.gca()
    ax.set_facecolor(NEGRO)
    nx.draw_networkx_edges(g, pos, ax=ax, edge_color=ENLACE, width=0.8, alpha=0.9)
    nx.draw_networkx_nodes(g, pos, ax=ax, node_color=colores, node_size=tam, linewidths=0)
    ax.set_axis_off()
    if titulo:
        ax.set_title(titulo, color="#E6EBF0", fontsize=14, pad=8)


def ar_red(tipo, n, k, rng):
    semilla = int(rng.integers(1 << 31))
    if tipo == "aleatoria":
        return nx.gnp_random_graph(n, k / (n - 1), seed=semilla)
    if tipo == "mundo pequeño":
        return nx.watts_strogatz_graph(n, k, 0.1, seed=semilla)
    return nx.barabasi_albert_graph(n, k // 2, seed=semilla)


def fig_redes():
    fig, ejes = plt.subplots(1, 3, figsize=(12, 4.2))
    fig.patch.set_facecolor(NEGRO)
    for eje, (tipo, titulo) in zip(ejes, (("aleatoria", "aleatoria (Erdős–Rényi)"), ("mundo pequeño", "mundo pequeño (Watts–Strogatz)"),
                                          ("libre de escala", "libre de escala (Barabási–Albert)"))):
        red_estilo_netlogo(tipo, ax=eje, titulo=titulo)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.9, bottom=0.02, wspace=0.05)
    fig.savefig(SALIDA / "redes.png", dpi=220, facecolor=NEGRO, transparent=False)
    plt.close(fig)


def fig_portada():
    fig, eje = plt.subplots(figsize=(7.5, 7.5))
    fig.patch.set_facecolor(NEGRO)
    red_estilo_netlogo("libre de escala", n=260, k=4, semilla=11, fraccion=0.3, ax=eje)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(SALIDA / "portada_red.png", dpi=200, facecolor=NEGRO, transparent=False)
    plt.close(fig)


def fig_mezcla_vs_red():
    """Mezcla perfecta (Bass) frente a red social: el mismo número de agentes, otra estructura."""
    fig, ejes = plt.subplots(1, 2, figsize=(9, 4.2))
    fig.patch.set_facecolor(NEGRO)
    rng = np.random.default_rng(5)
    n = 26
    g = nx.complete_graph(n)
    pos = nx.circular_layout(g)
    ejes[0].set_facecolor(NEGRO)
    nx.draw_networkx_edges(g, pos, ax=ejes[0], edge_color=ENLACE, width=0.4, alpha=0.6)
    nx.draw_networkx_nodes(g, pos, ax=ejes[0], node_color=[ADOPTANTE if i < 6 else NODO for i in range(n)], node_size=110, linewidths=0)
    ejes[0].set_axis_off(); ejes[0].set_title("modelo agregado: todos influyen sobre todos", color="#E6EBF0", fontsize=13, pad=8)
    red_estilo_netlogo("mundo pequeño", n=26, k=4, semilla=5, fraccion=0.23, ax=ejes[1], titulo="modelo en red: solo influyen los vecinos")
    fig.subplots_adjust(left=0.01, right=0.99, top=0.9, bottom=0.02, wspace=0.08)
    fig.savefig(SALIDA / "mezcla_vs_red.png", dpi=220, facecolor=NEGRO, transparent=False)
    plt.close(fig)


def fig_pew(datos, parametros):
    fig, eje = plt.subplots(figsize=(7.2, 4.0))
    marcas = {"entrenamiento": ("o", "full"), "validacion": ("s", "none"), "prueba": ("^", "none")}
    etiquetas = {"entrenamiento": "entrenamiento (2011–2016, 26 obs.)", "validacion": "validación (2018–2021, 3 obs.)", "prueba": "prueba (2023–2026, 4 obs.)"}
    for nombre, (mk, relleno) in marcas.items():
        a, b = parametros["particion"][nombre]["inicio"], parametros["particion"][nombre]["fin"]
        d = datos[(datos.anio_decimal >= a) & (datos.anio_decimal < b)]
        eje.plot(d.anio_decimal, d.adopcion_pct, mk, ms=7, color=ar.TINTA, fillstyle=relleno, mew=1.4, ls="none", label=etiquetas[nombre])
        if nombre != "entrenamiento":
            eje.axvspan(a, min(b, 2027), color=ar.REJILLA, alpha=0.45, lw=0)
    eje.set_xlim(2010.5, 2027)
    eje.set_ylim(0, 100)
    eje.set_ylabel("adultos con smartphone (%)")
    eje.set_xticks(range(2011, 2027, 3))
    eje.legend(loc="lower right")
    ar.guardar(fig, "pew")


def main():
    carpeta = sys.argv[1] if len(sys.argv) > 1 else "resultados"
    ar.RES = RAIZ / "datos" / carpeta
    parametros = pd.read_json(RAIZ / "analisis" / "parametros_calibrados.json", typ="series").to_dict()
    datos = pd.read_csv(RAIZ / "datos" / "pew_smartphone_eeuu.csv")

    fig_redes()
    fig_portada()
    fig_mezcla_vs_red()
    fig_pew(datos, parametros)

    e1 = ar.leer("publicidad_x_densidad")
    f1 = ["q-imitacion", "campaña?", "grado-promedio"]
    r1 = ar.resumen(ar.finales(e1, f1), f1)
    ar.fig_curvas(e1)
    ar.fig_densidad(r1)
    e2 = ar.leer("topologia_x_publicidad")
    f2 = ["q-imitacion", "campaña?", "tipo-red"]
    ar.fig_topologia(ar.resumen(ar.finales(e2, f2), f2))
    e3 = ar.leer("duracion_campana")
    f3 = ["q-imitacion", "duracion-campaña"]
    ar.fig_duracion(ar.resumen(ar.finales(e3, f3), f3))
    e4 = ar.leer("calibracion_pew")
    import json
    cifras = json.loads((RAIZ / "analisis" / "resumen_resultados.json").read_text())
    ar.fig_calibracion(e4, datos, parametros, cifras["calibracion"]["seleccion"])
    print("figuras de diapositivas en", SALIDA)


if __name__ == "__main__":
    main()
