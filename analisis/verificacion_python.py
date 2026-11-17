"""Implementación independiente (Python + networkx) de la misma regla de adopción del
modelo NetLogo. La usan generar_resultados_python.py (réplica de los experimentos, para
comparar ambas implementaciones) y sensibilidad.py.

Ejecutado solo, hace la verificación analítica: con la red completa (todos conectados
con todos) la regla debe recuperar en promedio la recursión mensual de Bass que NetLogo
integra como referencia. Imprime la diferencia máxima para los casos PS5 y GTA 6.

Uso:  python verificacion_python.py
"""
from pathlib import Path

import networkx as nx
import numpy as np

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


def simular(tipo="mundo pequeño", n=1000, k=16, beta=0.1, potencial=100.0, iniciales=2.5,
            p=0.0081, q=0.0375, campana=True, duracion=240, meses=72, rng=None, grafo=None):
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


def bass_mensual(F0, p, q, m, meses):
    """La recursión de Bass que NetLogo integra como referencia (porcentaje-bass)."""
    F = [F0]
    for _ in range(meses):
        F.append(F[-1] + (p + q * F[-1]) * (m - F[-1]))
    return 100 * np.array(F)


def main():
    n = 1000
    completa = nx.complete_graph(n)
    casos = {"PS5": dict(p=0.0081, q=0.0375, potencial=100, iniciales=2.5, meses=72),
             "GTA 6": dict(p=0.69, q=0.0375, potencial=21, iniciales=7, meses=24)}
    rng = np.random.default_rng(2026)
    salida = {}
    for nombre, c in casos.items():
        curvas = [simular(n=n, grafo=completa, rng=rng, **c)[0] for _ in range(20)]
        media = np.mean(curvas, axis=0)
        bass = bass_mensual(media[0] / 100, c["p"], c["q"], c["potencial"] / 100, c["meses"])
        salida[nombre] = {"diferencia_maxima_pp": float(np.abs(media - bass).max()), "final_agentes": float(media[-1]),
                          "final_bass": float(bass[-1])}
        print(f"{nombre}: red completa frente a Bass, diferencia máxima {np.abs(media - bass).max():.2f} puntos "
              f"(final {media[-1]:.1f} % frente a {bass[-1]:.1f} %)")
    import json
    (RAIZ / "analisis" / "verificacion_bass.json").write_text(json.dumps(salida, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
