# Difusión de una innovación en redes sociales — proyecto 14, Simulación Computacional

Modelo basado en agentes (NetLogo) de la adopción de una tecnología en una población conectada por una red social, calibrado con la serie de adopción de smartphones de Pew Research Center. Integrantes: Jesus Gregorio Delgado, David Andres Monroy Aguiar, Duvan Felipe Baquero Cerquera. Entrega: martes 17 de noviembre de 2026, 12:00.

## Qué hay en cada carpeta

| Carpeta | Contenido |
|---|---|
| `modelo/` | `difusion_innovacion.nlogo` (el modelo completo: código, interfaz, pestaña Info y los 4 experimentos BehaviorSpace) y los scripts `correr_experimentos.sh/.bat` para ejecutarlos sin abrir la interfaz. |
| `datos/` | `pew_smartphone_eeuu.csv` (serie real, 33 observaciones 2011–2026). `resultados/` recibe las tablas de NetLogo; `resultados_python/` tiene las de la réplica en Python. |
| `analisis/` | `calibracion_bass.py` (ajuste de p, q, m con partición), `analisis_resultados.py` (medidas, figuras y tablas del artículo), `figuras_diapositivas.py` (figuras de la presentación), `verificacion_python.py` y `generar_resultados_python.py` (réplica independiente del modelo). Salidas: `parametros_calibrados.json`, `resumen_resultados.json`, `figuras/`. |
| `articulo/` | `main.tex` + `referencias.bib` + `figuras/` + `tablas/` (formato LNCS). `vista_previa_main.pdf` es una compilación local aproximada; la definitiva se compila en Overleaf con la plantilla LNCS (ver abajo). |
| `presentacion/` | `presentacion.pptx` (18 diapositivas, con el guion en las notas del orador) y el script que la genera. |
| `sustentacion/` | `guion_sustentacion.md`: reparto de tiempos, texto por diapositiva, pasos de la demo y preguntas probables. |

## Cómo abrir y usar el modelo

1. Instalar NetLogo 6.4 (https://ccl.northwestern.edu/netlogo/; la 7.x también lo abre). La extensión `nw` viene incluida.
2. Abrir `modelo/difusion_innovacion.nlogo`, pulsar **configurar** y **simular**. La pestaña **Info** explica cada control y qué observar.
3. Experimentos: **Herramientas → BehaviorSpace** muestra los cuatro diseños (`publicidad_x_densidad`, `topologia_x_publicidad`, `duracion_campana`, `calibracion_pew`). Para correrlos todos sin interfaz:
   - Linux/Mac: `NETLOGO=/ruta/NetLogo-6.4.0 bash modelo/correr_experimentos.sh 4`
   - Windows: `modelo\correr_experimentos.bat "C:\Program Files\NetLogo 6.4.0" 4`
   Las tablas quedan en `datos/resultados/` (toman entre 30 y 90 minutos según el equipo).

## Cómo regenerar figuras, tablas, artículo y presentación

Requiere Python 3 con `numpy pandas scipy matplotlib networkx` y, para la presentación, Node con `pptxgenjs`.

```bash
python3 analisis/calibracion_bass.py              # p, q, m  → analisis/parametros_calibrados.json
python3 analisis/analisis_resultados.py           # lee datos/resultados/  → figuras, tablas y cifras del artículo
python3 analisis/figuras_diapositivas.py          # figuras de la presentación
PPTX_SKILL=<ruta al apply_theme.js> node presentacion/construir_presentacion.js
```

`analisis_resultados.py resultados_python` hace lo mismo con las tablas de la réplica en Python. Las cifras citadas en el artículo y en las diapositivas se leen de `articulo/tablas/cifras.tex`, así que al cambiar los resultados se actualizan solas.

## Cómo compilar el artículo en Overleaf

1. Nuevo proyecto desde la plantilla **Springer Lecture Notes in Computer Science** (https://www.overleaf.com/latex/templates/springer-lecture-notes-in-computer-science/kzwwpvhwnvfj).
2. Subir `main.tex`, `referencias.bib`, la carpeta `tablas/` y, dentro de `figuras/`, `esquema_sistema.pdf` más `fig_calibracion.pdf` y `fig_escenarios.pdf` (copias de `analisis/figuras/`; si se regeneran los resultados hay que volver a copiarlas). Borrar el `samplepaper.tex` de la plantilla y compilar `main.tex` con pdfLaTeX (compilador por defecto; el menú Recompile → Logs muestra si falta algo).
3. El estilo bibliográfico `splncs04.bst` ya viene con la plantilla.

## Estado y pendientes

Ver `PREGUNTAS_PENDIENTES.md`.
