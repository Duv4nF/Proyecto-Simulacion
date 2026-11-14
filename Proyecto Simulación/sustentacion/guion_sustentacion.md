# Guion de sustentación (15 minutos)

Proyecto 14 · Difusión de innovación o tecnología · Simulación Computacional · Universidad de los Llanos
Integrantes: Jesus Gregorio Delgado, David Andres Monroy Aguiar, Duvan Felipe Baquero Cerquera

La rúbrica pide participación equitativa, dominio del tiempo y demostración de la implementación. El reparto propuesto es de ~5 minutos por persona; el mismo texto está en las notas del orador de cada diapositiva (`presentacion/presentacion.pptx`). Cámbienlo si prefieren otro orden: lo importante es que quien hace la demo sea quien más haya practicado con el modelo.

| Bloque | Diapositivas | Quién | Tiempo |
|---|---|---|---|
| Apertura y planteamiento | 1–5 | Jesus | 0:00 – 4:10 |
| Metodología, datos y diseño experimental | 6–11 | David | 4:10 – 8:30 |
| Resultados | 12–15 | Duvan | 8:30 – 11:40 |
| Demostración en NetLogo | 16 | David | 11:40 – 13:30 |
| Conclusiones y referencias | 17–18 | Duvan | 13:30 – 15:00 |

## Bloque 1 · Jesus (0:00 – 4:10)

**Diapositiva 1 · Portada (0:40).** Buenas tardes. Somos Jesus, David y Duvan. Nuestro proyecto simula cómo una tecnología nueva, como el smartphone, se adopta en una población donde cada persona decide bajo la influencia de la publicidad y de sus contactos. Lo construimos en NetLogo, lo calibramos con datos reales y lo usamos para comparar escenarios que no se pueden observar en la realidad.

**Diapositiva 2 · Motivación (1:00).** El smartphone es el caso reciente más claro de difusión de una innovación: del 35 % de los adultos en 2011 al 91 % en 2026. La trayectoria es la curva en S que describió Rogers: arranca lento con los innovadores, se acelera con la mayoría y se satura al final. Bass la formalizó con dos fuerzas: la publicidad, que actúa sobre todos, y la imitación, que depende de cuántos ya adoptaron.

**Diapositiva 3 · Problema (1:00).** El modelo agregado describe la curva pero supone que todos influyen sobre todos. En la vida real la influencia viaja por una red social concreta. Eso deja sin responder tres preguntas: qué pasa sin publicidad, si importa la estructura de la red, y cuánto se pierde con una campaña corta.

**Diapositiva 4 · Justificación (0:50).** La simulación basada en agentes responde a esas preguntas porque representa explícitamente a cada individuo y su red, y permite correr escenarios contrafactuales. Para que no fuera solo un ejercicio cualitativo, calibramos el modelo con datos reales y lo evaluamos contra datos que no usamos para calibrar. Lo hicimos en NetLogo, que es libre y deja todo el modelo en un solo archivo.

**Diapositiva 5 · Objetivos (0:40).** El objetivo general es construir y calibrar el modelo para cuantificar el efecto de la publicidad y de la red sobre la adopción final. Los específicos: implementarlo en NetLogo con tres tipos de red, calibrarlo con partición entrenamiento-validación-prueba, evaluar los escenarios con réplicas e intervalos de confianza, y verificar la implementación con una réplica independiente en Python. *Le paso la palabra a David.*

## Bloque 2 · David (4:10 – 8:30)

**Diapositiva 6 · Modelo conceptual (1:00).** Cada agente es un nodo. Cada mes, quien no ha adoptado lo hace con esta probabilidad: la publicidad lo convence con probabilidad *p* mientras la campaña esté activa, y sus vecinos con probabilidad *q* por la fracción de vecinos que ya adoptaron. Si la red fuera completa, el modelo recupera a Bass; la diferencia entre ambos es el efecto de la red. Las decisiones se aplican todas a la vez al cerrar el mes y la adopción es irreversible.

**Diapositiva 7 · Esquema del sistema (0:40).** Arriba el flujo: los datos reales calibran Bass, que nos da *p*, *q* y *m*; NetLogo simula; BehaviorSpace corre los cuatro experimentos; Python calcula las medidas y las figuras. Abajo, lo que pasa dentro del modelo cada mes.

**Diapositiva 8 · Implementación (0:40).** NetLogo 6.4 con la extensión `nw`. *Configurar* crea la red y siembra los innovadores; *simular* ejecuta un mes en dos fases (decidir y actualizar) para que el orden de los agentes no afecte el resultado; BehaviorSpace corre los experimentos con 30 réplicas y exporta las tablas. Los colores de la figura son los de la interfaz.

**Diapositiva 9 · Conjunto de datos (0:40).** La serie real es de Pew Research Center: 33 encuestas entre 2011 y 2026. La dividimos cronológicamente: entrenamiento hasta 2016, validación 2018–2021 y prueba de 2023 en adelante. El segundo conjunto lo genera la simulación: 1710 corridas, más de 230 mil filas.

**Diapositiva 10 · Medidas de desempeño (0:30).** La principal es el porcentaje de adopción al final del período (10 años). La complementamos con el mes del 50 % y el pico de nuevos adoptantes; frente a la serie real, RMSE y MAPE por partición; todo con 30 réplicas e IC del 95 %.

**Diapositiva 11 · Diseño experimental (0:50).** Con entrenamiento estimamos *p* y *q*; como el potencial de mercado no se identifica desde la fase de crecimiento, lo elegimos en validación, igual que la estructura de red; prueba solo evalúa. Cuatro experimentos: publicidad por densidad, topología por publicidad, duración de la campaña y calibración. Como la separación entre *p* y *q* es sensible al origen temporal, cada escenario se corre con dos niveles de imitación: el calibrado y el típico de la literatura. *Duvan presenta los resultados.*

## Bloque 3 · Duvan (8:30 – 11:40)

**Diapositiva 12 · Calibración (0:50).** El ajuste en entrenamiento da *p* = 0,079 y *q* = 0,242 anuales; validación elige un potencial de mercado del 89 % y, entre nueve estructuras de red, la libre de escala con *k* = 16. En prueba, que nunca tocamos, el error es de ~4 puntos porcentuales, comparable al del modelo agregado. Con los mismos coeficientes, toda red difunde más lento que la mezcla perfecta, porque la influencia se desperdicia entre vecinos que ya adoptaron. *(Las cifras exactas están en la diapositiva; léanlas de ahí.)*

**Diapositiva 13 · Publicidad (0:50).** El resultado central: sin publicidad, con los coeficientes calibrados, en diez años se llega apenas a entre 8 % y 17 %; con campaña permanente, a entre 80 % y 86 %. Con la imitación de la literatura el patrón es el mismo con niveles más altos. La publicidad no es un acelerador: es la condición del despegue.

**Diapositiva 14 · Densidad y topología (0:50).** Sin publicidad, pasar de *k* = 2 a *k* = 16 multiplica la adopción por dos o por tres; con campaña solo añade unos 7 puntos. En topología pasa lo mismo: sin campaña, mundo pequeño es la más lenta (el agrupamiento atrapa la influencia) y libre de escala la más variable (depende de si un hub adopta temprano); con campaña, las tres convergen.

**Diapositiva 15 · Duración (0:40).** Rendimiento fuertemente decreciente: seis meses de publicidad suben la adopción final de 13 % a 29 %; dos años la llevan a 56 %; permanente, 84 %. Con imitación de la literatura, dos años bastan para 75 %. La publicidad vale más al comienzo.

## Bloque 4 · David · Demostración (11:40 – 13:30)

Abrir `modelo/difusion_innovacion.nlogo` antes de empezar la sustentación y dejarlo listo con *mundo pequeño*, *k* = 6, 500 agentes.

1. **configurar** → mostrar la red en anillo con atajos, los innovadores en naranja y los monitores de la red (grado medio, agrupamiento, camino medio).
2. **campaña? apagada → simular** → la mancha turquesa crece despacio alrededor de los innovadores; la curva queda muy por debajo de la de Bass.
3. **campaña? encendida → configurar → simular** → adoptantes nuevos (naranja) por toda la red, curva en S, el monitor *mes del 50 %* se activa.
4. **tipo-red = libre de escala → configurar → simular** → los nodos grandes (hubs) adoptan temprano y arrastran a sus vecinos.
5. **Herramientas → BehaviorSpace** → mostrar los cuatro experimentos y sus factores.

Si el tiempo aprieta, hacer solo 1–3. Si preguntan por el código, mostrar `decidir` y `actualizar` en la pestaña Código: son 25 líneas y ahí está la ecuación.

## Bloque 5 · Duvan (13:30 – 15:00)

**Diapositiva 17 · Conclusiones (1:00).** Tres conclusiones: la publicidad es la condición del despegue; su efecto se concentra en los primeros meses, así que una campaña corta e intensa rinde casi tanto como una permanente; y la estructura de la red solo cambia el resultado cuando la difusión es orgánica. El modelo quedó validado contra datos que no usamos para calibrar. Limitaciones: coeficientes homogéneos, red estática; el siguiente paso sería calibrar con datos colombianos.

**Diapositiva 18 · Referencias (0:30).** Bass y Rogers para la teoría; Goldenberg y Rand para la versión en red y las buenas prácticas de ABM; Watts y Strogatz para mundo pequeño; Sultan para los coeficientes típicos; NetLogo y Pew. Gracias; quedamos atentos a sus preguntas.

## Preguntas probables y respuestas cortas

- **¿Por qué NetLogo y no AnyLogic?** Es libre, el modelo queda en un archivo que cualquiera abre, BehaviorSpace automatiza las réplicas y la extensión `nw` trae los generadores de redes y sus métricas. AnyLogic habría servido igual para el mismo modelo; no necesitábamos sus módulos de eventos discretos ni de dinámica de sistemas.
- **¿Por qué datos de Estados Unidos y no de Colombia?** Pew publica la única serie pública larga y consistente de tenencia de smartphone (33 encuestas, 2011–2026). DANE y la CRC reportan tenencia de celular o cifras sueltas de smartphone, no una serie comparable. El modelo es genérico; con una serie local se recalibra sin cambiar nada más.
- **¿Qué papel tiene cada partición?** Entrenamiento estima *p* y *q* por mínimos cuadrados. Validación elige los hiperparámetros: el potencial de mercado *m* (no identificable desde la fase de crecimiento) y la estructura de red del ABM. Prueba solo mide el error final; no interviene en ninguna decisión.
- **¿Por qué dos valores de q?** Con datos agregados, la separación entre influencia externa e interna depende del origen temporal: distintos orígenes ajustan la curva casi igual con *q* entre 0,06 y 0,33 anual. Por eso evaluamos los escenarios con el valor calibrado y con el promedio de la literatura (Sultan et al., 1990).
- **¿Por qué la curva del ABM va por debajo de la de Bass con los mismos parámetros?** En una red los adoptantes se agrupan: parte de la influencia social de cada adoptante recae en vecinos que ya adoptaron y se desperdicia. En la mezcla perfecta no hay ese desperdicio. Por eso las redes densas y las libres de escala se acercan más a Bass.
- **¿Qué es la actualización sincrónica y por qué importa?** Todos los agentes deciden con el estado del inicio del mes y los cambios se aplican a la vez. Si se actualizara uno por uno, el orden en que NetLogo recorre los agentes cambiaría el resultado.
- **¿Cómo verificaron el modelo?** Con una implementación independiente en Python + networkx de la misma regla; las medias de adopción final de ambas implementaciones coinciden dentro de los intervalos de confianza. Además, con la red completa el ABM recupera la curva de Bass, que es la verificación analítica.
- **¿Por qué 30 réplicas?** Es el tamaño a partir del cual el IC del 95 % de la media con la *t* de Student es estable para estas varianzas; los intervalos resultantes son de ±0,3 a ±2 puntos porcentuales, mucho menores que las diferencias entre escenarios.
- **¿Qué pasaría con una red dinámica o con abandono?** No está en el modelo; son las extensiones que proponemos. Con abandono, la curva de Bass tendría un término de salida y el nivel final sería menor que *m*.
