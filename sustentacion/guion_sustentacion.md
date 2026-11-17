# Guion de sustentación (15 minutos)

Proyecto 14 · Difusión de innovación o tecnología · Simulación Computacional · Universidad de los Llanos
Integrantes: Jesus Gregorio Delgado, David Andres Monroy Aguiar, Duvan Felipe Baquero Cerquera

> Este archivo se genera con `python sustentacion/rellenar.py` a partir de `sustentacion/plantillas/guion_sustentacion.md`; las cifras salen del análisis. Para cambiar el texto, editen la plantilla.

La rúbrica evalúa presentación personal; claridad, entonación y dominio del tema; participación equitativa; desarrollo y resultados; diapositivas; dominio del tiempo, e implementación (código e interfaz en vivo). El plan suma unos 14 minutos, para dejar un minuto de margen para los cambios de orador y la demo. El mismo texto está en `presentacion/presentacion_notas.pdf`, con una página por diapositiva.

| Bloque | Diapositivas | Quién | Tiempo |
|---|---|---|---|
| Apertura, planteamiento y modelo | 1–6 | Jesus | 0:00 – 4:45 |
| Sistema, implementación, datos y diseño experimental | 7–11 | David | 4:45 – 8:35 |
| Medidas y resultados | 12–16 | Duvan | 8:35 – 12:15 |
| Demostración en NetLogo | 17 | David | 12:15 – 13:25 |
| Conclusiones y referencias | 18–19 | Duvan | 13:25 – 14:05 |

## Bloque 1 · Jesus (0:00 – 4:45)

**1 · Portada (0:40).** Buenos días. Somos Jesus, David y Duvan. Nuestro proyecto simula cómo se difunde un producto nuevo cuando cada persona decide influida por la publicidad y por sus contactos. Lo aplicamos a dos casos de actualidad: la PS5, una tecnología, y GTA 6, un videojuego que sale este jueves. Lo construimos en NetLogo, lo calibramos con datos reales y lo usamos para comparar escenarios que no se pueden observar.

**2 · Motivación (0:45).** La PS5 ya pasa de 97,9 millones de unidades, y sobre esa base sale GTA 6 el 19 de noviembre, después de una campaña que rompió récords: 90 millones de vistas del primer tráiler en un día. Bass explicó la difusión con dos fuerzas: la publicidad, que llega a todos, y la imitación, que depende de cuántos ya adoptaron. Cuando manda la imitación sale la curva en S, como en la PS5; cuando manda la publicidad, las ventas se concentran en el lanzamiento.

**3 · Problema (0:50).** El modelo de Bass describe bien las curvas agregadas, pero supone que todos influyen sobre todos, como en la red de la izquierda. En la vida real la influencia viaja por una red concreta, como la de la derecha. Eso deja cuatro preguntas sin responder: qué pasa sin publicidad, si importa la estructura de la red, cuánto se pierde con una campaña corta y si una consola y un videojuego responden igual.

**4 · Justificación (0:50).** La simulación basada en agentes responde esas preguntas porque representa a cada persona y sus contactos, y permite correr escenarios que no se pueden observar, como lanzar sin publicidad. Para que no fuera un ejercicio solo cualitativo, la PS5 se calibró con las ventas oficiales de Sony y se evaluó con datos que no usamos para ajustar. GTA 6 todavía no tiene ventas, así que sus parámetros salen por analogía con GTA V, que es la práctica estándar antes de un lanzamiento.

**5 · Objetivos (0:40).** El objetivo general es medir el efecto de la publicidad y de la red sobre la adopción final, en la PS5 y en GTA 6. Los específicos: implementarlo en NetLogo con tres tipos de red, calibrarlo con partición entrenamiento-validación-prueba, evaluar los escenarios con réplicas y verificarlo con una reimplementación independiente en Python.

**6 · Modelo (1:00).** Cada agente es un nodo. Cada mes, quien no ha adoptado lo hace con esta probabilidad: la publicidad lo convence con probabilidad *p* mientras la campaña esté activa, y sus vecinos con *q* por la fracción de vecinos que ya adoptaron. Las decisiones se aplican todas a la vez al cerrar el mes y la adopción es irreversible. Si la red fuera completa, el modelo recuperaría la curva de Bass; la diferencia entre ambas es el efecto de la red. Usamos tres redes: aleatoria, mundo pequeño, con grupos cerrados, y libre de escala, con pocos nodos muy conectados. *Le paso la palabra a David.*

## Bloque 2 · David (4:45 – 8:35)

**7 · Esquema del sistema (0:40).** Arriba el flujo: las ventas reales dan los parámetros, la PS5 por calibración de Bass y GTA 6 por analogía con GTA V; NetLogo simula; BehaviorSpace corre los cuatro experimentos; Python calcula las medidas. Abajo, lo que pasa dentro del modelo cada mes: la campaña y la red alimentan la regla, que decide si cada persona adopta.

**8 · Implementación (0:50).** Esto es NetLogo con la extensión nw. A la izquierda, la interfaz con el caso PS5 en una red libre de escala: en azul los que ya adoptaron, en naranja los de este mes, y los nodos grandes son los más conectados. A la derecha, el procedimiento `decidir`: cada no adoptante cuenta qué fracción de sus vecinos ya adoptó y sortea su decisión con la fórmula. Un procedimiento aparte, `actualizar`, aplica todas las decisiones a la vez para que el orden de los agentes no afecte el resultado. El selector de caso carga los parámetros de la PS5 o de GTA 6 con un clic.

**9 · Datos de la PS5 (0:40).** La serie real son las unidades de PS5 que Sony publica cada trimestre: 24 trimestres, de 4,5 a 97,9 millones. La expresamos como porcentaje de la base de la PS4, 117 millones, que fijamos antes de mirar los datos de prueba. El segundo conjunto lo genera la simulación: 1770 corridas de mil agentes.

**10 · Analogía con GTA V (0:50).** GTA 6 no tiene ventas todavía, así que usamos el método de analogía: tomamos el lanzamiento más parecido, GTA V. Vendió 29 millones en seis semanas y se estabilizó en 34 millones, sobre 160 millones de consolas. Con la imitación fijada en la de la PS5, el ajuste atribuye el salto del lanzamiento a la publicidad: 0,69 al mes, unas 18 veces la imitación, lo contrario de la PS5. Así modelamos GTA 6 entre los dueños de PS5, con un potencial del 21 % y dos años de horizonte.

**11 · Diseño experimental (0:50).** La serie de la PS5 se parte en el tiempo: con entrenamiento, 13 trimestres, estimamos *p* y *q*; como el potencial no se puede estimar en plena fase de crecimiento, lo elegimos en validación, 4 trimestres, igual que la red; la prueba, 7 trimestres, solo evalúa. Corremos cuatro experimentos, los tres de escenarios para los dos casos: publicidad por densidad, publicidad por topología y duración de la campaña, más la calibración. Cada combinación se repite 30 veces. *Duvan presenta las medidas y los resultados.*

## Bloque 3 · Duvan (8:35 – 12:15)

**12 · Medidas de desempeño (0:30).** La medida principal, la que pide el enunciado, es el porcentaje de adopción al final del período: seis años para la PS5 y dos para GTA 6. La complementamos con el mes del 50 % y el mes del pico de compras. Frente a la serie real usamos RMSE y MAPE por partición. Todo con 30 réplicas e intervalos del 95 %.

**13 · Calibración (0:50).** El ajuste da *p* = 0,097 y *q* = 0,449 anuales: en la PS5 la imitación pesa 4,6 veces más que la publicidad. En validación se eligió la red de mundo pequeño con *k* = 16. En prueba, que nunca usamos para ajustar, el error es de 4,91 puntos, mayor que el de Bass (3,22), porque la red frena la difusión. Ambos quedan un poco por debajo del dato de Sony de noviembre de 2026, más de 100 millones: la PS5 probablemente superará la base de la PS4.

**14 · Publicidad (0:50).** El resultado central. En la PS5, sin publicidad la adopción queda entre el 8,6 y el 21,1 % en seis años; con campaña, entre el 73,3 y el 82,6 %, con la curva en S. En GTA 6 la campaña lo decide todo: con ella se alcanza el potencial casi en el primer mes; sin ella la adopción apenas pasa de los compradores del primer día (7,8–7,9 %). Sin publicidad, la PS5 simplemente no despega.

**15 · Densidad y topología (0:50).** En la PS5 sin publicidad, pasar de 2 a 16 contactos multiplica la adopción por 2,5; con campaña solo por 1,1, porque la publicidad siembra adoptantes en toda la red. En la topología pasa lo mismo: sin campaña, la red de mundo pequeño es la más lenta de las tres, porque sus grupos cerrados atrapan la influencia, y la libre de escala la más variable, porque depende de si un nodo muy conectado adopta temprano. En GTA 6 la red casi no cambia nada.

**16 · Duración (0:40).** Si la campaña se corta, ¿cuánto se pierde? En GTA 6, un solo mes ya logra el 71 % del efecto de una campaña permanente: el lanzamiento concentra casi todo. En la PS5 el rendimiento es gradual: un año logra el 55 % y dos años el 75 %, porque la imitación necesita tiempo para sostener la difusión. *David hace la demostración.*

## Bloque 4 · David · Demostración (12:15 – 13:25)

Abrir `modelo/difusion_innovacion.nlogo` antes de empezar la sustentación. Dejar `poblacion` en 500, `tipo-red` en mundo pequeño, `grado-promedio` en 16 y `dibujar-red?` encendido.

1. **caso = GTA 6 (innovación) → configurar → simular.** Mostrar que casi todas las compras ocurren en el primer mes (gráfica de nuevos adoptantes) y que la curva llega al potencial del 21 %.
2. **campaña? apagada → configurar → simular.** La adopción apenas pasa del 7 % de compradores del primer día.
3. **caso = PS5 (tecnología), campaña? encendida → configurar → simular.** Curva en S frente a la de Bass; el monitor *mes del 50 %* se activa.

Solo si sobra tiempo: 4) PS5 con campaña apagada y `grado-promedio` en 2 (la difusión se frena); 5) Herramientas → BehaviorSpace para mostrar los cuatro experimentos. Si preguntan por el código, mostrar `aplicar-caso`, `decidir` y `actualizar` en la pestaña Código.

## Bloque 5 · Duvan (13:25 – 14:05)

**18 · Conclusiones (0:30).** Cuatro conclusiones. En la PS5, la publicidad es la condición del despegue. En GTA 6, el primer mes de campaña decide el resultado. La red pesa sobre todo cuando no hay publicidad. Y el modelo quedó validado con datos que no usamos para ajustar y verificado con una reimplementación independiente.

**19 · Referencias (0:10).** Las referencias están en pantalla. Gracias; quedamos atentos a sus preguntas.

## Preguntas probables

Las respuestas completas están en la guía de estudio (`sustentacion/guia_estudio.html`, también en Google Drive).
