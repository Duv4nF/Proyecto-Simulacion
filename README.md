# Publicidad y redes sociales en la difusión de innovaciones: PS5 y GTA 6 — proyecto 14, Simulación Computacional

Modelo basado en agentes (NetLogo) de la difusión de innovaciones en una red social, aplicado a dos casos: la **PS5** como tecnología nueva, calibrada y validada con la serie oficial de ventas de Sony (2020–2026), y **GTA 6** como innovación que se difunde entre los dueños de la PS5, con parámetros por analogía con el lanzamiento de GTA V. Integrantes: Jesus Gregorio Delgado, David Andres Monroy Aguiar, Duvan Felipe Baquero Cerquera.

## Contenido

| Carpeta | Contenido |
|---|---|
| `modelo/` | `difusion_innovacion.nlogo`: código, interfaz (con el selector de caso PS5 / GTA 6 / libre), pestaña Info y los 4 experimentos BehaviorSpace. `correr_experimentos.bat/.sh` los corren sin abrir la interfaz. |
| `datos/` | `ps5_ventas_sie.csv` (unidades de PS5 por trimestre fiscal, Sony) y `gtav_ventas_taketwo.csv` (ventas de GTA V, Take-Two y Guinness). `resultados/` tiene las tablas de NetLogo; `resultados_python/`, las de la réplica en Python. |
| `analisis/` | `datos_ps5.py` (serie, universo y partición), `calibracion_bass.py` (p, q, m de la PS5), `analogia_gtav.py` (parámetros de GTA 6), `analisis_resultados.py` (medidas, figuras, tablas y cifras), `figuras_diapositivas.py`, `verificacion_python.py` y `generar_resultados_python.py` (réplica independiente). `fuentes/` trae IBM Plex Sans (SIL OFL) para que las figuras salgan iguales en cualquier equipo. |
| `articulo/` | `main.tex` + `referencias.bib` + `figuras/` + `tablas/` (formato LNCS, 8 páginas con referencias). `articulo.pdf` es una compilación local con la clase oficial `llncs`. |
| `presentacion/` | `presentacion.pdf` (19 diapositivas), `presentacion_notas.pdf` (una página de notas del orador por diapositiva) y su fuente `presentacion.tex` (Beamer, XeLaTeX). `presentacion.pptx` es la misma presentación en PowerPoint, editable (texto, cajas, flechas y tabla nativos), con las notas del orador y las fuentes incrustadas; la genera `pptx/generar_pptx.py`. |
| `sustentacion/` | `guion_sustentacion.md` (reparto, tiempos y texto por diapositiva) y `guia_estudio.html` (guía completa para estudiar; también está en Google Drive). Se generan con `rellenar.py` desde `plantillas/`. |

## Cómo abrir y usar el modelo

1. Instalar NetLogo 6.4 o posterior (https://ccl.northwestern.edu/netlogo/). La extensión `nw` viene incluida.
2. Abrir `modelo/difusion_innovacion.nlogo`, elegir el `caso` (PS5, GTA 6 o libre), pulsar **configurar** y **simular**. La pestaña **Info** explica cada control.
3. Experimentos: **Herramientas → BehaviorSpace** muestra `calibracion_ps5`, `publicidad_x_densidad`, `topologia_x_publicidad` y `duracion_campana`. Sin interfaz:
   - Windows: `modelo\correr_experimentos.bat "C:\Program Files\NetLogo 7.0.4" 10` (el tercer argumento opcional es la lista de experimentos; sin ruta usa la versión más reciente instalada). El script llama al Java de NetLogo porque el `netlogo-headless.bat` de NetLogo 7.0.4 falla con rutas que tienen espacios.
   - Linux/Mac: `NETLOGO=/ruta/a/NetLogo bash modelo/correr_experimentos.sh 4`.
   Las tablas quedan en `datos/resultados/` (alrededor de una hora con 10 hilos).

## Cómo regenerar todo

Requiere Python 3 con `numpy pandas scipy matplotlib networkx pymupdf`. Las cifras del artículo, las diapositivas, el guion y la guía salen de `articulo/tablas/cifras.tex`, así que al cambiar los resultados se actualizan solas.

```bash
python analisis/calibracion_bass.py              # p, q, m de la PS5      -> analisis/parametros_calibrados.json
python analisis/analogia_gtav.py                 # parámetros de GTA 6    -> analisis/parametros_gta6.json
# correr los experimentos de NetLogo (arriba)     -> datos/resultados/
python analisis/generar_resultados_python.py     # réplica independiente  -> datos/resultados_python/
python analisis/verificacion_python.py           # red completa frente a Bass -> analisis/verificacion_bass.json
python analisis/sensibilidad.py                  # supuestos: GTA 6 más grande, más imitación, semilla de la PS5 -> analisis/sensibilidad.json
python analisis/analisis_resultados.py           # figuras, tablas, cifras y verificación NetLogo vs. Python
python analisis/figuras_diapositivas.py          # figuras de las diapositivas
cp analisis/figuras/fig_calibracion.pdf analisis/figuras/fig_escenarios.pdf articulo/figuras/
python sustentacion/rellenar.py                  # guion y guía de estudio con las cifras finales
```

Los valores de `aplicar-caso` en el modelo (p, q, m, adoptantes iniciales y meses de cada caso) son los de `parametros_calibrados.json` y `parametros_gta6.json` redondeados; si se recalibra, hay que actualizarlos a mano.

Presentación (desde `presentacion/`, con XeLaTeX y los paquetes `beamer`, `fontspec`, `pgf` y `listings`):

```bash
xelatex presentacion.tex
xelatex -jobname=presentacion_notas "\def\connotas{}\input{presentacion}"
```

El esquema del sistema (`articulo/figuras/esquema_sistema.tex`) también se compila con XeLaTeX.

Versión en PowerPoint (Windows, con PowerPoint y `pip install python-pptx fonttools`; instalar antes las fuentes de `analisis/fuentes` y `presentacion/pptx/fuentes`):

```bash
python presentacion/pptx/generar_pptx.py . presentacion/sin_fuentes.pptx
powershell -File presentacion/pptx/incrustar.ps1 -entrada "$PWD/presentacion/sin_fuentes.pptx" -salida "$PWD/presentacion/presentacion.pptx"
```

El generador copia la posición de cada elemento del PDF de Beamer (texto, interlineado, kerning, fórmulas), así que si cambian las cifras o el texto hay que actualizarlo también en `generar_pptx.py`. `incrustar.ps1` guarda el archivo desde PowerPoint con las fuentes completas incrustadas.

## Cómo compilar el artículo en Overleaf

1. Nuevo proyecto desde la plantilla **Springer Lecture Notes in Computer Science** (https://www.overleaf.com/latex/templates/springer-lecture-notes-in-computer-science/kzwwpvhwnvfj).
2. Subir `main.tex`, `referencias.bib`, la carpeta `tablas/` y, dentro de `figuras/`, `esquema_sistema.pdf`, `fig_calibracion.pdf` y `fig_escenarios.pdf`. Borrar el `samplepaper.tex` de la plantilla y compilar `main.tex` con pdfLaTeX.
3. El estilo bibliográfico `splncs04.bst` ya viene con la plantilla.

## Estado y pendientes

Ver `PREGUNTAS_PENDIENTES.md`.
