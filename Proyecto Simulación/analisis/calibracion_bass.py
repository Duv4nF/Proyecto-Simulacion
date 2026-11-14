"""Calibración del modelo agregado de Bass con la serie de adopción de smartphones (Pew).

Partición cronológica del conjunto de datos:
  - entrenamiento : 2011 – 2016   (fase de crecimiento; se estiman p, q, m)
  - validación    : 2018 – 2021   (selección de la estructura de red del ABM)
  - prueba        : 2023 – 2026   (evaluación final, no se usa para ajustar nada)

El origen temporal t = 0 se fija en junio de 2007 (lanzamiento del iPhone), de modo
que el modelo describe la difusión desde el inicio de la categoría.

Salida: analisis/parametros_calibrados.json con p, q, m anuales y sus equivalentes
mensuales (p/12, q/12), que son los valores por defecto del modelo NetLogo.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

RAIZ = Path(__file__).resolve().parents[1]
T0 = 2007.46  # junio de 2007

PARTICION = {  # intervalos [inicio, fin) en año decimal
    "entrenamiento": (2011.0, 2017.0),
    "validacion": (2018.0, 2022.0),
    "prueba": (2023.0, 2027.0),
}


def bass_F(t, p, q, m):
    """Fracción acumulada de adoptantes del modelo de Bass (forma cerrada)."""
    e = np.exp(-(p + q) * t)
    return m * (1 - e) / (1 + (q / p) * e)


def rmse(y, yhat):
    return float(np.sqrt(np.mean((y - yhat) ** 2)))


def mape(y, yhat):
    return float(np.mean(np.abs((y - yhat) / y)) * 100)


def main():
    datos = pd.read_csv(RAIZ / "datos" / "pew_smartphone_eeuu.csv")
    datos["t"] = datos["anio_decimal"] - T0
    datos["F"] = datos["adopcion_pct"] / 100

    def subconjunto(nombre):
        a, b = PARTICION[nombre]
        return datos[(datos.anio_decimal >= a) & (datos.anio_decimal < b)]

    ent, val, pru = (subconjunto(k) for k in ("entrenamiento", "validacion", "prueba"))

    # El potencial de mercado m no es identificable desde la fase de crecimiento
    # (el ajuste libre lo lleva a la cota superior), así que se trata como
    # hiperparámetro: para cada m candidato se estiman p y q en entrenamiento y
    # se elige el m con menor RMSE en validación.
    rejilla_m = np.round(np.arange(0.80, 1.0001, 0.01), 2)
    candidatos = []
    for m_c in rejilla_m:
        (p_c, q_c), cov_c = curve_fit(
            lambda t, p, q: bass_F(t, p, q, m_c), ent.t.values, ent.F.values,
            p0=(0.02, 0.4), bounds=([1e-4, 0.0], [0.5, 2.0]),
        )
        yhat_val = bass_F(val.t.values, p_c, q_c, m_c) * 100
        candidatos.append((rmse(val.adopcion_pct.values, yhat_val), m_c, p_c, q_c, cov_c))
    rmse_val, m, p, q, cov = min(candidatos, key=lambda c: c[0])
    err = np.sqrt(np.diag(cov))

    resumen = {
        "origen_temporal": T0,
        "anual": {"p": p, "q": q, "m": m, "error_estandar": dict(zip("pq", err.tolist()))},
        "mensual": {"p": p / 12, "q": q / 12, "m": m},
        "seleccion_m": [{"m": float(c[1]), "RMSE_validacion": c[0]} for c in candidatos],
        "tiempo_pico_anios": float(np.log(q / p) / (p + q)),
        "particion": {k: {"inicio": a, "fin": b} for k, (a, b) in PARTICION.items()},
        "n_observaciones": {"entrenamiento": len(ent), "validacion": len(val), "prueba": len(pru)},
        "desempeno_bass": {},
    }
    for nombre, sub in (("entrenamiento", ent), ("validacion", val), ("prueba", pru)):
        yhat = bass_F(sub.t.values, p, q, m) * 100
        resumen["desempeno_bass"][nombre] = {
            "RMSE_pct": rmse(sub.adopcion_pct.values, yhat),
            "MAPE_pct": mape(sub.adopcion_pct.values, yhat),
        }

    salida = RAIZ / "analisis" / "parametros_calibrados.json"
    salida.write_text(json.dumps(resumen, indent=2, ensure_ascii=False))
    print(json.dumps(resumen, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
