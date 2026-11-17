"""Parámetros de GTA 6 por analogía con el lanzamiento de GTA V (método de "guessing by analogy").

GTA 6 todavía no tiene ventas publicadas, así que sus parámetros se toman del producto
análogo más cercano: GTA V (17-sep-2013, PS3 y Xbox 360). Las cifras oficiales de
Take-Two (unidades acumuladas vendidas a tiendas) se expresan como fracción de la base
instalada de ambas consolas en ese momento (80 + 80 millones) y se ajusta la misma
recursión mensual de Bass que usa el modelo:

    F(t+1) = F(t) + (p + q F(t)) (m - F(t)),   F(0) = compradores del día del lanzamiento

con F(0) = las unidades de las primeras 24 horas (11,21 millones, Guinness World Records),
m = la meseta del primer año (34 millones) y q = la imitación calibrada con la serie de PS5.
Se estima p, la influencia externa de la campaña de lanzamiento. Sin fijar F(0) los datos no
separan F(0) de p, porque la primera cifra oficial llega seis semanas después del lanzamiento.

Salida: analisis/parametros_gta6.json (valores que usan los experimentos de NetLogo).
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

sys.path.insert(0, str(Path(__file__).resolve().parent))
import datos_ps5 as dp  # noqa: E402

RAIZ = dp.RAIZ
LANZAMIENTO_GTAV = pd.Timestamp("2013-09-17")
BASE_M = {"PS3": 80.0, "Xbox 360": 80.0}      # Sony (2-nov-2013) y Microsoft (17-oct-2013), millones
HORIZONTE = 24                                 # meses: período de evaluación de GTA 6


def recursion(F0, p, q, m, meses):
    F = [F0]
    for _ in range(meses):
        F.append(F[-1] + (p + q * F[-1]) * (m - F[-1]))
    return np.array(F)


def main():
    pq5 = json.loads((RAIZ / "analisis" / "parametros_calibrados.json").read_text(encoding="utf-8"))
    q = round(pq5["mensual"]["q"], 4)                   # imitación calibrada con PS5 (mensual)
    base = sum(BASE_M.values())
    d = pd.read_csv(RAIZ / "datos" / "gtav_ventas_taketwo.csv", parse_dates=["fecha"])
    d["t_meses"] = (d["fecha"] - LANZAMIENTO_GTAV).dt.days / dp.DIAS_MES
    d["F"] = d["unidades_acumuladas_M"] / base
    dia1 = d[d["tipo"] == "primeras 24 horas"].iloc[0]
    F0 = float(dia1["F"])                                # compradores del primer día
    obs = d[d["tipo"] == "sell-in"]
    m = float(obs["F"].max())                            # meseta del primer año

    def residuos(x):
        curva = recursion(F0, x[0], q, m, 14)
        return np.interp(obs["t_meses"], np.arange(15), curva) - obs["F"]

    ajuste = least_squares(residuos, x0=(0.3,), bounds=([0.0], [1.0]))
    p = float(ajuste.x[0])
    rmse_pp = float(100 * np.sqrt(np.mean(ajuste.fun ** 2)))

    salida = {
        "analogo": "Grand Theft Auto V (PS3 y Xbox 360), lanzado el 17-sep-2013",
        "base_instalada_M": BASE_M,
        "observaciones": [{"fecha": str(f.date()), "tipo": ti, "t_meses": round(t, 2), "unidades_M": u, "fraccion_base": round(F, 4)}
                          for f, ti, t, u, F in zip(d["fecha"], d["tipo"], d["t_meses"], d["unidades_acumuladas_M"], d["F"])],
        "ajuste": {"F0": float(F0), "p_mes": float(p), "q_mes": q, "m": m, "rmse_pp": rmse_pp},
        # valores redondeados que usan los experimentos (NetLogo y la réplica en Python)
        "gta6": {
            "potencial_mercado_pct": round(100 * m),
            "adoptantes_iniciales_pct": round(100 * F0),             # entero, como m
            "p_mes": round(float(p), 2),
            "q_mes": [q, round(2 * q, 4)],                           # calibrada con PS5 y el doble (sensibilidad)
            "horizonte_meses": HORIZONTE,
        },
    }
    (RAIZ / "analisis" / "parametros_gta6.json").write_text(json.dumps(salida, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(salida, indent=2, ensure_ascii=False))
    curva = recursion(F0, p, q, m, 14)
    print("curva ajustada (% de la base), meses 0-6:", np.round(100 * curva[:7], 1))


if __name__ == "__main__":
    main()
