;; ============================================================================
;; Difusión de innovación en una red social
;; Modelo basado en agentes — Simulación Computacional, Universidad de los Llanos
;;
;; Cada agente es una persona en una red social. En cada mes, quien aún no ha
;; adoptado la tecnología lo hace con probabilidad
;;
;;     P = 1 - (1 - p)·(1 - q·f)
;;
;; donde p es la influencia externa (publicidad / medios masivos), q la
;; influencia social (imitación) y f la fracción de sus vecinos que ya adoptó.
;; Es la versión en red del modelo de Bass (1969), siguiendo a Goldenberg,
;; Libai y Muller (2001) y a Rand y Rust (2011).
;; ============================================================================

extensions [ nw ]

globals [
  nuevos          ; adoptantes nuevos en el mes actual
  pico-nuevos     ; mayor número de adoptantes nuevos en un mes
  mes-pico        ; mes en que ocurrió ese pico
  mes-50          ; primer mes con adopción >= 50 % (-1 si no se alcanza)
  bass-F          ; fracción acumulada según el modelo agregado de Bass (referencia)
  grado-medio     ; propiedades estructurales de la red generada
  agrupamiento
  camino-medio
]

turtles-own [
  adoptante?       ; ya adoptó la tecnología
  susceptible?     ; hace parte del potencial de mercado (puede llegar a adoptar)
  decide-adoptar?  ; decisión tomada en el mes actual (actualización sincrónica)
  mes-adopcion     ; mes en que adoptó (-1 si no ha adoptado)
]

;; ---------------------------------------------------------------- configuración

to setup
  clear-all
  if semilla != 0 [ random-seed semilla ]
  crear-red
  ask turtles [
    set shape "circle"
    set adoptante? false
    set decide-adoptar? false
    set mes-adopcion -1
    set susceptible? random-float 100 < potencial-mercado
    set size min list 2.2 (0.5 + 0.08 * count link-neighbors)
  ]
  sembrar-adoptantes
  medir-red
  set mes-50 -1
  set bass-F (count turtles with [ adoptante? ]) / count turtles
  reset-ticks
  colorear
end

to crear-red
  let n poblacion
  (ifelse
    tipo-red = "aleatoria" [
      nw:generate-random turtles links n (grado-promedio / (n - 1))
      disponer-resorte
    ]
    tipo-red = "mundo pequeño" [
      nw:generate-watts-strogatz turtles links n (grado-promedio / 2) prob-reconexion
      if dibujar-red? [ layout-circle (sort turtles) (max-pxcor - 2) ]
    ]
    [ ; libre de escala
      nw:generate-preferential-attachment turtles links n (grado-promedio / 2)
      disponer-resorte
    ]
  )
  ask links [ set color gray - 3.5 ]
end

to disponer-resorte
  ask turtles [ setxy random-xcor random-ycor ]
  if dibujar-red? [
    let largo 0.8 * world-width / sqrt poblacion
    repeat 40 [ layout-spring turtles links 0.25 largo 1.2 ]
  ]
end

;; los primeros adoptantes (innovadores) se eligen al azar dentro del potencial de mercado
to sembrar-adoptantes
  let n round (adoptantes-iniciales / 100 * count turtles)
  ask n-of (min list n count turtles with [ susceptible? ]) turtles with [ susceptible? ] [
    set adoptante? true
    set mes-adopcion 0
  ]
end

to medir-red
  nw:set-context turtles links
  set grado-medio mean [ count link-neighbors ] of turtles
  set agrupamiento mean [ nw:clustering-coefficient ] of turtles
  set camino-medio nw:mean-path-length       ; false si la red no es conexa
end

;; ---------------------------------------------------------------- dinámica

to go
  if ticks >= meses [ stop ]
  decidir
  actualizar
  tick
  colorear
end

;; cada no adoptante decide con base en el estado de sus vecinos al inicio del mes
to decidir
  let p p-efectivo
  ask turtles with [ susceptible? and not adoptante? ] [
    let vecinos link-neighbors
    let f 0
    if any? vecinos [ set f (count vecinos with [ adoptante? ]) / (count vecinos) ]
    let prob 1 - (1 - p) * (1 - q-imitacion * f)
    set decide-adoptar? random-float 1 < prob
  ]
end

;; las decisiones se aplican todas a la vez (actualización sincrónica)
to actualizar
  let recientes turtles with [ decide-adoptar? ]
  set nuevos count recientes
  ask recientes [
    set adoptante? true
    set decide-adoptar? false
    set mes-adopcion ticks + 1
  ]
  if nuevos > pico-nuevos [
    set pico-nuevos nuevos
    set mes-pico ticks + 1
  ]
  if mes-50 = -1 and porcentaje-adopcion >= 50 [ set mes-50 ticks + 1 ]
  ; referencia: modelo agregado de Bass integrado con paso de un mes
  let m potencial-mercado / 100
  set bass-F bass-F + (p-efectivo + q-imitacion * bass-F) * (m - bass-F)
end

;; la publicidad solo actúa mientras la campaña está activa
to-report p-efectivo
  report ifelse-value (campaña? and ticks < duracion-campaña) [ p-publicidad ] [ 0 ]
end

;; ---------------------------------------------------------------- medidas

to-report porcentaje-adopcion
  report 100 * count turtles with [ adoptante? ] / count turtles
end

to-report porcentaje-bass
  report 100 * bass-F
end

;; ---------------------------------------------------------------- visual

to colorear
  ask turtles [
    set color (ifelse-value
      not susceptible?        [ gray - 3 ]
      not adoptante?          [ gray ]
      mes-adopcion = ticks    [ orange ]      ; adoptó en el mes que acaba de terminar
                              [ turquoise ])
  ]
end
@#$#@#$#@
GRAPHICS-WINDOW
215
10
650
446
-1
-1
7.0
1
10
1
1
1
0
0
0
1
-30
30
-30
30
0
0
1
mes
30.0

BUTTON
10
10
105
43
configurar
setup
NIL
1
T
OBSERVER
NIL
C
NIL
NIL
1

BUTTON
110
10
205
43
simular
go
T
1
T
OBSERVER
NIL
S
NIL
NIL
0

BUTTON
10
47
205
80
avanzar un mes
go
NIL
1
T
OBSERVER
NIL
M
NIL
NIL
0

TEXTBOX
12
88
205
106
Población y red social
12
0.0
1

SLIDER
10
106
205
139
poblacion
poblacion
100
2000
500.0
50
1
agentes
HORIZONTAL

CHOOSER
10
143
205
188
tipo-red
tipo-red
"aleatoria" "mundo pequeño" "libre de escala"
1

SLIDER
10
192
205
225
grado-promedio
grado-promedio
2
20
6.0
2
1
vecinos
HORIZONTAL

SLIDER
10
229
205
262
prob-reconexion
prob-reconexion
0
1
0.1
0.01
1
NIL
HORIZONTAL

SLIDER
10
266
205
299
potencial-mercado
potencial-mercado
50
100
100.0
1
1
%
HORIZONTAL

SLIDER
10
303
205
336
adoptantes-iniciales
adoptantes-iniciales
0
10
2.5
0.5
1
%
HORIZONTAL

TEXTBOX
12
344
205
362
Difusión
12
0.0
1

SLIDER
10
362
205
395
q-imitacion
q-imitacion
0
0.2
0.02
0.001
1
NIL
HORIZONTAL

SWITCH
10
399
205
432
campaña?
campaña?
0
1
-1000

SLIDER
10
436
205
469
p-publicidad
p-publicidad
0
0.03
0.0066
0.0001
1
NIL
HORIZONTAL

SLIDER
10
473
205
506
duracion-campaña
duracion-campaña
0
240
120.0
6
1
meses
HORIZONTAL

SLIDER
10
510
205
543
meses
meses
12
240
120.0
12
1
NIL
HORIZONTAL

INPUTBOX
10
547
105
607
semilla
0.0
1
0
Number

SWITCH
110
547
205
580
dibujar-red?
dibujar-red?
0
1
-1000

TEXTBOX
215
452
650
500
gris: aún no adopta · turquesa: adoptante · naranja: adoptó este mes · gris oscuro: fuera del potencial de mercado. El tamaño del nodo crece con su número de vecinos.
11
5.0
1

PLOT
660
10
1035
205
Adopción acumulada (%)
mes
% de la población
0.0
120.0
0.0
100.0
true
true
"" ""
PENS
"agentes en red" 1.0 0 -14835848 true "" "plot porcentaje-adopcion"
"Bass agregado" 1.0 0 -7500403 true "" "plot porcentaje-bass"

PLOT
660
210
1035
360
Nuevos adoptantes por mes
mes
agentes
0.0
120.0
0.0
10.0
true
false
"" ""
PENS
"nuevos" 1.0 1 -955883 true "" "plot nuevos"

MONITOR
660
368
750
413
% adopción
porcentaje-adopcion
1
1
11

MONITOR
755
368
845
413
mes del 50 %
mes-50
0
1
11

MONITOR
850
368
940
413
pico (mes)
mes-pico
0
1
11

MONITOR
945
368
1035
413
nuevos (mes)
nuevos
0
1
11

MONITOR
660
418
780
463
grado medio
grado-medio
2
1
11

MONITOR
785
418
905
463
agrupamiento
agrupamiento
3
1
11

MONITOR
910
418
1035
463
camino medio
camino-medio
2
1
11

TEXTBOX
660
470
1035
530
Valores por defecto de p y q: coeficientes mensuales calibrados con la serie de adopción de smartphones de Pew Research (2011–2026); ver analisis/parametros_calibrados.json.
11
5.0
1

@#$#@#$#@
## ¿QUÉ ES?

Un modelo basado en agentes de la **difusión de una innovación** (por ejemplo, los teléfonos inteligentes) en una población conectada por una red social. Cada agente decide en cada mes si adopta o no la tecnología, influido por dos fuerzas: la **publicidad** (influencia externa, que llega a todos por igual) y la **imitación** de sus vecinos en la red (influencia social).

La medida de desempeño principal es el **porcentaje de adopción al final del período**. El modelo permite comparar escenarios: difusión sin publicidad frente a una campaña activa, redes más o menos densas, y distintas estructuras de red.

## ¿CÓMO FUNCIONA?

1. Se genera una red social con `poblacion` agentes y grado promedio `grado-promedio`, de uno de tres tipos: **aleatoria** (Erdős–Rényi), **mundo pequeño** (Watts–Strogatz, con probabilidad de reconexión `prob-reconexion`) o **libre de escala** (Barabási–Albert).
2. Una fracción `potencial-mercado` de los agentes puede llegar a adoptar; el resto nunca lo hará (siguen en la red y diluyen la influencia de sus vecinos).
3. Un `adoptantes-iniciales` % de agentes (los innovadores) empieza con la tecnología.
4. En cada mes, cada agente que aún no ha adoptado observa la fracción `f` de sus vecinos que ya adoptó y adopta con probabilidad

   `P = 1 − (1 − p)·(1 − q·f)`

   donde `p = p-publicidad` mientras la campaña está activa (y 0 si no) y `q = q-imitacion`. Las decisiones de todos los agentes se aplican simultáneamente al terminar el mes.

Esta regla es la versión en red del modelo de Bass. La gráfica muestra también la curva del **modelo agregado de Bass** con los mismos parámetros, que supone que todos influyen sobre todos (campo medio); la diferencia entre ambas curvas es el efecto de la estructura de la red.

## ¿CÓMO SE USA?

Pulse **configurar** para generar la red y **simular** para correr la simulación hasta `meses`. **avanzar un mes** ejecuta un solo paso.

Colores: gris = aún no adopta; turquesa = adoptante; naranja = adoptó en el mes que acaba de terminar; gris oscuro = fuera del potencial de mercado. El tamaño del nodo crece con su número de vecinos.

`semilla` distinta de 0 fija la semilla aleatoria para reproducir una corrida. `dibujar-red?` desactivado omite la disposición visual de la red (útil con poblaciones grandes o en BehaviorSpace).

Los experimentos de la sección **Herramientas → BehaviorSpace** reproducen los escenarios del artículo: publicidad × densidad, topología × publicidad, duración de la campaña y calibración con datos reales.

## COSAS PARA OBSERVAR

* Sin campaña (`campaña?` apagado) la difusión depende por completo de los innovadores iniciales y de la densidad de la red: con `grado-promedio` bajo la innovación puede no despegar nunca.
* Con campaña, la curva toma la forma de S característica de Bass; la publicidad "siembra" adoptantes en todas las partes de la red y la imitación hace el resto.
* En redes libres de escala los nodos muy conectados (grandes) adoptan temprano y aceleran el despegue.
* La curva del modelo agregado suele ir **por encima** de la del modelo en red: en una red real, los adoptantes se agrupan y la influencia social se desperdicia entre quienes ya adoptaron.

## COSAS PARA PROBAR

* Fije `campaña?` apagado y busque el `grado-promedio` mínimo a partir del cual la adopción final supera el 50 %.
* Compare una campaña corta (`duracion-campaña` = 12) con una permanente: ¿cuánto se pierde en adopción final?
* Con `potencial-mercado` = 89 %, `adoptantes-iniciales` = 0 y `meses` = 228, compare la curva con la serie real de smartphones (2007–2026).

## CRÉDITOS Y REFERENCIAS

Proyecto de curso — Simulación Computacional, Ingeniería de Sistemas, Universidad de los Llanos (2026).
Jesus Gregorio Delgado, David Andres Monroy Aguiar, Duvan Felipe Baquero Cerquera.

* Bass, F. M. (1969). A new product growth model for consumer durables. *Management Science*, 15(5), 215–227.
* Goldenberg, J., Libai, B. y Muller, E. (2001). Talk of the network: a complex systems look at the underlying process of word-of-mouth. *Marketing Letters*, 12(3), 211–223.
* Rand, W. y Rust, R. T. (2011). Agent-based modeling in marketing: guidelines for rigor. *International Journal of Research in Marketing*, 28(3), 181–193.
* Rogers, E. M. (2003). *Diffusion of Innovations* (5.ª ed.). Free Press.
* Wilensky, U. (1999). NetLogo. Center for Connected Learning and Computer-Based Modeling, Northwestern University.
@#$#@#$#@
default
true
0
Polygon -7500403 true true 150 5 40 250 150 205 260 250

circle
false
0
Circle -7500403 true true 0 0 300

circle 2
false
0
Circle -7500403 true true 0 0 300
Circle -16777216 true false 30 30 240
@#$#@#$#@
NetLogo 6.4.0
@#$#@#$#@
setup
repeat 60 [ go ]
@#$#@#$#@
@#$#@#$#@
<experiments>
  <experiment name="publicidad_x_densidad" repetitions="30" sequentialRunOrder="false" runMetricsEveryStep="true">
    <setup>setup</setup>
    <go>go</go>
    <timeLimit steps="120"/>
    <metric>porcentaje-adopcion</metric>
    <metric>nuevos</metric>
    <metric>mes-50</metric>
    <metric>pico-nuevos</metric>
    <metric>mes-pico</metric>
    <metric>grado-medio</metric>
    <metric>agrupamiento</metric>
    <metric>camino-medio</metric>
    <enumeratedValueSet variable="poblacion"><value value="1000"/></enumeratedValueSet>
    <enumeratedValueSet variable="tipo-red"><value value="&quot;mundo pequeño&quot;"/></enumeratedValueSet>
    <enumeratedValueSet variable="grado-promedio"><value value="2"/><value value="4"/><value value="6"/><value value="8"/><value value="12"/><value value="16"/></enumeratedValueSet>
    <enumeratedValueSet variable="prob-reconexion"><value value="0.1"/></enumeratedValueSet>
    <enumeratedValueSet variable="potencial-mercado"><value value="100"/></enumeratedValueSet>
    <enumeratedValueSet variable="adoptantes-iniciales"><value value="2.5"/></enumeratedValueSet>
    <enumeratedValueSet variable="q-imitacion"><value value="0.02"/><value value="0.032"/></enumeratedValueSet>
    <enumeratedValueSet variable="campaña?"><value value="false"/><value value="true"/></enumeratedValueSet>
    <enumeratedValueSet variable="p-publicidad"><value value="0.0066"/></enumeratedValueSet>
    <enumeratedValueSet variable="duracion-campaña"><value value="120"/></enumeratedValueSet>
    <enumeratedValueSet variable="meses"><value value="120"/></enumeratedValueSet>
    <enumeratedValueSet variable="semilla"><value value="0"/></enumeratedValueSet>
    <enumeratedValueSet variable="dibujar-red?"><value value="false"/></enumeratedValueSet>
  </experiment>
  <experiment name="topologia_x_publicidad" repetitions="30" sequentialRunOrder="false" runMetricsEveryStep="true">
    <setup>setup</setup>
    <go>go</go>
    <timeLimit steps="120"/>
    <metric>porcentaje-adopcion</metric>
    <metric>nuevos</metric>
    <metric>mes-50</metric>
    <metric>pico-nuevos</metric>
    <metric>mes-pico</metric>
    <metric>grado-medio</metric>
    <metric>agrupamiento</metric>
    <metric>camino-medio</metric>
    <enumeratedValueSet variable="poblacion"><value value="1000"/></enumeratedValueSet>
    <enumeratedValueSet variable="tipo-red"><value value="&quot;aleatoria&quot;"/><value value="&quot;mundo pequeño&quot;"/><value value="&quot;libre de escala&quot;"/></enumeratedValueSet>
    <enumeratedValueSet variable="grado-promedio"><value value="6"/></enumeratedValueSet>
    <enumeratedValueSet variable="prob-reconexion"><value value="0.1"/></enumeratedValueSet>
    <enumeratedValueSet variable="potencial-mercado"><value value="100"/></enumeratedValueSet>
    <enumeratedValueSet variable="adoptantes-iniciales"><value value="2.5"/></enumeratedValueSet>
    <enumeratedValueSet variable="q-imitacion"><value value="0.02"/><value value="0.032"/></enumeratedValueSet>
    <enumeratedValueSet variable="campaña?"><value value="false"/><value value="true"/></enumeratedValueSet>
    <enumeratedValueSet variable="p-publicidad"><value value="0.0066"/></enumeratedValueSet>
    <enumeratedValueSet variable="duracion-campaña"><value value="120"/></enumeratedValueSet>
    <enumeratedValueSet variable="meses"><value value="120"/></enumeratedValueSet>
    <enumeratedValueSet variable="semilla"><value value="0"/></enumeratedValueSet>
    <enumeratedValueSet variable="dibujar-red?"><value value="false"/></enumeratedValueSet>
  </experiment>
  <experiment name="duracion_campana" repetitions="30" sequentialRunOrder="false" runMetricsEveryStep="true">
    <setup>setup</setup>
    <go>go</go>
    <timeLimit steps="120"/>
    <metric>porcentaje-adopcion</metric>
    <metric>nuevos</metric>
    <metric>mes-50</metric>
    <metric>pico-nuevos</metric>
    <metric>mes-pico</metric>
    <enumeratedValueSet variable="poblacion"><value value="1000"/></enumeratedValueSet>
    <enumeratedValueSet variable="tipo-red"><value value="&quot;mundo pequeño&quot;"/></enumeratedValueSet>
    <enumeratedValueSet variable="grado-promedio"><value value="6"/></enumeratedValueSet>
    <enumeratedValueSet variable="prob-reconexion"><value value="0.1"/></enumeratedValueSet>
    <enumeratedValueSet variable="potencial-mercado"><value value="100"/></enumeratedValueSet>
    <enumeratedValueSet variable="adoptantes-iniciales"><value value="2.5"/></enumeratedValueSet>
    <enumeratedValueSet variable="q-imitacion"><value value="0.02"/><value value="0.032"/></enumeratedValueSet>
    <enumeratedValueSet variable="campaña?"><value value="true"/></enumeratedValueSet>
    <enumeratedValueSet variable="p-publicidad"><value value="0.0066"/></enumeratedValueSet>
    <enumeratedValueSet variable="duracion-campaña"><value value="0"/><value value="6"/><value value="12"/><value value="24"/><value value="60"/><value value="120"/></enumeratedValueSet>
    <enumeratedValueSet variable="meses"><value value="120"/></enumeratedValueSet>
    <enumeratedValueSet variable="semilla"><value value="0"/></enumeratedValueSet>
    <enumeratedValueSet variable="dibujar-red?"><value value="false"/></enumeratedValueSet>
  </experiment>
  <experiment name="calibracion_pew" repetitions="30" sequentialRunOrder="false" runMetricsEveryStep="true">
    <setup>setup</setup>
    <go>go</go>
    <timeLimit steps="228"/>
    <metric>porcentaje-adopcion</metric>
    <metric>nuevos</metric>
    <metric>porcentaje-bass</metric>
    <metric>grado-medio</metric>
    <metric>agrupamiento</metric>
    <metric>camino-medio</metric>
    <enumeratedValueSet variable="poblacion"><value value="1000"/></enumeratedValueSet>
    <enumeratedValueSet variable="tipo-red"><value value="&quot;aleatoria&quot;"/><value value="&quot;mundo pequeño&quot;"/><value value="&quot;libre de escala&quot;"/></enumeratedValueSet>
    <enumeratedValueSet variable="grado-promedio"><value value="4"/><value value="8"/><value value="16"/></enumeratedValueSet>
    <enumeratedValueSet variable="prob-reconexion"><value value="0.1"/></enumeratedValueSet>
    <enumeratedValueSet variable="potencial-mercado"><value value="89"/></enumeratedValueSet>
    <enumeratedValueSet variable="adoptantes-iniciales"><value value="0"/></enumeratedValueSet>
    <enumeratedValueSet variable="q-imitacion"><value value="0.0202"/></enumeratedValueSet>
    <enumeratedValueSet variable="campaña?"><value value="true"/></enumeratedValueSet>
    <enumeratedValueSet variable="p-publicidad"><value value="0.0066"/></enumeratedValueSet>
    <enumeratedValueSet variable="duracion-campaña"><value value="240"/></enumeratedValueSet>
    <enumeratedValueSet variable="meses"><value value="228"/></enumeratedValueSet>
    <enumeratedValueSet variable="semilla"><value value="0"/></enumeratedValueSet>
    <enumeratedValueSet variable="dibujar-red?"><value value="false"/></enumeratedValueSet>
  </experiment>
</experiments>
@#$#@#$#@
@#$#@#$#@
default
0.0
-0.2 0 0.0 1.0
0.0 1 1.0 0.0
0.2 0 0.0 1.0
link direction
true
0
Line -7500403 true 150 150 90 180
Line -7500403 true 150 150 210 180
@#$#@#$#@
0
@#$#@#$#@
