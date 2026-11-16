"""Reproduce los experimentos BehaviorSpace con la implementación en Python y escribe
tablas con el mismo formato que exporta NetLogo (datos/resultados_python/).

Los diseños (factores, niveles, réplicas y meses) se leen directamente del archivo
modelo/difusion_innovacion.nlogo, así que ambas implementaciones corren siempre los
mismos experimentos. Sirve para (a) probar la cadena de análisis sin NetLogo y
(b) verificar la implementación: los resultados oficiales son los de NetLogo.

Uso:  python generar_resultados_python.py [réplicas] [experimento ...]
"""
import csv
import itertools
import re
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verificacion_python import crear_red, propiedades, simular  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
MODELO = RAIZ / "modelo" / "difusion_innovacion.nlogo"
SALIDA = RAIZ / "datos" / "resultados_python"
METRICAS = ["porcentaje-adopcion", "nuevos", "mes-50", "pico-nuevos", "mes-pico", "grado-medio", "agrupamiento",
            "camino-medio", "porcentaje-bass"]
CON_ESTRUCTURA = {"topologia_x_publicidad", "calibracion_ps5"}   # experimentos que miden agrupamiento y caminos


def valor(texto):
    """Convierte un valor de BehaviorSpace ("&quot;aleatoria&quot;", true, 0.02) al tipo de Python."""
    if texto.startswith('"'):
        return texto.strip('"')
    if texto in ("true", "false"):
        return texto == "true"
    numero = float(texto)
    return int(numero) if numero.is_integer() and "." not in texto else numero


def casos():
    """Parámetros de cada caso tal como los fija el procedimiento `aplicar-caso` del modelo."""
    texto = MODELO.read_text(encoding="utf-8")
    bloque = re.search(r"to aplicar-caso(.*?)\nend", texto, re.S).group(1)
    salida = {}
    for nombre, cuerpo in re.findall(r'if caso = "([^"]+)" \[(.*?)\n  \]', bloque, re.S):
        salida[nombre] = {v: valor(x) for v, x in re.findall(r"set ([\w\-?]+) ([\d.]+)", cuerpo)}
    return salida


def experimentos():
    """Diseños BehaviorSpace del modelo: {nombre: (réplicas, meses, {variable: [niveles]})} en orden de variables."""
    texto = MODELO.read_text(encoding="utf-8")
    xml = re.search(r"<experiments>.*</experiments>", texto, re.S).group(0)
    salida = {}
    for exp in ET.fromstring(xml):
        factores = {e.get("variable"): [valor(v.get("value")) for v in e.findall("value")]
                    for e in exp.findall("enumeratedValueSet")}
        salida[exp.get("name")] = (int(exp.get("repetitions")), int(exp.find("timeLimit").get("steps")), factores)
    return salida


def correr(args):
    corrida, columnas, cfg, con_estructura = args
    rng = np.random.default_rng(1000 + corrida)
    g = crear_red(cfg["tipo-red"], cfg["poblacion"], cfg["grado-promedio"], cfg["prob-reconexion"], rng)
    grado, agrup, camino = propiedades(g) if con_estructura else (np.mean([d for _, d in g.degree()]), np.nan, np.nan)
    curva, nuevos = simular(n=cfg["poblacion"], k=cfg["grado-promedio"], potencial=cfg["potencial-mercado"],
                            iniciales=cfg["adoptantes-iniciales"], p=cfg["p-publicidad"], q=cfg["q-imitacion"],
                            campana=cfg["campaña?"], duracion=cfg["duracion-campaña"], meses=cfg["meses"], rng=rng, grafo=g)
    # referencia agregada de Bass con paso mensual (igual que en NetLogo)
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
        filas.append([corrida] + [columnas[v] for v in columnas] + [t, curva[t], nuevos[t], mes50, pico, mes_pico,
                                                           grado, agrup, "false" if np.isnan(camino) else camino, bass[t]])
    return filas


def main():
    reps_arg = int(sys.argv[1]) if len(sys.argv) > 1 else None
    pedidos = sys.argv[2:]
    SALIDA.mkdir(parents=True, exist_ok=True)
    presets = casos()
    for nombre, (reps, meses, factores) in experimentos().items():
        if pedidos and nombre not in pedidos:
            continue
        reps = reps_arg or reps
        variables = list(factores)
        tareas, corrida = [], 0
        for combinacion in itertools.product(*factores.values()):
            cfg = dict(zip(variables, combinacion))
            parametros = {**cfg, **presets.get(cfg.get("caso"), {})}   # como `aplicar-caso` en setup
            parametros["meses"] = min(parametros["meses"], meses)
            for _ in range(reps):
                corrida += 1
                tareas.append((corrida, cfg, parametros, nombre in CON_ESTRUCTURA))
        with ProcessPoolExecutor() as ex:
            resultados = list(ex.map(correr, tareas, chunksize=4))
        with open(SALIDA / f"{nombre}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, quoting=csv.QUOTE_ALL)
            w.writerow(["Resultados generados con la implementación de referencia en Python (verificacion_python.py)"])
            w.writerow(["difusion_innovacion.nlogo"]); w.writerow([nombre]); w.writerow([""])
            w.writerow(["min-pxcor", "max-pxcor", "min-pycor", "max-pycor"]); w.writerow([-30, 30, -30, 30])
            w.writerow(["[run number]"] + variables + ["[step]"] + METRICAS)
            for filas in resultados:
                for fila in filas:
                    w.writerow([str(v).lower() if isinstance(v, bool) else v for v in fila])
        print(nombre, "corridas:", corrida)


if __name__ == "__main__":
    main()
