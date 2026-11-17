"""Serie real de la tecnología (PS5) y supuestos comunes a la calibración y al análisis.

La serie oficial de Sony Interactive Entertainment da las unidades de PS5 vendidas
(sell-in) por trimestre fiscal desde el lanzamiento. El porcentaje de adopción se
expresa sobre un universo fijado ANTES de ver los datos de prueba: la base instalada
de la generación anterior (PS4, más de 117 millones de unidades según la misma fuente).

Partición cronológica (fechas de cierre de trimestre, inclusivas):
  - entrenamiento : dic-2020 a dic-2023  (13 trimestres; se estiman p y q)
  - validación    : mar-2024 a dic-2024  (4 trimestres; se eligen m y la estructura de red)
  - prueba        : mar-2025 a sep-2026  (7 trimestres; solo evaluación)
"""
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
ARCHIVO = RAIZ / "datos" / "ps5_ventas_sie.csv"

LANZAMIENTO = pd.Timestamp("2020-11-12")    # PS5 en EE. UU. y Japón (t = 0 del modelo)
UNIVERSO_M = 117.0                          # base instalada de PS4, millones de unidades
DIAS_MES = 365.25 / 12
PARTICION = {
    "entrenamiento": ("2020-12-31", "2023-12-31"),
    "validacion": ("2024-03-31", "2024-12-31"),
    "prueba": ("2025-03-31", "2026-09-30"),
}
NOMBRE_PARTICION = {"entrenamiento": "entrenamiento", "validacion": "validación", "prueba": "prueba"}
# dato oficial posterior a la serie, usado solo como control: "más de 100 millones" al 10-nov-2026
CONTROL = {"fecha": pd.Timestamp("2026-11-10"), "minimo_M": 100.0}
MESES_CALIBRACION = 74                       # del lanzamiento a finales de 2026


def anio_decimal(fecha):
    """Año decimal de una fecha (para ejes y tablas)."""
    fecha = pd.Timestamp(fecha)
    inicio = pd.Timestamp(year=fecha.year, month=1, day=1)
    dias = 366 if fecha.is_leap_year else 365
    return fecha.year + (fecha - inicio).days / dias


def cargar():
    """Serie con unidades acumuladas, porcentaje de adopción, tiempos desde el lanzamiento y partición."""
    d = pd.read_csv(ARCHIVO, parse_dates=["fecha_cierre"])
    d["unidades_acumuladas_M"] = d["unidades_trimestre_M"].cumsum().round(1)
    d["adopcion_pct"] = 100 * d["unidades_acumuladas_M"] / UNIVERSO_M
    dias = (d["fecha_cierre"] - LANZAMIENTO).dt.days
    d["t_anios"] = dias / 365.25
    d["t_meses"] = dias / DIAS_MES
    d["anio_decimal"] = d["fecha_cierre"].map(anio_decimal)
    d["particion"] = ""
    for nombre, (a, b) in PARTICION.items():
        d.loc[(d.fecha_cierre >= a) & (d.fecha_cierre <= b), "particion"] = nombre
    return d


def subconjunto(d, nombre):
    return d[d.particion == nombre]
