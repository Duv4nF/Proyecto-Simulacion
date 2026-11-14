"""Reproduce los cuatro experimentos BehaviorSpace con la implementación en Python
y escribe tablas con el mismo formato que exporta NetLogo (datos/resultados_python/).

Sirve para (a) probar la cadena de análisis sin NetLogo y (b) comparar ambas
implementaciones. Los resultados oficiales del artículo son los de NetLogo.
"""
import csv
import itertools
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verificacion_python import crear_red, propiedades, simular  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "datos" / "resultados_python"
REPS = int(sys.argv[1]) if len(sys.argv) > 1 else 30

BASE = {"poblacion": 1000, "tipo-red": "mundo pequeño", "grado-promedio": 6, "prob-reconexion": 0.1,
        "potencial-mercado": 100, "adoptantes-iniciales": 2.5, "q-imitacion": 0.02, "campaña?": True,
        "p-publicidad": 0.0066, "duracion-campaña": 120, "meses": 120, "semilla": 0, "dibujar-red?": False}

EXPERIMENTOS = {
    "publicidad_x_densidad": {"grado-promedio": [2, 4, 6, 8, 12, 16], "q-imitacion": [0.02, 0.032], "campaña?": [False, True]},
    "topologia_x_publicidad": {"tipo-red": ["aleatoria", "mundo pequeño", "libre de escala"], "q-imitacion": [0.02, 0.032], "campaña?": [False, True]},
    "duracion_campana": {"duracion-campaña": [0, 6, 12, 24, 60, 120], "q-imitacion": [0.02, 0.032]},
    "calibracion_pew": {"tipo-red": ["aleatoria", "mundo pequeño", "libre de escala"], "grado-promedio": [4, 8, 16],
                        "potencial-mercado": [89], "adoptantes-iniciales": [0], "q-imitacion": [0.0202],
                        "duracion-campaña": [240], "meses": [228]},
}
METRICAS = ["porcentaje-adopcion", "nuevos", "mes-50", "pico-nuevos", "mes-pico", "grado-medio", "agrupamiento", "camino-medio", "porcentaje-bass"]
ORDEN_VARS = list(BASE)


def correr(args):
    corrida, cfg, con_estructura = args
    rng = np.random.default_rng(1000 + corrida)
    g = crear_red(cfg["tipo-red"], cfg["poblacion"], cfg["grado-promedio"], cfg["prob-reconexion"], rng)
    grado, agrup, camino = propiedades(g) if con_estructura else (np.mean([d for _, d in g.degree()]), np.nan, np.nan)
    curva, nuevos = simular(n=cfg["poblacion"], k=cfg["grado-promedio"], potencial=cfg["potencial-mercado"],
                            iniciales=cfg["adoptantes-iniciales"], p=cfg["p-publicidad"], q=cfg["q-imitacion"],
                            campana=cfg["campaña?"], duracion=cfg["duracion-campaña"], meses=cfg["meses"], rng=rng, grafo=g)
    # referencia agregada de Bass con paso mensual
    m, F, bass = cfg["potencial-mercado"] / 100, curva[0] / 100, [curva[0]]
    for t in range(cfg["meses"]):
        p_ef = cfg["p-publicidad"] if (cfg["campaña?"] and t < cfg["duracion-campaña"]) else 0.0
        F = F + (p_ef + cfg["q-imitacion"] * F) * (m - F)
        bass.append(100 * F)
    filas, mes50, pico, mes_pico = [], -1, 0, 0
    for t in range(cfg["meses"] + 1):
        if mes50 == -1 and curva[t] >= 50:
            mes50 = t
        if nuevos[t] > pico:
            pico, mes_pico = nuevos[t], t
        valores = [corrida] + [cfg[v] for v in ORDEN_VARS] + [t, curva[t], nuevos[t], mes50, pico, mes_pico,
                                                              grado, agrup, "false" if np.isnan(camino) else camino, bass[t]]
        filas.append(valores)
    return filas


def main():
    SALIDA.mkdir(parents=True, exist_ok=True)
    for nombre, factores in EXPERIMENTOS.items():
        claves = list(factores)
        tareas, corrida = [], 0
        for combinacion in itertools.product(*factores.values()):
            cfg = {**BASE, **dict(zip(claves, combinacion))}
            for _ in range(REPS):
                corrida += 1
                tareas.append((corrida, cfg, nombre in ("topologia_x_publicidad", "calibracion_pew")))
        with ProcessPoolExecutor() as ex:
            resultados = list(ex.map(correr, tareas, chunksize=4))
        with open(SALIDA / f"{nombre}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, quoting=csv.QUOTE_ALL)
            w.writerow(["Resultados generados con la implementación de referencia en Python (verificacion_python.py)"])
            w.writerow(["difusion_innovacion.nlogo"]); w.writerow([nombre]); w.writerow([""]); w.writerow(["min-pxcor", "max-pxcor", "min-pycor", "max-pycor"]); w.writerow([-30, 30, -30, 30])
            w.writerow(["[run number]"] + ORDEN_VARS + ["[step]"] + METRICAS)
            for filas in resultados:
                for fila in filas:
                    w.writerow([str(v).lower() if isinstance(v, bool) else v for v in fila])
        print(nombre, "corridas:", corrida)


if __name__ == "__main__":
    main()
