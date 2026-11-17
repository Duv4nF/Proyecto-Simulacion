;; ============================================================================
;; Difusión de innovaciones en una red social: PS5 (tecnología) y GTA 6 (innovación)
;; Modelo basado en agentes — Simulación Computacional, Universidad de los Llanos
;;
;; Cada agente es una persona en una red social. En cada mes, quien aún no ha
;; adoptado lo hace con probabilidad
;;
;;     P = 1 - (1 - p)·(1 - q·f)
;;
;; donde p es la influencia externa (publicidad / campaña de lanzamiento), q la
;; influencia social (imitación) y f la fracción de sus vecinos que ya adoptó.
;; Es la versión en red del modelo de Bass (1969), siguiendo a Goldenberg,
;; Libai y Muller (2001) y a Rand y Rust (2011).
;;
;; El selector `caso` carga los parámetros de los dos casos del proyecto:
;;   - PS5 (tecnología): calibrado con la serie oficial de ventas de Sony (2020-2026);
;;   - GTA 6 (innovación): por analogía con el lanzamiento de GTA V (2013-2014);
;;   - libre: usa los valores de los deslizadores.
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
  aplicar-caso
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

;; Parámetros de cada caso de estudio. No tocan la red, la campaña ni su duración,
;; que son los factores de los experimentos; "libre" respeta los deslizadores.
to aplicar-caso
  if caso = "PS5 (tecnología)" [
    ;; Bass calibrado con la serie de Sony (analisis/parametros_calibrados.json)
    set p-publicidad 0.0081
    set q-imitacion 0.0375
    set potencial-mercado 100
    set adoptantes-iniciales 2.5    ; innovadores de Rogers
    set meses 72                    ; seis años desde el lanzamiento
  ]
  if caso = "GTA 6 (innovación)" [
    ;; por analogía con GTA V (analisis/parametros_gta6.json)
    set p-publicidad 0.69           ; campaña de lanzamiento
    set q-imitacion 0.0375          ; imitación medida con la PS5
    set potencial-mercado 21        ; meseta del primer año de GTA V sobre su base instalada
    set adoptantes-iniciales 7      ; compradores del primer día
    set meses 24                    ; dos años desde el lanzamiento
  ]
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
                              [ blue ])
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
16.0
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
0
100
21.0
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
20
7.0
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
0.5
0.0375
0.0001
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
1
0.69
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
240.0
1
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
6
240
24.0
1
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
gris: aún no adopta · azul: adoptante · naranja: adoptó este mes · gris oscuro: fuera del potencial de mercado. El tamaño del nodo crece con su número de vecinos.
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
24.0
0.0
100.0
true
true
"" ""
PENS
"agentes en red" 1.0 0 -13345367 true "" "plot porcentaje-adopcion"
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
24.0
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

CHOOSER
660
470
1035
515
caso
caso
"libre" "PS5 (tecnología)" "GTA 6 (innovación)"
2

TEXTBOX
660
520
1035
580
PS5: Bass calibrado con la serie oficial de Sony (2020–2026). GTA 6: parámetros por analogía con el lanzamiento de GTA V. libre: usa los deslizadores. El caso se aplica al pulsar configurar.
11
5.0
1

@#$#@#$#@
## ¿QUÉ ES?

Un modelo basado en agentes de la **difusión de innovaciones** en una población conectada por una red social, aplicado a dos casos: la **PS5** como tecnología nueva (calibrada con datos reales) y **GTA 6** como innovación que se difunde entre los dueños de PS5 (escenario hipotético por analogía con GTA V). Cada agente decide en cada mes si adopta, influido por dos fuerzas: la **publicidad** (influencia externa, que llega a todos por igual) y la **imitación** de sus vecinos en la red (influencia social).

La medida de desempeño principal es el **porcentaje de adopción al final del período**. El modelo permite comparar escenarios: difusión sin publicidad frente a una campaña activa, redes más o menos densas, distintas estructuras de red y campañas de distinta duración.

## ¿CÓMO FUNCIONA?

1. Se genera una red social con `poblacion` agentes y grado promedio `grado-promedio`, de uno de tres tipos: **aleatoria** (Erdős–Rényi), **mundo pequeño** (Watts–Strogatz, con probabilidad de reconexión `prob-reconexion`) o **libre de escala** (Barabási–Albert).
2. Una fracción `potencial-mercado` de los agentes puede llegar a adoptar; el resto nunca lo hará (siguen en la red y diluyen la influencia de sus vecinos).
3. Un `adoptantes-iniciales` % de agentes empieza con el producto (innovadores o compradores del primer día).
4. En cada mes, cada agente que aún no ha adoptado observa la fracción `f` de sus vecinos que ya adoptó y adopta con probabilidad

   `P = 1 − (1 − p)·(1 − q·f)`

   donde `p = p-publicidad` mientras la campaña está activa (y 0 si no) y `q = q-imitacion`. Las decisiones de todos los agentes se aplican simultáneamente al terminar el mes.

Esta regla es la versión en red del modelo de Bass. La gráfica muestra también la curva del **modelo agregado de Bass** con los mismos parámetros, que supone que todos influyen sobre todos; la diferencia entre ambas curvas es el efecto de la estructura de la red.

## CASOS

* **PS5 (tecnología)**: `p` = 0,0081 y `q` = 0,0375 mensuales, ajustados con la serie oficial de unidades de Sony (2020–2026) y expresados sobre la base instalada de PS4 (117 millones); potencial del 100 %, 2,5 % de innovadores y 72 meses.
* **GTA 6 (innovación)**: `p` = 0,69 mensual (campaña de lanzamiento), `q` = 0,0375 (la imitación medida con la PS5), potencial del 21 % de los dueños de PS5, 7 % de compradores el primer día y 24 meses, por analogía con el primer año de GTA V (cifras de Take-Two).
* **libre**: usa los deslizadores tal como estén.

El caso se aplica al pulsar **configurar**; no cambia la red, la campaña ni su duración.

## ¿CÓMO SE USA?

Elija el `caso`, pulse **configurar** para generar la red y **simular** para correr hasta `meses`. **avanzar un mes** ejecuta un solo paso.

Colores: gris = aún no adopta; azul = adoptante; naranja = adoptó en el mes que acaba de terminar; gris oscuro = fuera del potencial de mercado. El tamaño del nodo crece con su número de vecinos.

`semilla` distinta de 0 fija la semilla aleatoria para reproducir una corrida. `dibujar-red?` desactivado omite la disposición visual de la red (útil con poblaciones grandes o en BehaviorSpace).

Los experimentos de **Herramientas → BehaviorSpace** reproducen los del artículo: calibración con la serie de PS5, publicidad × densidad, topología × publicidad y duración de la campaña, los tres últimos para ambos casos.

## COSAS PARA OBSERVAR

* PS5: la curva tiene forma de S; la imitación pesa más que la publicidad (`q` > `p`).
* GTA 6: casi todas las compras ocurren en el primer mes con campaña y luego caen (`p` > `q`), como en el lanzamiento de un éxito de taquilla.
* Sin campaña, la difusión depende de los adoptantes iniciales y de la densidad de la red.
* La curva del modelo agregado suele ir **por encima** de la del modelo en red: en una red, los adoptantes se agrupan y la influencia social se desperdicia entre quienes ya adoptaron.

## COSAS PARA PROBAR

* Caso PS5 con `campaña?` apagado: ¿cuánto cambia la adopción final al pasar `grado-promedio` de 2 a 16?
* Caso GTA 6 con `duracion-campaña` = 1: ¿qué parte del efecto de una campaña permanente se logra con un solo mes?
* Caso libre con `potencial-mercado` = 100, `adoptantes-iniciales` = 0, `p-publicidad` = 0,0081, `q-imitacion` = 0,0375 y `meses` = 74: compare la curva con la serie real de la PS5.

## CRÉDITOS Y REFERENCIAS

Proyecto de curso — Simulación Computacional, Ingeniería de Sistemas, Universidad de los Llanos (2026).
Jesus Gregorio Delgado, David Andres Monroy Aguiar, Duvan Felipe Baquero Cerquera.

* Bass, F. M. (1969). A new product growth model for consumer durables. *Management Science*, 15(5), 215–227.
* Goldenberg, J., Libai, B. y Muller, E. (2001). Talk of the network: a complex systems look at the underlying process of word-of-mouth. *Marketing Letters*, 12(3), 211–223.
* Rand, W. y Rust, R. T. (2011). Agent-based modeling in marketing: guidelines for rigor. *International Journal of Research in Marketing*, 28(3), 181–193.
* Rogers, E. M. (2003). *Diffusion of Innovations* (5.ª ed.). Free Press.
* Wilensky, U. (1999). NetLogo. Center for Connected Learning and Computer-Based Modeling, Northwestern University.
* Sony Interactive Entertainment. Business Data & Sales. https://www.sonyinteractive.com/en/our-company/business-data-sales/
* Take-Two Interactive. Comunicados de resultados de los años fiscales 2014 y 2015 (ventas de Grand Theft Auto V).
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
    <timeLimit steps="72"/>
    <metric>porcentaje-adopcion</metric>
    <metric>nuevos</metric>
    <metric>mes-50</metric>
    <metric>pico-nuevos</metric>
    <metric>mes-pico</metric>
    <metric>grado-medio</metric>
    <metric>agrupamiento</metric>
    <metric>camino-medio</metric>
    <enumeratedValueSet variable="caso"><value value="&quot;PS5 (tecnología)&quot;"/><value value="&quot;GTA 6 (innovación)&quot;"/></enumeratedValueSet>
    <enumeratedValueSet variable="tipo-red"><value value="&quot;mundo pequeño&quot;"/></enumeratedValueSet>
    <enumeratedValueSet variable="grado-promedio"><value value="2"/><value value="4"/><value value="6"/><value value="8"/><value value="12"/><value value="16"/></enumeratedValueSet>
    <enumeratedValueSet variable="campaña?"><value value="false"/><value value="true"/></enumeratedValueSet>
    <enumeratedValueSet variable="duracion-campaña"><value value="240"/></enumeratedValueSet>
    <enumeratedValueSet variable="poblacion"><value value="1000"/></enumeratedValueSet>
    <enumeratedValueSet variable="prob-reconexion"><value value="0.1"/></enumeratedValueSet>
    <enumeratedValueSet variable="semilla"><value value="0"/></enumeratedValueSet>
    <enumeratedValueSet variable="dibujar-red?"><value value="false"/></enumeratedValueSet>
  </experiment>
  <experiment name="topologia_x_publicidad" repetitions="30" sequentialRunOrder="false" runMetricsEveryStep="true">
    <setup>setup</setup>
    <go>go</go>
    <timeLimit steps="72"/>
    <metric>porcentaje-adopcion</metric>
    <metric>nuevos</metric>
    <metric>mes-50</metric>
    <metric>pico-nuevos</metric>
    <metric>mes-pico</metric>
    <metric>grado-medio</metric>
    <metric>agrupamiento</metric>
    <metric>camino-medio</metric>
    <enumeratedValueSet variable="caso"><value value="&quot;PS5 (tecnología)&quot;"/><value value="&quot;GTA 6 (innovación)&quot;"/></enumeratedValueSet>
    <enumeratedValueSet variable="tipo-red"><value value="&quot;aleatoria&quot;"/><value value="&quot;mundo pequeño&quot;"/><value value="&quot;libre de escala&quot;"/></enumeratedValueSet>
    <enumeratedValueSet variable="grado-promedio"><value value="16"/></enumeratedValueSet>
    <enumeratedValueSet variable="campaña?"><value value="false"/><value value="true"/></enumeratedValueSet>
    <enumeratedValueSet variable="duracion-campaña"><value value="240"/></enumeratedValueSet>
    <enumeratedValueSet variable="poblacion"><value value="1000"/></enumeratedValueSet>
    <enumeratedValueSet variable="prob-reconexion"><value value="0.1"/></enumeratedValueSet>
    <enumeratedValueSet variable="semilla"><value value="0"/></enumeratedValueSet>
    <enumeratedValueSet variable="dibujar-red?"><value value="false"/></enumeratedValueSet>
  </experiment>
  <experiment name="duracion_campana" repetitions="30" sequentialRunOrder="false" runMetricsEveryStep="true">
    <setup>setup</setup>
    <go>go</go>
    <timeLimit steps="72"/>
    <metric>porcentaje-adopcion</metric>
    <metric>nuevos</metric>
    <metric>mes-50</metric>
    <metric>pico-nuevos</metric>
    <metric>mes-pico</metric>
    <metric>grado-medio</metric>
    <metric>agrupamiento</metric>
    <metric>camino-medio</metric>
    <enumeratedValueSet variable="caso"><value value="&quot;PS5 (tecnología)&quot;"/><value value="&quot;GTA 6 (innovación)&quot;"/></enumeratedValueSet>
    <enumeratedValueSet variable="tipo-red"><value value="&quot;mundo pequeño&quot;"/></enumeratedValueSet>
    <enumeratedValueSet variable="grado-promedio"><value value="16"/></enumeratedValueSet>
    <enumeratedValueSet variable="campaña?"><value value="true"/></enumeratedValueSet>
    <enumeratedValueSet variable="duracion-campaña"><value value="0"/><value value="1"/><value value="3"/><value value="6"/><value value="12"/><value value="24"/><value value="240"/></enumeratedValueSet>
    <enumeratedValueSet variable="poblacion"><value value="1000"/></enumeratedValueSet>
    <enumeratedValueSet variable="prob-reconexion"><value value="0.1"/></enumeratedValueSet>
    <enumeratedValueSet variable="semilla"><value value="0"/></enumeratedValueSet>
    <enumeratedValueSet variable="dibujar-red?"><value value="false"/></enumeratedValueSet>
  </experiment>
  <experiment name="calibracion_ps5" repetitions="30" sequentialRunOrder="false" runMetricsEveryStep="true">
    <setup>setup</setup>
    <go>go</go>
    <timeLimit steps="74"/>
    <metric>porcentaje-adopcion</metric>
    <metric>nuevos</metric>
    <metric>porcentaje-bass</metric>
    <metric>grado-medio</metric>
    <metric>agrupamiento</metric>
    <metric>camino-medio</metric>
    <enumeratedValueSet variable="caso"><value value="&quot;libre&quot;"/></enumeratedValueSet>
    <enumeratedValueSet variable="poblacion"><value value="1000"/></enumeratedValueSet>
    <enumeratedValueSet variable="tipo-red"><value value="&quot;aleatoria&quot;"/><value value="&quot;mundo pequeño&quot;"/><value value="&quot;libre de escala&quot;"/></enumeratedValueSet>
    <enumeratedValueSet variable="grado-promedio"><value value="4"/><value value="8"/><value value="16"/></enumeratedValueSet>
    <enumeratedValueSet variable="prob-reconexion"><value value="0.1"/></enumeratedValueSet>
    <enumeratedValueSet variable="potencial-mercado"><value value="100"/></enumeratedValueSet>
    <enumeratedValueSet variable="adoptantes-iniciales"><value value="0"/></enumeratedValueSet>
    <enumeratedValueSet variable="q-imitacion"><value value="0.0375"/></enumeratedValueSet>
    <enumeratedValueSet variable="campaña?"><value value="true"/></enumeratedValueSet>
    <enumeratedValueSet variable="p-publicidad"><value value="0.0081"/></enumeratedValueSet>
    <enumeratedValueSet variable="duracion-campaña"><value value="240"/></enumeratedValueSet>
    <enumeratedValueSet variable="meses"><value value="74"/></enumeratedValueSet>
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
