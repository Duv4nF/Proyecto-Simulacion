#!/bin/bash
# Corre los cuatro experimentos BehaviorSpace del modelo sin abrir la interfaz y
# escribe las tablas en datos/resultados/. Luego, para regenerar figuras, tablas y
# cifras del artículo y de la presentación:
#     python3 analisis/analisis_resultados.py
#     python3 analisis/figuras_diapositivas.py
#
# Uso:  NETLOGO=/ruta/a/NetLogo bash modelo/correr_experimentos.sh [hilos] ["experimento1 experimento2"]
# Sin lista de experimentos corre los cuatro. En Windows: correr_experimentos.bat (ver README.md).
set -e
NETLOGO="${NETLOGO:-$HOME/NetLogo-6.4.0}"
HILOS="${1:-2}"
EXPS="${2:-calibracion_ps5 publicidad_x_densidad topologia_x_publicidad duracion_campana}"
AQUI="$(cd "$(dirname "$0")" && pwd)"
SALIDA="$AQUI/../datos/resultados"
mkdir -p "$SALIDA"
for EXP in $EXPS; do
  echo "== $EXP"
  "$NETLOGO/netlogo-headless.sh" --model "$AQUI/difusion_innovacion.nlogo" \
      --experiment "$EXP" --table "$SALIDA/$EXP.csv" --threads "$HILOS"
done
echo "listo: $SALIDA"
