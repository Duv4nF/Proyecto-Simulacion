"""Implementación independiente (Python + networkx) de la misma regla de adopción
del modelo NetLogo. Sirve para verificar que los resultados del ABM no dependen
de la plataforma: con los mismos parámetros, ambas implementaciones deben dar
curvas estadísticamente equivalentes.

Uso:  python3 verificacion_python.py   (escribe datos/resultados/verificacion_python.csv)
"""
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
import scipy.sparse as sp

RAIZ = Path(__file__).resolve().parents[1]


def crear_red(tipo, n, k, beta, rng):
    semilla = int(rng.integers(1 << 31))
    if tipo == "aleatoria":
        return nx.gnp_random_graph(n, k / (n - 1), seed=semilla)
    if tipo == "mundo pequeño":
        return nx.watts_strogatz_graph(n, k, beta, seed=semilla)
    return nx.barabasi_albert_graph(n, k // 2, seed=semilla)


def propiedades(g):
    grado = np.mean([d for _, d in g.degree()])
    agrup = nx.average_clustering(g)
    camino = nx.average_shortest_path_length(g) if nx.is_connected(g) else np.nan
    return grado, agrup, camino


def simular(tipo="mundo pequeño", n=1000, k=6, beta=0.1, potencial=100.0, iniciales=2.5,
            p=0.0066, q=0.02, campana=True, duracion=120, meses=120, rng=None, grafo=None):
    """Devuelve la curva de adopción (%) en cada mes, de 0 a `meses`, y los nuevos por mes."""
    rng = rng or np.random.default_rng()
    g = grafo if grafo is not None else crear_red(tipo, n, k, beta, rng)
    A = nx.to_scipy_sparse_array(g, format="csr", dtype=float)
    grado = np.asarray(A.sum(axis=1)).ravel()
    grado_seguro = np.where(grado > 0, grado, 1.0)
    susceptible = rng.random(n) * 100 < potencial
    adoptante = np.zeros(n, dtype=bool)
    semillas = np.flatnonzero(susceptible)
    n_ini = min(round(iniciales / 100 * n), len(semillas))
    adoptante[rng.choice(semillas, n_ini, replace=False)] = True
    curva, nuevos_mes = [100 * adoptante.mean()], [0]
    for t in range(meses):
        p_ef = p if (campana and t < duracion) else 0.0
        f = (A @ adoptante.astype(float)) / grado_seguro        # fracción de vecinos adoptantes
        prob = 1 - (1 - p_ef) * (1 - q * f)
        decide = susceptible & ~adoptante & (rng.random(n) < prob)
        adoptante |= decide                                      # actualización sincrónica
        curva.append(100 * adoptante.mean())
        nuevos_mes.append(int(decide.sum()))
    return np.array(curva), np.array(nuevos_mes)


def main():
    rng = np.random.default_rng(2026)
    filas = []
    for campana in (False, True):
        for k in (2, 4, 6, 8, 12, 16):
            for rep in range(30):
                curva, _ = simular(k=k, campana=campana, rng=rng)
                filas.append({"campaña": campana, "grado-promedio": k, "rep": rep,
                              "adopcion_final": curva[-1], "adopcion_60": curva[60]})
    res = pd.DataFrame(filas)
    print(res.groupby(["campaña", "grado-promedio"])[["adopcion_final", "adopcion_60"]].agg(["mean", "std"]).round(1))
    salida = RAIZ / "datos" / "resultados" / "verificacion_python.csv"
    salida.parent.mkdir(parents=True, exist_ok=True)
    res.to_csv(salida, index=False)


if __name__ == "__main__":
    main()
