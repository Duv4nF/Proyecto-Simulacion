"""Calibración del modelo agregado de Bass con la serie oficial de ventas de PS5.

Partición cronológica (ver datos_ps5.py):
  - entrenamiento : dic-2020 – dic-2023  (se estiman p y q)
  - validación    : mar-2024 – dic-2024  (se elige m; luego, la estructura de red del ABM)
  - prueba        : mar-2025 – sep-2026  (evaluación final, no se usa para ajustar nada)

El origen temporal t = 0 es el lanzamiento (12-nov-2020) y el porcentaje de adopción se
mide sobre la base instalada de PS4 (117 millones).

Salida: analisis/parametros_calibrados.json con p, q, m anuales y sus equivalentes
mensuales (p/12, q/12), que son los valores del experimento de calibración en NetLogo.
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import curve_fit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import datos_ps5 as dp  # noqa: E402

RAIZ = dp.RAIZ
REJILLA_M = np.round(np.arange(0.80, 1.0001, 0.01), 2)


def bass_F(t, p, q, m):
    """Fracción acumulada de adoptantes del modelo de Bass (forma cerrada)."""
    e = np.exp(-(p + q) * t)
    return m * (1 - e) / (1 + (q / p) * e)


def rmse(y, yhat):
    return float(np.sqrt(np.mean((np.asarray(y) - np.asarray(yhat)) ** 2)))


def mape(y, yhat):
    y, yhat = np.asarray(y), np.asarray(yhat)
    return float(np.mean(np.abs((y - yhat) / y)) * 100)


def main():
    datos = dp.cargar()
    ent, val, pru = (dp.subconjunto(datos, k) for k in ("entrenamiento", "validacion", "prueba"))

    # El potencial de mercado m no es identificable desde la fase de crecimiento
    # (el ajuste libre lo lleva a la cota superior), así que se trata como
    # hiperparámetro: para cada m candidato se estiman p y q en entrenamiento y
    # se elige el m con menor RMSE en validación.
    candidatos = []
    for m_c in REJILLA_M:
        (p_c, q_c), cov_c = curve_fit(
            lambda t, p, q: bass_F(t, p, q, m_c), ent.t_anios.values, ent.adopcion_pct.values / 100,
            p0=(0.05, 0.4), bounds=([1e-4, 0.0], [0.5, 2.0]),
        )
        yhat_val = bass_F(val.t_anios.values, p_c, q_c, m_c) * 100
        candidatos.append((rmse(val.adopcion_pct.values, yhat_val), float(m_c), p_c, q_c, cov_c))
    rmse_val, m, p, q, cov = min(candidatos, key=lambda c: c[0])
    err = np.sqrt(np.diag(cov))
    (p_l, q_l, m_l), _ = curve_fit(bass_F, ent.t_anios.values, ent.adopcion_pct.values / 100,
                                   p0=(0.05, 0.4, 1.0), bounds=([1e-4, 0.0, 0.3], [0.5, 2.0, 3.0]))
    (p_t, q_t, m_t), _ = curve_fit(bass_F, datos.t_anios.values, datos.adopcion_pct.values / 100,
                                   p0=(0.05, 0.4, 1.0), bounds=([1e-4, 0.0, 0.3], [0.5, 2.0, 3.0]))

    resumen = {
        "lanzamiento": str(dp.LANZAMIENTO.date()),
        "origen_temporal": dp.anio_decimal(dp.LANZAMIENTO),
        "universo_millones": dp.UNIVERSO_M,
        "anual": {"p": p, "q": q, "m": m, "error_estandar": dict(zip("pq", err.tolist()))},
        "mensual": {"p": p / 12, "q": q / 12, "m": m},
        "m_en_borde_de_rejilla": bool(m in (REJILLA_M[0], REJILLA_M[-1])),
        "ajuste_libre_entrenamiento": {"p": float(p_l), "q": float(q_l), "m": float(m_l)},
        "ajuste_libre_toda_la_serie": {"p": float(p_t), "q": float(q_t), "m": float(m_t)},
        "seleccion_m": [{"m": c[1], "RMSE_validacion": c[0]} for c in candidatos],
        "tiempo_pico_anios": float(np.log(q / p) / (p + q)),
        "particion": {k: {"inicio": a, "fin": b} for k, (a, b) in dp.PARTICION.items()},
        "n_observaciones": {k: int((datos.particion == k).sum()) for k in dp.PARTICION},
        "desempeno_bass": {},
    }
    for nombre, sub in (("entrenamiento", ent), ("validacion", val), ("prueba", pru)):
        yhat = bass_F(sub.t_anios.values, p, q, m) * 100
        resumen["desempeno_bass"][nombre] = {
            "RMSE_pct": rmse(sub.adopcion_pct.values, yhat),
            "MAPE_pct": mape(sub.adopcion_pct.values, yhat),
        }
    t_ctrl = (dp.CONTROL["fecha"] - dp.LANZAMIENTO).days / 365.25
    resumen["control"] = {"fecha": str(dp.CONTROL["fecha"].date()),
                          "real_minimo_pct": 100 * dp.CONTROL["minimo_M"] / dp.UNIVERSO_M,
                          "bass_pct": float(100 * bass_F(t_ctrl, p, q, m))}

    salida = RAIZ / "analisis" / "parametros_calibrados.json"
    salida.write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in resumen.items() if k != "seleccion_m"}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
