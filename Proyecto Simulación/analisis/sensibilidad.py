"""Análisis de sensibilidad de los supuestos que no salen de la calibración (réplica en Python).

1. GTA 6 más grande que GTA V: los analistas esperan cerca del doble de lo que implica la analogía.
   Se duplican a la vez el potencial de mercado y los compradores del primer día.
2. GTA 6 con el doble de imitación (q fijado en el de la PS5 es un supuesto).
3. PS5 con otra semilla de adoptantes iniciales (1 %, 2,5 % y 5 %): el nivel "sin campaña"
   depende de cuántos empiezan, que no se calibra.

Todos en la red de los escenarios (mundo pequeño, k = 16), 30 réplicas.
Uso:  python analisis/sensibilidad.py      (escribe analisis/sensibilidad.json)
"""
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verificacion_python import simular  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
REPS = 30


def correr(args):
    m, iniciales, p, q, campana, duracion, k, meses, semilla = args
    curva, _ = simular(tipo="mundo pequeño", n=1000, k=k, beta=0.1, potencial=m, iniciales=iniciales, p=p, q=q,
                       campana=campana, duracion=duracion, meses=meses, rng=np.random.default_rng(semilla))
    return curva[-1]


def media(ex, m, ini, p, q, campana, duracion, meses, semilla0, k=16):
    return float(np.mean(list(ex.map(correr, [(m, ini, p, q, campana, duracion, k, meses, semilla0 + i) for i in range(REPS)]))))


def main():
    g = json.loads((RAIZ / "analisis" / "parametros_gta6.json").read_text(encoding="utf-8"))["gta6"]
    pq5 = json.loads((RAIZ / "analisis" / "parametros_calibrados.json").read_text(encoding="utf-8"))["mensual"]
    p_g, q_g, m_g, ini_g, h_g = g["p_mes"], g["q_mes"][0], g["potencial_mercado_pct"], g["adoptantes_iniciales_pct"], g["horizonte_meses"]
    p_5, q_5 = round(pq5["p"], 4), round(pq5["q"], 4)
    salida = {}
    with ProcessPoolExecutor() as ex:
        d = {"potencial_pct": 2 * m_g, "iniciales_pct": 2 * ini_g}
        d["sin_k2"] = media(ex, 2 * m_g, 2 * ini_g, p_g, q_g, False, 240, h_g, 7000, k=2)
        d["sin_k16"] = media(ex, 2 * m_g, 2 * ini_g, p_g, q_g, False, 240, h_g, 7100)
        d["con_k16"] = media(ex, 2 * m_g, 2 * ini_g, p_g, q_g, True, 240, h_g, 7200)
        d["un_mes_k16"] = media(ex, 2 * m_g, 2 * ini_g, p_g, q_g, True, 1, h_g, 7300)
        d["fraccion_un_mes"] = 100 * (d["un_mes_k16"] - d["sin_k16"]) / (d["con_k16"] - d["sin_k16"])
        salida["gta_doble"] = d
        salida["gta_q_doble"] = {"q_mes": 2 * q_g,
                                 "sin_k16": media(ex, m_g, ini_g, p_g, 2 * q_g, False, 240, h_g, 7400),
                                 "con_k16": media(ex, m_g, ini_g, p_g, 2 * q_g, True, 240, h_g, 7500)}
        salida["ps5_semilla"] = {}
        for i, semilla in enumerate((1, 2.5, 5)):
            salida["ps5_semilla"][str(semilla)] = {"sin": media(ex, 100, semilla, p_5, q_5, False, 240, 72, 8000 + 100 * i),
                                                   "con": media(ex, 100, semilla, p_5, q_5, True, 240, 72, 9000 + 100 * i)}
    (RAIZ / "analisis" / "sensibilidad.json").write_text(json.dumps(salida, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(salida, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
