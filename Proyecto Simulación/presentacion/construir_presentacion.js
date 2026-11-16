// Construye presentacion.pptx a partir de las figuras y cifras generadas por el análisis.
// Uso: node construir_presentacion.js
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const Fi = require("react-icons/fi");
const { applyTheme } = require(process.env.PPTX_SKILL + "/scripts/apply_theme.js");

const RAIZ = path.resolve(__dirname, "..");
const FIG = path.join(RAIZ, "analisis", "figuras", "diapositivas");
const ESQUEMA = path.join(RAIZ, "articulo", "figuras", "esquema_sistema.png");

// ---------------------------------------------------------------- cifras del análisis
const cifras = {};
for (const m of fs.readFileSync(path.join(RAIZ, "articulo", "tablas", "cifras.tex"), "utf8").matchAll(/\\newcommand\{\\cifra(\w+)\}\{([^}]*)\}/g)) {
  cifras[m[1]] = m[2].replace("$\\star$", "").replace("--", "—");
}
const c = (k) => { if (!(k in cifras)) throw new Error("cifra desconocida: " + k); return cifras[k]; };

// ---------------------------------------------------------------- tema
const THEME = {
  name: "Difusión en red",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1B2430", lt1: "FFFFFF", dk2: "55626F", lt2: "EEF2F5",
    accent1: "0E9C98", accent2: "D96C1A", accent3: "6250D6", accent4: "1FC2BC", accent5: "F08A3C", accent6: "8A97A3",
    hlink: "0E9C98", folHlink: "6250D6",
  },
};
const HEX = THEME.colors;
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 × 5.625 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Difusión de una innovación en redes sociales";
pres.author = "J. G. Delgado, D. A. Monroy, D. F. Baquero";
const C = pres.SchemeColor;

const PIE = "Difusión de una innovación en redes sociales  ·  Simulación Computacional  ·  Universidad de los Llanos";

pres.defineSlideMaster({
  title: "CONTENIDO",
  background: { color: HEX.lt1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.3, w: 9.0, h: 0.75, fontSize: 24, bold: true, color: C.text1, margin: 0, align: "left", valign: "middle" } } },
    { text: { text: PIE, options: { x: 0.5, y: 5.2, w: 8.0, h: 0.3, fontSize: 9, color: C.text2, margin: 0, valign: "middle" } } },
  ],
  slideNumber: { x: 9.0, y: 5.2, w: 0.5, h: 0.3, fontSize: 9, color: C.text2, align: "right" },
});
pres.defineSlideMaster({
  title: "OSCURA",
  background: { color: HEX.dk1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.3, w: 9.0, h: 0.75, fontSize: 24, bold: true, color: C.background1, margin: 0, align: "left", valign: "middle" } } },
    { text: { text: PIE, options: { x: 0.5, y: 5.2, w: 8.0, h: 0.3, fontSize: 9, color: C.accent6, margin: 0, valign: "middle" } } },
  ],
  slideNumber: { x: 9.0, y: 5.2, w: 0.5, h: 0.3, fontSize: 9, color: C.accent6, align: "right" },
});
pres.defineSlideMaster({ title: "PORTADA", background: { color: HEX.dk1 }, objects: [] });

// ---------------------------------------------------------------- utilidades
const iconos = {};
async function icono(nombre, color) {
  const clave = nombre + color;
  if (!iconos[clave]) {
    const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Fi[nombre], { color: "#" + color, size: 256, strokeWidth: 1.75 }));
    const buf = await sharp(Buffer.from(svg)).resize(256, 256).png().toBuffer();
    iconos[clave] = "image/png;base64," + buf.toString("base64");
  }
  return iconos[clave];
}

async function iconoEnCirculo(slide, nombre, x, y, d, { fondo = C.accent1, trazo = HEX.lt1, objectName } = {}) {
  slide.addShape(pres.ShapeType.ellipse, { x, y, w: d, h: d, fill: { color: fondo }, line: { color: fondo, width: 0 }, objectName: objectName || "círculo " + nombre });
  slide.addImage({ data: await icono(nombre, trazo), x: x + d * 0.25, y: y + d * 0.25, w: d * 0.5, h: d * 0.5, objectName: "icono " + nombre });
}

function texto(slide, t, o) { slide.addText(t, { isTextBox: true, margin: 0, fontFace: undefined, ...o }); }

// tarjeta con icono, encabezado y descripción
async function tarjeta(slide, { x, y, w, h, icono: ic, titulo, cuerpo, fondo = C.background2, color = C.text1, acento = C.accent1, tamTitulo = 15, tamCuerpo = 12.5 }) {
  slide.addShape(pres.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.12, fill: { color: fondo }, line: { color: fondo, width: 0 }, objectName: "tarjeta " + titulo });
  await iconoEnCirculo(slide, ic, x + 0.25, y + 0.25, 0.55, { fondo: acento });
  texto(slide, titulo, { x: x + 0.95, y: y + 0.22, w: w - 1.15, h: 0.6, fontSize: tamTitulo, bold: true, color, valign: "middle", objectName: "título " + titulo });
  texto(slide, cuerpo, { x: x + 0.25, y: y + 0.95, w: w - 0.5, h: h - 1.1, fontSize: tamCuerpo, color: C.text2, valign: "top", objectName: "texto " + titulo });
}

// nodo numerado (el motivo de la presentación: nodos de una red)
function nodo(slide, n, x, y, d = 0.5, fondo = C.accent1, colorTexto = HEX.lt1) {
  slide.addShape(pres.ShapeType.ellipse, { x, y, w: d, h: d, fill: { color: fondo }, line: { color: fondo, width: 0 }, objectName: "nodo " + n });
  texto(slide, String(n), { x, y, w: d, h: d, fontSize: d >= 0.5 ? 15 : 12, bold: true, color: colorTexto, align: "center", valign: "middle", objectName: "número " + n });
}

function enlace(slide, x1, y1, x2, y2, color = C.accent6, width = 1.25) {
  slide.addShape(pres.ShapeType.line, { x: x1, y: y1, w: x2 - x1, h: y2 - y1, line: { color, width }, objectName: "enlace" });
}

function cifraGrande(slide, valor, etiqueta, x, y, w, { color = C.accent1, tam = 40, tamEtiqueta = 12, align = "left" } = {}) {
  texto(slide, valor, { x, y, w, h: 0.75, fontSize: tam, bold: true, color, align, valign: "bottom", fontFace: THEME.headFontFace, objectName: "cifra " + etiqueta });
  texto(slide, etiqueta, { x, y: y + 0.78, w, h: 0.5, fontSize: tamEtiqueta, color: C.text2, align, valign: "top", objectName: "etiqueta " + etiqueta });
}

function notas(slide, quien, guion) { slide.addNotes(`[${quien}]\n${guion}`); }

const PCT = (k) => c(k) + " %";

(async () => {
  // ================================================================ 1. Portada
  pres.addSection({ title: "Apertura" });
  let s = pres.addSlide({ masterName: "PORTADA", sectionTitle: "Apertura" });
  s.addImage({ path: path.join(FIG, "portada_red.png"), x: 5.1, y: 0.1, w: 5.4, h: 5.4, sizing: { type: "contain", w: 5.4, h: 5.4 }, objectName: "red social con adoptantes" });
  texto(s, "PROYECTO DE CURSO · SIMULACIÓN COMPUTACIONAL", { x: 0.55, y: 0.6, w: 4.6, h: 0.3, fontSize: 10, color: C.accent4, charSpacing: 2, objectName: "antetítulo" });
  texto(s, "Difusión de una innovación en redes sociales", { x: 0.55, y: 1.0, w: 4.6, h: 1.5, fontSize: 30, bold: true, color: C.background1, fontFace: THEME.headFontFace, valign: "top", objectName: "título" });
  texto(s, "Un modelo basado en agentes calibrado con la adopción de teléfonos inteligentes", { x: 0.55, y: 2.55, w: 4.4, h: 0.8, fontSize: 14, color: C.accent6, valign: "top", objectName: "subtítulo" });
  texto(s, [
    { text: "Jesus Gregorio Delgado", options: { bold: true, breakLine: true } }, { text: "160005010", options: { color: C.accent6, breakLine: true } },
    { text: "David Andres Monroy Aguiar", options: { bold: true, breakLine: true } }, { text: "160005019", options: { color: C.accent6, breakLine: true } },
    { text: "Duvan Felipe Baquero Cerquera", options: { bold: true, breakLine: true } }, { text: "160005002", options: { color: C.accent6 } },
  ], { x: 0.55, y: 3.45, w: 4.4, h: 1.35, fontSize: 11.5, color: C.background1, valign: "top", lineSpacingMultiple: 1.05, objectName: "integrantes" });
  texto(s, "Ingeniería de Sistemas · Universidad de los Llanos · noviembre de 2026", { x: 0.55, y: 4.95, w: 4.6, h: 0.3, fontSize: 10, color: C.accent6, objectName: "institución" });
  notas(s, "Jesus · 0:00–0:40", "Buenas tardes. Somos Jesus, David y Duvan. Nuestro proyecto simula cómo una tecnología nueva, como el smartphone, se adopta en una población donde cada persona decide bajo la influencia de la publicidad y de sus contactos. Lo construimos en NetLogo, lo calibramos con datos reales y lo usamos para comparar escenarios que no se pueden observar en la realidad.");

  // ================================================================ 2. Motivación
  pres.addSection({ title: "Planteamiento" });
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Planteamiento" });
  s.addText("Motivación: del 35 % al 91 % de los adultos en 15 años", { placeholder: "title" });
  const hitos = [["35 %", "2011", "innovadores y adoptantes tempranos"], ["77 %", "2016", "mayoría temprana y tardía"], ["91 %", "2026", "saturación: queda el 9 % que no adopta"]];
  enlace(s, 1.0, 2.05, 9.0, 2.05, C.accent6, 1.5);
  for (let i = 0; i < hitos.length; i++) {
    const x = 0.5 + i * 3.1;
    nodo(s, hitos[i][1], x + 0.95, 1.75, 0.6, i === 2 ? C.accent2 : C.accent1);
    cifraGrande(s, hitos[i][0], hitos[i][2], x, 2.5, 2.5, { color: i === 2 ? C.accent2 : C.accent1, tam: 44 });
  }
  texto(s, "Tenencia de teléfono inteligente entre adultos de Estados Unidos (Pew Research Center, Mobile Fact Sheet).", { x: 0.5, y: 3.95, w: 9, h: 0.3, fontSize: 11, italic: true, color: C.text2, objectName: "fuente" });
  texto(s, [
    { text: "Es la curva en S de Rogers. ", options: { bold: true } },
    { text: "Bass la explica con dos fuerzas: una influencia externa —publicidad y medios, que llega a todos por igual— y una influencia interna —imitación, el “voz a voz”— proporcional a cuántos ya adoptaron." },
  ], { x: 0.5, y: 4.3, w: 9, h: 0.8, fontSize: 13.5, color: C.text1, valign: "top", objectName: "explicación" });
  notas(s, "Jesus · 0:40–1:40", "El smartphone es el caso reciente más claro de difusión de una innovación: del 35 % de los adultos en 2011 al 91 % en 2026. La trayectoria es la curva en S que describió Rogers: arranca lento con los innovadores, se acelera con la mayoría y se satura al final. Bass la formalizó con dos fuerzas: la publicidad, que actúa sobre todos, y la imitación, que depende de cuántos ya adoptaron.");

  // ================================================================ 3. Problema
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Planteamiento" });
  s.addText("Problema: el modelo clásico no ve la red", { placeholder: "title" });
  s.addImage({ path: path.join(FIG, "mezcla_vs_red.png"), x: 0.5, y: 1.2, w: 5.2, h: 2.4, sizing: { type: "contain", w: 5.2, h: 2.4 }, objectName: "mezcla perfecta frente a red social" });
  texto(s, "El modelo de Bass supone una población homogénea y perfectamente mezclada: cualquier adoptante influye sobre cualquier otro. En la realidad, cada persona conoce la tecnología, la ve funcionar y la recomienda dentro de su red social.", { x: 6.0, y: 1.2, w: 3.5, h: 2.4, fontSize: 13, color: C.text1, valign: "middle", objectName: "explicación del problema" });
  const preguntas = [["FiRadio", "¿Qué pasa si no hay publicidad y todo depende del contacto social?"], ["FiShare2", "¿Importa que la red sea densa o dispersa, o que tenga unos pocos muy conectados?"], ["FiClock", "¿Cuánto se pierde si la campaña dura dos años en lugar de diez?"]];
  for (let i = 0; i < preguntas.length; i++) {
    const x = 0.5 + i * 3.1;
    await iconoEnCirculo(s, preguntas[i][0], x, 3.85, 0.5, { fondo: i === 0 ? C.accent2 : C.accent1 });
    texto(s, preguntas[i][1], { x: x + 0.65, y: 3.8, w: 2.3, h: 1.2, fontSize: 12.5, color: C.text1, valign: "top", objectName: "pregunta " + (i + 1) });
  }
  notas(s, "Jesus · 1:40–2:40", "El problema es que el modelo agregado describe la curva pero supone que todos influyen sobre todos. En la vida real la influencia viaja por una red social concreta. Eso deja sin responder tres preguntas que le interesan a quien diseña una campaña: qué pasa sin publicidad, si importa la estructura de la red, y cuánto se pierde con una campaña corta.");

  // ================================================================ 4. Justificación
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Planteamiento" });
  s.addText("Justificación: agentes, red explícita y datos reales", { placeholder: "title" });
  const just = [
    ["FiUsers", "Explícito", "Representa a cada persona, su red y su regla de decisión. La estructura social deja de ser un supuesto y pasa a ser un parámetro."],
    ["FiGitBranch", "Contrafactual", "Permite correr escenarios que no existen en los datos: la misma población sin campaña, con otra red o con una campaña más corta."],
    ["FiDatabase", "Anclado en datos", "Se calibra con una serie real de adopción y se evalúa contra datos reservados que no participaron en la calibración."],
  ];
  for (let i = 0; i < just.length; i++) {
    await tarjeta(s, { x: 0.5 + i * 3.1, y: 1.3, w: 2.9, h: 2.75, icono: just[i][0], titulo: just[i][1], cuerpo: just[i][2], acento: i === 1 ? C.accent2 : C.accent1 });
  }
  await iconoEnCirculo(s, "FiCpu", 0.5, 4.3, 0.5, { fondo: C.accent3 });
  texto(s, "Herramienta: NetLogo, libre y reproducible, con BehaviorSpace para automatizar 1710 corridas, y Python para el análisis. El modelo completo cabe en un archivo que cualquiera puede abrir.", { x: 1.15, y: 4.25, w: 8.35, h: 0.65, fontSize: 12.5, color: C.text1, valign: "middle", objectName: "herramienta" });
  notas(s, "Jesus · 2:40–3:30", "La simulación basada en agentes responde a esas preguntas porque representa explícitamente a cada individuo y su red, y porque permite correr escenarios contrafactuales. Para que no fuera solo un ejercicio cualitativo, calibramos el modelo con datos reales y lo evaluamos contra datos que no usamos para calibrar. Lo hicimos en NetLogo, que es libre y deja todo el modelo en un solo archivo.");

  // ================================================================ 5. Objetivos
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Planteamiento" });
  s.addText("Objetivos", { placeholder: "title" });
  s.addShape(pres.ShapeType.roundRect, { x: 0.5, y: 1.25, w: 9.0, h: 1.1, rectRadius: 0.12, fill: { color: C.background2 }, line: { color: C.background2, width: 0 }, objectName: "panel objetivo general" });
  texto(s, [
    { text: "Objetivo general. ", options: { bold: true, color: C.accent1 } },
    { text: "Construir y calibrar un modelo basado en agentes de la difusión de una innovación para cuantificar el efecto de la publicidad y de la estructura de la red social sobre el porcentaje de adopción al final de un período." },
  ], { x: 0.8, y: 1.3, w: 8.4, h: 1.0, fontSize: 14, color: C.text1, valign: "middle", objectName: "objetivo general" });
  const esp = [
    "Implementar en NetLogo la versión en red del modelo de Bass con tres generadores de redes sociales.",
    "Calibrar p, q y m con la serie de adopción de smartphones usando una partición cronológica: entrenamiento, validación y prueba.",
    "Evaluar, con 30 réplicas e intervalos de confianza, los escenarios de publicidad, densidad, topología y duración de la campaña.",
    "Verificar la implementación con una réplica independiente del modelo en Python.",
  ];
  enlace(s, 1.05, 2.95, 1.05, 4.75, C.accent6, 1.25);
  for (let i = 0; i < esp.length; i++) {
    const y = 2.7 + i * 0.6;
    nodo(s, i + 1, 0.8, y, 0.5);
    texto(s, esp[i], { x: 1.5, y, w: 8.0, h: 0.5, fontSize: 12.5, color: C.text1, valign: "middle", objectName: "objetivo específico " + (i + 1) });
  }
  notas(s, "Jesus · 3:30–4:10", "El objetivo general es construir y calibrar el modelo para cuantificar el efecto de la publicidad y de la red sobre la adopción final. Los específicos: implementarlo en NetLogo con tres tipos de red, calibrarlo con datos reales usando partición entrenamiento-validación-prueba, evaluar los escenarios con réplicas e intervalos de confianza, y verificar la implementación con una réplica independiente en Python. Le paso la palabra a David para la metodología.");

  // ================================================================ 6. Modelo conceptual
  pres.addSection({ title: "Metodología" });
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Metodología" });
  s.addText("Metodología: cada mes, cada agente decide si adopta", { placeholder: "title" });
  s.addShape(pres.ShapeType.roundRect, { x: 0.5, y: 1.25, w: 5.4, h: 1.15, rectRadius: 0.12, fill: { color: C.text1 }, line: { color: C.text1, width: 0 }, objectName: "panel ecuación" });
  texto(s, [
    { text: "P", options: {} }, { text: "i", options: { subscript: true } }, { text: " = 1 − (1 − p · a", options: {} }, { text: "t", options: { subscript: true } },
    { text: ") · (1 − q · f", options: {} }, { text: "i", options: { subscript: true } }, { text: ")", options: {} },
  ], { x: 0.7, y: 1.3, w: 5.0, h: 1.05, fontSize: 26, bold: true, color: C.background1, fontFace: THEME.headFontFace, align: "center", valign: "middle", objectName: "regla de adopción" });
  const terminos = [
    ["p", "publicidad", "influencia externa: la campaña llega a todos por igual mientras está activa (aₜ = 1)", C.accent2],
    ["q", "imitación", "influencia social: el agente copia a sus vecinos; q es la fuerza del “voz a voz”", C.accent1],
    ["fᵢ", "vecinos adoptantes", "fracción de los vecinos del agente i que ya adoptaron; crece a medida que se difunde", C.accent1],
    ["m", "potencial de mercado", "fracción de la población que puede llegar a adoptar; el resto sigue en la red sin adoptar", C.accent3],
  ];
  for (let i = 0; i < terminos.length; i++) {
    const y = 2.55 + i * 0.56;
    nodo(s, terminos[i][0], 0.5, y, 0.48, terminos[i][3]);
    texto(s, [{ text: terminos[i][1] + "  ", options: { bold: true } }, { text: terminos[i][2], options: { color: C.text2 } }], { x: 1.1, y, w: 4.8, h: 0.48, fontSize: 11.5, color: C.text1, valign: "middle", objectName: "término " + terminos[i][1] });
  }
  // ilustración: un agente y sus vecinos
  const cx = 8.0, cy = 2.95;
  const vecinos = [[0, -1.05], [0.95, -0.5], [0.95, 0.5], [0, 1.05], [-0.95, 0.5], [-0.95, -0.5]];
  vecinos.forEach(([dx, dy], i) => enlace(s, cx + 0.2, cy + 0.2, cx + dx + 0.2, cy + dy + 0.2, C.accent6, 1.25));
  vecinos.forEach(([dx, dy], i) => s.addShape(pres.ShapeType.ellipse, { x: cx + dx, y: cy + dy, w: 0.4, h: 0.4, fill: { color: i < 2 ? C.accent1 : C.accent6 }, line: { color: C.background1, width: 1 }, objectName: "vecino " + (i + 1) }));
  s.addShape(pres.ShapeType.ellipse, { x: cx - 0.05, y: cy - 0.05, w: 0.5, h: 0.5, fill: { color: C.background1 }, line: { color: C.text1, width: 1.5 }, objectName: "agente i" });
  texto(s, "i", { x: cx - 0.05, y: cy - 0.05, w: 0.5, h: 0.5, fontSize: 13, bold: true, italic: true, color: C.text1, align: "center", valign: "middle", fontFace: THEME.headFontFace, objectName: "letra i" });
  texto(s, "fᵢ = 2 / 6: dos de sus seis vecinos ya adoptaron", { x: 6.3, y: 4.45, w: 3.4, h: 0.3, fontSize: 11, color: C.text2, align: "center", objectName: "lectura de f" });
  texto(s, "Supuestos: adopción irreversible · decisiones simultáneas al cerrar el mes · red estática · 2,5 % de innovadores iniciales", { x: 0.5, y: 4.88, w: 9, h: 0.3, fontSize: 10.5, italic: true, color: C.text2, objectName: "supuestos" });
  notas(s, "David · 4:10–5:10", "El modelo es la versión en red del modelo de Bass. Cada agente es un nodo. Cada mes, quien no ha adoptado lo hace con esta probabilidad: la publicidad lo convence con probabilidad p mientras la campaña esté activa, y sus vecinos lo convencen con probabilidad q por la fracción de vecinos que ya adoptaron. Si la red fuera completa, el modelo recupera a Bass; la diferencia entre ambos es el efecto de la red. Las decisiones se aplican todas a la vez al cerrar el mes y la adopción es irreversible.");

  // ================================================================ 7. Esquema del sistema
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Metodología" });
  s.addText("Esquema del sistema desarrollado", { placeholder: "title" });
  s.addImage({ path: ESQUEMA, x: 0.5, y: 1.2, w: 9.0, h: 3.6, sizing: { type: "contain", w: 9.0, h: 3.6 }, objectName: "esquema del sistema: calibración, modelo, experimentos y análisis" });
  texto(s, "Arriba, el flujo de trabajo: la serie real calibra p, q y m; NetLogo simula; BehaviorSpace corre los experimentos; Python analiza. Abajo, el interior del modelo: la red provee fᵢ, la campaña provee aₜ, la regla decide.", { x: 0.5, y: 4.8, w: 9, h: 0.35, fontSize: 10.5, italic: true, color: C.text2, objectName: "lectura del esquema" });
  notas(s, "David · 5:10–5:50", "Este es el sistema completo. Arriba el flujo: los datos reales calibran el modelo de Bass, que nos da p, q y m; con ellos NetLogo genera la red y simula; BehaviorSpace corre los cuatro experimentos y Python calcula las medidas y las figuras. Abajo, lo que pasa dentro del modelo cada mes: la red entrega la fracción de vecinos adoptantes, la campaña entrega la señal de publicidad, y la regla decide quién cambia de estado.");

  // ================================================================ 8. Implementación
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Metodología" });
  s.addText("Implementación en NetLogo con la extensión nw", { placeholder: "title" });
  s.addImage({ path: path.join(FIG, "redes.png"), x: 0.5, y: 1.15, w: 9.0, h: 3.15, sizing: { type: "contain", w: 9.0, h: 3.15 }, objectName: "tres tipos de red generados por el modelo" });
  const impl = [
    ["configurar", "genera la red (aleatoria, mundo pequeño o libre de escala) con grado promedio k, marca el potencial de mercado y siembra los innovadores"],
    ["simular", "cada mes: decidir (cada no adoptante calcula fᵢ y sortea) y actualizar (aplica todo a la vez); dibuja la curva frente a la de Bass"],
    ["BehaviorSpace", "4 experimentos × 30 réplicas definidos en el mismo archivo; exportan CSV con una fila por corrida y mes"],
  ];
  for (let i = 0; i < impl.length; i++) {
    const x = 0.5 + i * 3.1;
    texto(s, [{ text: impl[i][0], options: { bold: true, color: C.accent1, breakLine: true } }, { text: impl[i][1], options: { color: C.text2 } }], { x, y: 4.38, w: 2.9, h: 0.8, fontSize: 10.5, color: C.text1, valign: "top", objectName: "implementación " + impl[i][0] });
  }
  notas(s, "David · 5:50–6:30", "Lo implementamos en NetLogo con la extensión nw (el archivo es de la versión 6.4 y los experimentos los corrimos en la 7.0.4), que genera las tres familias de redes y mide agrupamiento y longitud de camino. Configurar crea la red y siembra los innovadores; simular ejecuta un mes en dos fases para que el orden de los agentes no afecte el resultado; y BehaviorSpace corre los cuatro experimentos con treinta réplicas y exporta las tablas. Los colores que ven aquí son los de la interfaz: gris no adoptante, turquesa adoptante, naranja adoptó este mes.");

  // ================================================================ 9. Conjunto de datos
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Metodología" });
  s.addText("Conjunto de datos: la serie real y los datos simulados", { placeholder: "title" });
  s.addImage({ path: path.join(FIG, "pew.png"), x: 0.4, y: 1.15, w: 5.6, h: 3.15, sizing: { type: "contain", w: 5.6, h: 3.15 }, objectName: "serie de Pew con la partición" });
  texto(s, "Serie real: 33 encuestas de Pew Research Center (2011–2026), porcentaje de adultos de EE. UU. con smartphone. Partición cronológica: entrenamiento 2011–2016 (26 obs.), validación 2018–2021 (3), prueba 2023–2026 (4).", { x: 0.5, y: 4.3, w: 5.4, h: 0.8, fontSize: 11, color: C.text2, valign: "top", objectName: "descripción serie real" });
  s.addShape(pres.ShapeType.roundRect, { x: 6.3, y: 1.2, w: 3.2, h: 3.9, rectRadius: 0.12, fill: { color: C.background2 }, line: { color: C.background2, width: 0 }, objectName: "panel datos simulados" });
  await iconoEnCirculo(s, "FiDatabase", 6.55, 1.45, 0.5, { fondo: C.accent3 });
  texto(s, "Datos de la simulación", { x: 7.15, y: 1.42, w: 2.3, h: 0.55, fontSize: 14, bold: true, color: C.text1, valign: "middle", objectName: "título datos simulados" });
  cifraGrande(s, "1710", "corridas de 1000 agentes", 6.55, 2.05, 2.8, { color: C.accent3, tam: 30, tamEtiqueta: 11 });
  cifraGrande(s, "230 000", "filas: una por corrida y mes", 6.55, 3.0, 2.8, { color: C.accent3, tam: 30, tamEtiqueta: 11 });
  texto(s, "Columnas: parámetros, mes, % adopción, nuevos, mes del 50 %, pico, propiedades de la red.", { x: 6.55, y: 4.1, w: 2.75, h: 0.9, fontSize: 10.5, color: C.text2, valign: "top", objectName: "columnas" });
  notas(s, "David · 6:30–7:10", "Usamos dos conjuntos de datos. El real es la serie de Pew Research Center de tenencia de smartphone en adultos de Estados Unidos: 33 encuestas entre 2011 y 2026. La dividimos cronológicamente, como corresponde a una serie de tiempo: entrenamiento hasta 2016, validación de 2018 a 2021 y prueba de 2023 en adelante, que no se usa para ninguna decisión. El segundo conjunto lo genera la simulación: 1710 corridas con una fila por mes, más de 230 mil filas.");

  // ================================================================ 10. Medidas de desempeño
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Metodología" });
  s.addText("Medidas de desempeño", { placeholder: "title" });
  const med = [
    ["FiTarget", "Adopción final (%)", "Medida principal: fracción de la población que adoptó a los 120 meses (10 años).", C.accent1],
    ["FiTrendingUp", "T₅₀ y pico", "Mes en que se alcanza el 50 % (velocidad del despegue) y mayor número de nuevos adoptantes en un mes.", C.accent1],
    ["FiActivity", "RMSE y MAPE", "Error de la curva simulada frente a la serie real, en cada partición y en puntos porcentuales.", C.accent2],
    ["FiRepeat", "30 réplicas", "Cada escenario se corre 30 veces con semillas distintas: media e intervalo de confianza del 95 % (t de Student).", C.accent3],
  ];
  for (let i = 0; i < med.length; i++) {
    await tarjeta(s, { x: 0.5 + (i % 2) * 4.6, y: 1.25 + Math.floor(i / 2) * 1.95, w: 4.4, h: 1.8, icono: med[i][0], titulo: med[i][1], cuerpo: med[i][2], acento: med[i][3], tamCuerpo: 12 });
  }
  notas(s, "David · 7:10–7:40", "La medida principal, como pide el proyecto, es el porcentaje de adopción al final del período, diez años. La complementamos con el mes en que se alcanza el 50 %, que mide la velocidad, y el pico de nuevos adoptantes. Frente a la serie real usamos RMSE y MAPE por partición. Y todo se reporta con treinta réplicas e intervalos de confianza del 95 %.");

  // ================================================================ 11. Diseño experimental
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Metodología" });
  s.addText("Diseño experimental: partición y cuatro experimentos", { placeholder: "title" });
  // barra de partición 2007–2027
  const x0 = 0.5, anchoAnios = 9.0 / 20; // 2007 → 2027
  const anio = (a) => x0 + (a - 2007) * anchoAnios;
  s.addShape(pres.ShapeType.rect, { x: x0, y: 1.45, w: 9.0, h: 0.45, fill: { color: C.background2 }, line: { color: C.background2, width: 0 }, objectName: "línea de tiempo" });
  const bloques = [["entrenamiento", 2011, 2017, C.accent1], ["validación", 2018, 2022, C.accent3], ["prueba", 2023, 2027, C.accent2]];
  for (const [n, a, b, col] of bloques) {
    s.addShape(pres.ShapeType.rect, { x: anio(a), y: 1.45, w: anio(b) - anio(a), h: 0.45, fill: { color: col }, line: { color: col, width: 0 }, objectName: "partición " + n });
    texto(s, n, { x: anio(a), y: 1.45, w: anio(b) - anio(a), h: 0.45, fontSize: 11, bold: true, color: C.background1, align: "center", valign: "middle", objectName: "rótulo " + n });
  }
  for (const a of [2007, 2011, 2017, 2022, 2027]) {
    texto(s, String(a), { x: anio(a) - 0.4, y: 1.95, w: 0.8, h: 0.25, fontSize: 9.5, color: C.text2, align: "center", objectName: "año " + a });
  }
  texto(s, "junio de 2007: origen de la simulación de calibración (lanzamiento del iPhone)", { x: 0.5, y: 1.15, w: 6, h: 0.25, fontSize: 9.5, italic: true, color: C.text2, objectName: "nota origen" });
  texto(s, "estima p, q · elige m y la red · solo evalúa", { x: 5.0, y: 1.15, w: 4.5, h: 0.25, fontSize: 9.5, italic: true, color: C.text2, align: "right", objectName: "roles partición" });
  const filas = [
    [{ text: "exp.", options: { bold: true, color: C.background1, fill: { color: C.text1 } } }, { text: "factores y niveles", options: { bold: true, color: C.background1, fill: { color: C.text1 } } }, { text: "corridas", options: { bold: true, color: C.background1, fill: { color: C.text1 }, align: "right" } }],
    ["E1  publicidad × densidad", "campaña {sin, con} × k ∈ {2, 4, 6, 8, 12, 16} × q ∈ {0,020 calibrado; 0,032 literatura}", "720"],
    ["E2  topología × publicidad", "red {aleatoria, mundo pequeño, libre de escala} × campaña × q", "360"],
    ["E3  duración de la campaña", "{0, 6, 12, 24, 60, 120} meses × q", "360"],
    ["E4  calibración con datos reales", "3 topologías × k ∈ {4, 8, 16}, q calibrado, m = " + c("BassM") + " %, 228 meses", "270"],
  ].map((f, i) => (i === 0 ? f : [{ text: f[0], options: { bold: true } }, { text: f[1] }, { text: f[2], options: { align: "right" } }]));
  s.addTable(filas, { x: 0.5, y: 2.4, w: 9.0, colW: [2.6, 5.5, 0.9], fontSize: 11, color: C.text1, border: { type: "solid", color: HEX.lt2, pt: 0.75 }, rowH: 0.42, valign: "middle", margin: 0.06, objectName: "tabla de experimentos" });
  texto(s, "Fijos: N = 1000 · mundo pequeño (β = 0,1), k = 6 · 2,5 % innovadores · p = " + c("BassPmes") + " mensual · 120 meses · 30 réplicas por combinación", { x: 0.5, y: 4.72, w: 9, h: 0.3, fontSize: 10.5, italic: true, color: C.text2, objectName: "parámetros fijos" });
  notas(s, "David · 7:40–8:30", "La partición es cronológica. Con entrenamiento estimamos p y q; como el potencial de mercado no se identifica desde la fase de crecimiento, lo elegimos en validación, igual que la estructura de red del modelo de agentes; prueba solo evalúa. Los cuatro experimentos: publicidad por densidad, topología por publicidad, duración de la campaña y calibración con datos reales. Como la separación entre p y q es sensible al origen temporal, cada escenario se corre con dos niveles de imitación: el calibrado y el típico de la literatura.");

  // ================================================================ 12. Calibración
  pres.addSection({ title: "Resultados" });
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Resultados" });
  s.addText("Calibración: el modelo reproduce la serie de prueba", { placeholder: "title" });
  s.addImage({ path: path.join(FIG, "fig_calibracion.png"), x: 0.4, y: 1.2, w: 6.0, h: 3.2, sizing: { type: "contain", w: 6.0, h: 3.2 }, objectName: "serie real, Bass ajustado y ABM" });
  texto(s, "Puntos: serie real por partición. Línea gris: Bass ajustado. Turquesa: ABM con la estructura elegida en validación (banda: IC 95 %).", { x: 0.5, y: 4.5, w: 5.8, h: 0.5, fontSize: 10.5, italic: true, color: C.text2, objectName: "lectura calibración" });
  texto(s, [
    { text: "Ajuste de Bass (anual)", options: { bold: true, breakLine: true } },
    { text: "p = " + c("BassP") + "   q = " + c("BassQ") + "   m = " + c("BassM") + " %", options: { color: C.text2, breakLine: true } },
    { text: " ", options: { fontSize: 6, breakLine: true } },
    { text: "Estructura elegida en validación", options: { bold: true, breakLine: true } },
    { text: "red " + c("AbmSelRed") + ", k = " + c("AbmSelK") + " (RMSE " + c("AbmRmseVal") + " pp)", options: { color: C.text2 } },
  ], { x: 6.7, y: 1.2, w: 2.9, h: 1.6, fontSize: 12, color: C.text1, valign: "top", objectName: "parámetros calibrados" });
  cifraGrande(s, c("AbmRmsePru") + " pp", "RMSE del ABM en prueba (Bass: " + c("BassRmsePru") + " pp)", 6.7, 2.95, 2.9, { color: C.accent1, tam: 34, tamEtiqueta: 11 });
  texto(s, "Con los mismos coeficientes, toda red difunde algo más lento que la mezcla perfecta: los adoptantes se agrupan y parte de su influencia cae en vecinos que ya adoptaron.", { x: 6.7, y: 4.2, w: 2.9, h: 0.9, fontSize: 10.5, color: C.text2, valign: "top", objectName: "interpretación calibración" });
  notas(s, "Duvan · 8:30–9:20", "Primero la calibración. El ajuste de Bass en entrenamiento da p = " + c("BassP") + " y q = " + c("BassQ") + " anuales, y validación elige un potencial de mercado del " + c("BassM") + " %. Entre las nueve estructuras de red, validación escoge la " + c("AbmSelRed") + " con k = " + c("AbmSelK") + ". En la partición de prueba, que nunca tocamos, el error es de " + c("AbmRmsePru") + " puntos porcentuales, comparable al del modelo agregado. Un detalle interesante: con los mismos coeficientes, cualquier red difunde más lento que la mezcla perfecta, porque la influencia se desperdicia entre vecinos que ya adoptaron.");

  // ================================================================ 13. Publicidad
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Resultados" });
  s.addText("Sin publicidad no hay despegue; con campaña, curva en S", { placeholder: "title" });
  s.addImage({ path: path.join(FIG, "fig_curvas.png"), x: 0.4, y: 1.15, w: 6.3, h: 3.2, sizing: { type: "contain", w: 6.3, h: 3.2 }, objectName: "curvas de adopción con y sin campaña" });
  cifraGrande(s, PCT("SinCalKDieciseis"), "adopción a 10 años sin campaña (red densa, q calibrado)", 7.0, 1.2, 2.6, { color: C.accent2, tam: 36, tamEtiqueta: 11 });
  cifraGrande(s, PCT("ConCalKDieciseis"), "con campaña permanente en la misma red", 7.0, 2.55, 2.6, { color: C.accent1, tam: 36, tamEtiqueta: 11 });
  texto(s, "Sin campaña, ninguna configuración alcanza el 50 % en diez años; con campaña se alcanza hacia el mes " + c("TcincuentaConCalKSeis") + " (q calibrado) o " + c("TcincuentaConLitKSeis") + " (q de la literatura).", { x: 0.5, y: 4.45, w: 6.2, h: 0.6, fontSize: 11.5, color: C.text1, valign: "top", objectName: "lectura publicidad" });
  texto(s, "La publicidad no acelera la difusión: la hace posible.", { x: 7.0, y: 4.0, w: 2.6, h: 0.9, fontSize: 13, bold: true, italic: true, color: C.text1, valign: "top", fontFace: THEME.headFontFace, objectName: "mensaje publicidad" });
  notas(s, "Duvan · 9:20–10:10", "Este es el resultado central. Sin publicidad, con los coeficientes calibrados, la difusión depende solo de los innovadores iniciales y en diez años llega apenas al " + c("SinCalMin") + " – " + c("SinCalMax") + " %. Con una campaña permanente la curva toma la forma de S y llega al " + c("ConCalMin") + " – " + c("ConCalMax") + " %. Con la imitación más fuerte de la literatura, a la derecha, el patrón es el mismo con niveles más altos. La publicidad no es un acelerador: es la condición para que la innovación despegue.");

  // ================================================================ 14. Densidad y topología
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Resultados" });
  s.addText("La red importa cuando la difusión es orgánica", { placeholder: "title" });
  s.addImage({ path: path.join(FIG, "fig_densidad.png"), x: 0.4, y: 1.15, w: 6.1, h: 3.1, sizing: { type: "contain", w: 6.1, h: 3.1 }, objectName: "adopción final frente al grado promedio" });
  texto(s, [
    { text: "Densidad. ", options: { bold: true, color: C.accent1 } },
    { text: "Sin publicidad, pasar de k = 2 a k = 16 multiplica la adopción final por " + c("DensidadRazonSinCal") + " (q calibrado) y por " + c("DensidadRazonSinLit") + " (q literatura). Con campaña solo añade unos " + c("DensidadGananciaCon") + " puntos: la publicidad siembra adoptantes en toda la red." },
  ], { x: 6.8, y: 1.2, w: 2.8, h: 1.9, fontSize: 11.5, color: C.text1, valign: "top", objectName: "lectura densidad" });
  texto(s, [
    { text: "Topología (k = 6, sin campaña, q = 0,032). ", options: { bold: true, color: C.accent3 } },
    { text: "Mundo pequeño " + c("TopoSinLitMundo") + " %: el agrupamiento (C = " + c("EstMundoC") + ") atrapa la influencia en grupos ya convencidos. Aleatoria " + c("TopoSinLitAleatoria") + " % y libre de escala " + c("TopoSinLitEscala") + " %, esta última la más variable (DE " + c("TopoSinLitEscalaDe") + "): si un nodo muy conectado adopta temprano, hay cascada. Con campaña, las tres convergen." },
  ], { x: 6.8, y: 3.2, w: 2.8, h: 1.9, fontSize: 11.5, color: C.text1, valign: "top", objectName: "lectura topología" });
  s.addShape(pres.ShapeType.roundRect, { x: 0.5, y: 4.35, w: 6.0, h: 0.75, rectRadius: 0.12, fill: { color: C.background2 }, line: { color: C.background2, width: 0 }, objectName: "panel asimetría" });
  await iconoEnCirculo(s, "FiShare2", 0.7, 4.475, 0.5, { fondo: C.accent1 });
  texto(s, "Asimetría: la densidad y la topología cambian mucho el resultado sin publicidad y casi nada con ella. Con campaña, ningún agente depende de que la influencia le llegue por un camino largo.", { x: 1.35, y: 4.38, w: 5.05, h: 0.7, fontSize: 11.5, color: C.text1, valign: "middle", objectName: "mensaje asimetría" });
  notas(s, "Duvan · 10:10–11:00", "¿Y la red? Sin publicidad, la densidad importa mucho: de k igual a 2 a k igual a 16 la adopción se multiplica por " + c("DensidadRazonSinCal") + " con el q calibrado y por " + c("DensidadRazonSinLit") + " con el de la literatura. Con campaña, el mismo cambio solo añade unos " + c("DensidadGananciaCon") + " puntos. En topología pasa lo mismo: sin campaña, la red de mundo pequeño es la más lenta porque su alto agrupamiento atrapa la influencia, y la libre de escala es la más variable, porque depende de si un hub adopta temprano. Con campaña, las tres convergen.");

  // ================================================================ 15. Duración de la campaña
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Resultados" });
  s.addText("Dos años de campaña logran el " + c("DurCalFraccionVeinticuatro") + " % del efecto", { placeholder: "title" });
  s.addImage({ path: path.join(FIG, "fig_duracion.png"), x: 0.5, y: 1.2, w: 4.6, h: 3.1, sizing: { type: "contain", w: 4.6, h: 3.1 }, objectName: "adopción final según duración de la campaña" });
  texto(s, "Adopción final a 120 meses según los meses de campaña, para los dos niveles de q (media e IC 95 %).", { x: 0.5, y: 4.45, w: 4.6, h: 0.5, fontSize: 10.5, italic: true, color: C.text2, objectName: "leyenda duración" });
  const dur = [["0", c("DurCalDCero")], ["6", c("DurCalDSeis")], ["24", c("DurCalDVeinticuatro")], ["60", c("DurCalDSesenta")], ["120", c("DurCalDCientoveinte")]];
  texto(s, "meses de campaña  →  adopción final (q calibrado)", { x: 5.6, y: 1.2, w: 3.9, h: 0.3, fontSize: 11, bold: true, color: C.text1, objectName: "encabezado duración" });
  enlace(s, 5.85, 1.95, 5.85, 4.0, C.accent6, 1.25);
  for (let i = 0; i < dur.length; i++) {
    const y = 1.6 + i * 0.52;
    nodo(s, dur[i][0], 5.6, y, 0.5, i === 0 ? C.accent2 : C.accent1);
    texto(s, dur[i][1] + " %", { x: 6.3, y, w: 1.3, h: 0.5, fontSize: 18, bold: true, color: C.text1, valign: "middle", fontFace: THEME.headFontFace, objectName: "adopción duración " + dur[i][0] });
    const nota = ["sin publicidad", "+" + c("DurCalGananciaSeis") + " puntos en seis meses", "dos años", "cinco años", "campaña permanente"][i];
    texto(s, nota, { x: 7.65, y, w: 1.9, h: 0.5, fontSize: 11, color: C.text2, valign: "middle", objectName: "nota duración " + dur[i][0] });
  }
  texto(s, "Con q de la literatura, dos años de campaña bastan para " + c("DurLitDVeinticuatro") + " % (el " + c("DurLitFraccionVeinticuatro") + " % del efecto): la imitación sostiene la difusión una vez sembrados suficientes adoptantes.", { x: 5.6, y: 4.3, w: 3.9, h: 0.7, fontSize: 11, color: C.text1, valign: "top", objectName: "lectura duración" });
  notas(s, "Duvan · 11:00–11:40", "El tercer experimento interrumpe la campaña después de cierto número de meses. El rendimiento es fuertemente decreciente: los primeros seis meses elevan la adopción final de " + c("DurCalDCero") + " a " + c("DurCalDSeis") + " %, dos años la llevan a " + c("DurCalDVeinticuatro") + " % y una campaña permanente a " + c("DurCalDCientoveinte") + " %. Con la imitación de la literatura, dos años bastan para " + c("DurLitDVeinticuatro") + " %. La publicidad vale más al comienzo, cuando la influencia social todavía es débil.");

  // ================================================================ 16. Demostración
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Resultados" });
  s.addText("Demostración en NetLogo", { placeholder: "title" });
  const demo = [
    ["Configurar", "mundo pequeño, k = 6, 500 agentes: la red en anillo con atajos; los innovadores en naranja."],
    ["Simular sin campaña", "campaña? apagada: la mancha turquesa crece despacio alrededor de los innovadores y la curva queda lejos de la de Bass."],
    ["Activar la campaña", "campaña? encendida: adoptantes nuevos en toda la red, curva en S, el monitor del 50 % se activa."],
    ["Cambiar la topología", "libre de escala: los nodos grandes (hubs) adoptan temprano y arrastran a sus vecinos."],
    ["Abrir BehaviorSpace", "Herramientas → BehaviorSpace: los cuatro experimentos con sus factores y 30 réplicas."],
  ];
  enlace(s, 0.75, 1.65, 0.75, 4.45, C.accent6, 1.25);
  for (let i = 0; i < demo.length; i++) {
    const y = 1.3 + i * 0.72;
    nodo(s, i + 1, 0.5, y, 0.5);
    texto(s, [{ text: demo[i][0] + "  ", options: { bold: true } }, { text: demo[i][1], options: { color: C.text2 } }], { x: 1.2, y, w: 4.9, h: 0.62, fontSize: 11.5, color: C.text1, valign: "middle", objectName: "paso demo " + (i + 1) });
  }
  s.addShape(pres.ShapeType.roundRect, { x: 6.4, y: 1.3, w: 3.1, h: 3.6, rectRadius: 0.12, fill: { color: C.text1 }, line: { color: C.text1, width: 0 }, objectName: "panel qué observar" });
  texto(s, "Qué observar", { x: 6.65, y: 1.4, w: 2.6, h: 0.4, fontSize: 14, bold: true, color: C.background1, objectName: "título qué observar" });
  texto(s, [
    { text: "Colores: ", options: { bold: true, color: C.accent4 } }, { text: "gris no adopta · turquesa adoptante · naranja adoptó este mes · gris oscuro fuera del mercado", options: { breakLine: true } },
    { text: " ", options: { fontSize: 6, breakLine: true } },
    { text: "Gráfica: ", options: { bold: true, color: C.accent4 } }, { text: "la curva del modelo en red frente a la de Bass con los mismos parámetros", options: { breakLine: true } },
    { text: " ", options: { fontSize: 6, breakLine: true } },
    { text: "Monitores: ", options: { bold: true, color: C.accent4 } }, { text: "% adopción, mes del 50 %, pico, grado medio, agrupamiento y camino medio de la red generada", options: { breakLine: true } },
    { text: " ", options: { fontSize: 6, breakLine: true } },
    { text: "Semilla: ", options: { bold: true, color: C.accent4 } }, { text: "fijarla reproduce exactamente una corrida" },
  ], { x: 6.65, y: 1.85, w: 2.65, h: 2.95, fontSize: 11, color: C.background1, valign: "top", objectName: "qué observar" });
  notas(s, "David · 11:40–13:30 (demo en vivo)", "Abrimos difusion_innovacion.nlogo. Paso 1: configurar con mundo pequeño y k = 6. Paso 2: simular sin campaña y ver cómo la adopción apenas crece alrededor de los innovadores. Paso 3: encender campaña y repetir: la curva en S y los adoptantes nuevos apareciendo por toda la red. Paso 4: cambiar a libre de escala y mostrar los hubs. Paso 5: abrir BehaviorSpace para mostrar cómo se definieron los experimentos. Si el tiempo aprieta, hacer solo los pasos 1 a 3.");

  // ================================================================ 17. Conclusiones
  pres.addSection({ title: "Cierre" });
  s = pres.addSlide({ masterName: "OSCURA", sectionTitle: "Cierre" });
  s.addText("Conclusiones", { placeholder: "title" });
  const concl = [
    ["FiRadio", "La publicidad es la condición del despegue", "Con los coeficientes calibrados, la difusión orgánica llega como máximo al " + c("SinCalMax") + " % en diez años; con campaña permanente, al menos al " + c("ConCalMin") + " %.", C.accent2],
    ["FiClock", "Su efecto se concentra al inicio", "Dos años de campaña logran el " + c("DurCalFraccionVeinticuatro") + " % del efecto de una permanente; con imitación fuerte, el " + c("DurLitFraccionVeinticuatro") + " %.", C.accent4],
    ["FiShare2", "La red importa cuando la difusión es orgánica", "Más densidad y caminos cortos aceleran; el agrupamiento frena; los hubs generan cascadas. Con publicidad, la estructura deja de importar.", C.accent4],
  ];
  for (let i = 0; i < concl.length; i++) {
    const x = 0.5 + i * 3.1;
    await iconoEnCirculo(s, concl[i][0], x, 1.3, 0.6, { fondo: concl[i][3], trazo: HEX.dk1 });
    texto(s, concl[i][1], { x, y: 2.05, w: 2.9, h: 0.8, fontSize: 15, bold: true, color: C.background1, valign: "top", fontFace: THEME.headFontFace, objectName: "conclusión " + (i + 1) });
    texto(s, concl[i][2], { x, y: 2.9, w: 2.9, h: 1.2, fontSize: 11.5, color: C.accent6, valign: "top", objectName: "detalle conclusión " + (i + 1) });
  }
  texto(s, [
    { text: "Validación: ", options: { bold: true, color: C.accent4 } }, { text: "error de " + c("AbmRmsePru") + " puntos porcentuales en la partición de prueba, comparable al modelo agregado de Bass (" + c("BassRmsePru") + ").", options: { breakLine: true } },
    { text: "Limitaciones y trabajo futuro: ", options: { bold: true, color: C.accent4 } }, { text: "coeficientes homogéneos, red estática, p y q poco identificables con datos agregados; umbrales heterogéneos, redes dinámicas y calibración con datos colombianos." },
  ], { x: 0.5, y: 4.2, w: 9.0, h: 0.85, fontSize: 11, color: C.background1, valign: "top", objectName: "validación y limitaciones" });
  notas(s, "Duvan · 13:30–14:30", "Tres conclusiones. Primera: la publicidad no es un acelerador sino la condición del despegue. Segunda: su efecto se concentra en los primeros meses: dos años de campaña logran el " + c("DurCalFraccionVeinticuatro") + " % del efecto de una permanente, y el " + c("DurLitFraccionVeinticuatro") + " % con imitación fuerte. Tercera: la estructura de la red solo cambia el resultado cuando la difusión es orgánica. El modelo quedó validado contra datos que no usamos para calibrar, con un error comparable al del modelo de Bass. Como limitaciones, los coeficientes son homogéneos y la red es estática; el siguiente paso sería calibrarlo con datos colombianos.");

  // ================================================================ 18. Referencias
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Cierre" });
  s.addText("Referencias", { placeholder: "title" });
  const refs = [
    "Bass, F. M. (1969). A new product growth model for consumer durables. Management Science, 15(5), 215–227.",
    "Rogers, E. M. (2003). Diffusion of Innovations (5.ª ed.). Free Press.",
    "Goldenberg, J., Libai, B. y Muller, E. (2001). Talk of the network: a complex systems look at the underlying process of word-of-mouth. Marketing Letters, 12(3), 211–223.",
    "Rand, W. y Rust, R. T. (2011). Agent-based modeling in marketing: guidelines for rigor. International Journal of Research in Marketing, 28(3), 181–193.",
    "Watts, D. J. y Strogatz, S. H. (1998). Collective dynamics of ‘small-world’ networks. Nature, 393, 440–442.",
    "Sultan, F., Farley, J. U. y Lehmann, D. R. (1990). A meta-analysis of applications of diffusion models. Journal of Marketing Research, 27(1), 70–77.",
    "Wilensky, U. (1999). NetLogo. Center for Connected Learning and Computer-Based Modeling, Northwestern University. ccl.northwestern.edu/netlogo",
    "Pew Research Center (2026). Mobile Fact Sheet. pewresearch.org/internet/fact-sheet/mobile",
  ];
  for (let i = 0; i < refs.length; i++) {
    const col = i % 2, fila = Math.floor(i / 2);
    const x = 0.5 + col * 4.65, y = 1.3 + fila * 0.95;
    nodo(s, i + 1, x, y + 0.05, 0.38, fila % 2 === col % 2 ? C.accent1 : C.accent3);
    texto(s, refs[i], { x: x + 0.5, y, w: 3.95, h: 0.9, fontSize: 10.5, color: C.text1, valign: "top", objectName: "referencia " + (i + 1) });
  }
  notas(s, "Duvan · 14:30–15:00", "Estas son las referencias en las que se apoya el modelo: Bass y Rogers para la teoría de difusión, Goldenberg y Rand para la versión en red y las buenas prácticas de modelado basado en agentes, Watts y Strogatz para las redes de mundo pequeño, Sultan para los valores típicos de los coeficientes, NetLogo y los datos de Pew. Gracias; quedamos atentos a sus preguntas.");

  const salida = path.join(__dirname, "presentacion.pptx");
  await pres.writeFile({ fileName: salida });
  await applyTheme(salida, THEME);
  console.log("escrito", salida);
})().catch((e) => { console.error(e); process.exit(1); });
