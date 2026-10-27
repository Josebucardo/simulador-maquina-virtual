/** PowerPoint editable a partir de la implementación y evidencias del grupo 13.
 * La aplicación Python no necesita Node. Para regenerar: npm ci --prefix presentation
 * y node scripts/generar_presentacion.mjs.
 * @oai/artifact-tool no está disponible en este entorno; se exporta OOXML con PptxGenJS.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import { spawnSync } from 'node:child_process';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
let require;
for (const dir of ['presentation', 'tmp/presentationdeps']) {
  const manifest = path.join(ROOT, dir, 'package.json');
  if (fs.existsSync(manifest)) {
    const candidate = createRequire(manifest);
    try { candidate.resolve('pptxgenjs'); require = candidate; break; } catch {}
  }
}
if (!require) throw new Error('Ejecuta npm ci --prefix presentation para regenerar el PowerPoint.');
const PptxGenJS = require('pptxgenjs');
const pptx = new PptxGenJS();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = 'Grupo 13';
pptx.subject = 'Arquitectura de Sistemas Operativos · Máquina virtual simple';
pptx.title = 'Defensa de la máquina virtual simple';
pptx.company = 'Grupo 13';
pptx.lang = 'es-NI';
pptx.theme = {headFontFace: 'Aptos Display', bodyFontFace: 'Aptos', lang: 'es-NI'};
const W = 13.333, H = 7.5;
const C = {navy:'10273B', teal:'166B70', ink:'172D40', muted:'526779', paper:'F7FAFC', line:'D9E2EA'};
const guide = fs.readFileSync(path.join(ROOT, 'docs/exposicion/GUIA_TRES_INTEGRANTES.md'), 'utf8');
const summary = JSON.parse(fs.readFileSync(path.join(ROOT, 'docs/evidencias/resumen.json'), 'utf8'));

function text(slide, value, x, y, w, h, opts={}) {
  slide.addText(value, {x,y,w,h,fontFace:'Aptos',fontSize:21,color:C.ink,
    margin:0,breakLine:false,paraSpaceAfterPt:9,valign:'mid',...opts});
}
function page(title, number, dark=false) {
  const slide=pptx.addSlide(); slide.background={color:dark?C.navy:C.paper};
  text(slide,title,.65,.38,12.0,.72,{fontFace:'Aptos Display',fontSize:32,bold:true,color:dark?'FFFFFF':C.ink});
  text(slide,'GRUPO 13  ·  ARQUITECTURA DE SISTEMAS OPERATIVOS',.67,7.12,10,.15,{fontSize:9,color:dark?'B9CDD8':C.muted});
  text(slide,String(number).padStart(2,'0'),12.13,7.08,.5,.2,{fontSize:10,align:'right',color:dark?'B9CDD8':C.muted});
  const pattern = new RegExp('### Diapositiva '+number+' [^\\n]+\\n([\\s\\S]*?)(?=\\n### Diapositiva |\\n## |$)');
  const notes=guide.match(pattern)?.[1]??'';
  const person=number<=5?1:number<=11?2:3;
  slide.addNotes(`Integrante ${person}.\n${notes.replace(/\*\*/g,'').trim()}\n\nFuentes: propuesta del grupo 13, páginas 2 a 9; docs/DOCUMENTO_TECNICO_GRUPO13.md; src/vm_studio/motor.py; docs/evidencias/resumen.json (${summary.fecha}). Capturas: implementación real de VM Studio. Ilustración conceptual de portada: generada con IA; no representa hardware del proyecto.`);
  return slide;
}
function table(slide, rows, widths, y=1.65, fontSize=20) {
  const cells=rows.map((row,i)=>row.map(cell=>({text:String(cell),options:{
    bold:i===0,color:i===0?'FFFFFF':C.ink,fill:i===0?C.navy:(i%2?'FFFFFF':'EDF3F6')
  }})));
  slide.addTable(cells,{x:.7,y,w:11.93,colW:widths,border:{type:'solid',pt:.6,color:C.line},
    fontFace:'Aptos',fontSize,color:C.ink,margin:[.14,.16,.14,.16],
    autoPage:false,breakLine:false,paraSpaceAfterPt:0,valign:'mid',rowH:.54,
    bold:false});
}
function image(slide, relative, x,y,w,h, crop=false) {
  const file=path.join(ROOT,relative);
  if(!fs.existsSync(file)) throw new Error('Imagen ausente: '+file);
  // Todos los recursos entregados son PNG. Conservar proporción explícitamente
  // evita que distintas versiones de Office interpreten el ajuste de otra forma.
  const bytes=fs.readFileSync(file), iw=bytes.readUInt32BE(16), ih=bytes.readUInt32BE(20);
  const scale=Math.min(w/iw,h/ih), fw=iw*scale, fh=ih*scale;
  slide.addImage({path:file,x:x+(w-fw)/2,y:y+(h-fh)/2,w:fw,h:fh,
    altText:relative.includes('conceptual')?'Ilustración conceptual de un procesador':'Captura real de VM Studio'});
}
function line(slide, value, y, opts={}) {text(slide,value,.72,y,11.85,.7,opts);}

// 1 Portada
{
 const s=page('Máquina virtual simple',1,true);
 image(s,'presentation/assets/procesador_conceptual.png',7.2,1.28,5.45,5.3,true);
 text(s,'VM STUDIO',.72,1.68,6.1,.9,{fontSize:46,bold:true,color:'FFFFFF'});
 text(s,'Memoria, registros y\nciclo de instrucciones',.75,2.92,6.1,1.22,{fontSize:29,color:'D4E7EF'});
 text(s,'Implementación didáctica en Python',.75,4.67,6,.55,{fontSize:21,color:'8EDCCF'});
 text(s,'Integrante 1 · Integrante 2 · Integrante 3',.75,5.65,6,.6,{fontSize:17,color:'E0EAF1'});
}
// 2 Problema y objetivo
{
 const s=page('Problema y objetivo',2);
 text(s,'Las instrucciones cambian el estado de la CPU,\npero esos cambios normalmente no son visibles.',.75,1.63,11.7,1.5,{fontSize:30,bold:true});
 text(s,'Objetivo del proyecto',.75,3.72,11.7,.45,{fontSize:23,bold:true,color:C.teal});
 text(s,'Interpretar programas pequeños y observar, después de cada instrucción,\ncómo cambian PC, IR, ACC y memoria.',.75,4.4,11.7,1.35,{fontSize:27});
}
// 3 Arquitectura
{
 const s=page('Arquitectura del simulador',3);
 table(s,[['Componente','Responsabilidad'],['Interfaz y consola','Cargar, ejecutar y mostrar el mismo estado'],['Unidad de control','Coordinar Fetch, Decode y Execute'],['Memoria y registros','Conservar instrucciones, datos y estado'],['Controladores','Adaptar teclado, archivos y salida'],['Reportes','Conservar una instantánea de la ejecución']],[3.55,8.38],1.55,22);
 line(s,'Un solo motor para las dos interfaces',6.08,{fontSize:25,bold:true,color:C.teal});
}
// 4 Memoria
{
 const s=page('Memoria e instrucciones',4);
 text(s,'100 celdas\ndirecciones 0–99',.8,1.65,3.65,1.35,{fontSize:35,bold:true,color:C.teal});
 text(s,'El código inicia en 0.\nDATA inicializa datos\nsin ocupar código.',.8,3.6,3.65,1.8,{fontSize:23});
 s.addTable([['Dirección','Contenido inicial','Tipo'],['0–4','LOAD, ADD, STORE, OUTPUT, HALT','Código'],['10','10','Dato'],['11','20','Dato'],['20','0 → 30 al ejecutar STORE','Dato']].map((r,i)=>r.map(t=>({text:t,options:{bold:i===0,color:i===0?'FFFFFF':C.ink,fill:i===0?C.navy:'FFFFFF'}}))),{x:4.8,y:1.62,w:7.65,colW:[1.55,4.55,1.55],fontFace:'Aptos',fontSize:19,border:{pt:.7,color:C.line},margin:.16,rowH:.7,autoPage:false});
}
// 5 Registros
{
 const s=page('Registros de la máquina',5);
 table(s,[['Registro','Función','Tras ADD 11'],['PC','Dirección de la próxima instrucción','2'],['IR','Última instrucción obtenida','ADD 11'],['ACC','Dato de trabajo y resultado','30'],['Z / N','ACC es cero / ACC es negativo','0 / 0']],[1.7,7.15,3.08],1.65,22);
 line(s,'PC es una dirección; IR es una instrucción; ACC es un dato.',6.0,{fontSize:24,color:C.teal});
}
// 6 Lenguaje
{
 const s=page('Lenguaje de instrucciones',6);
 table(s,[['Grupo','Instrucciones','Efecto'],['Transferencia','LOAD · STORE','Leer y escribir memoria'],['Aritmética','ADD · SUB','Modificar ACC'],['Control del flujo','JMP · JZ · JNZ','Cambiar PC'],['Entrada y salida','INPUT · OUTPUT','Leer y emitir enteros'],['Terminación','HALT','Detener la ejecución']],[3.15,4.35,4.43],1.55,21);
 line(s,'DATA dir valor es una directiva del cargador; no consume ciclos.',6.08,{fontSize:22,color:C.teal});
}
// 7 Ciclo
{
 const s=page('Ciclo Fetch Decode Execute',7);
 table(s,[['Fase','Operación','Ejemplo ADD 11'],['FETCH','Leer Mem[PC] y copiar a IR','IR = ADD 11'],['DECODE','Identificar opcode y operando','Operación ADD; dirección 11'],['EXECUTE','Aplicar el efecto de la operación','ACC = 10 + 20 = 30']],[2.05,5.9,3.98],1.8,22);
 text(s,'El PC se incrementa después de Decode y antes de Execute.\nUn salto puede reemplazar ese destino.',.75,5.2,11.8,1,{fontSize:24,color:C.teal});
}
// 8 Suma
{
 const s=page('Traza de la suma',8);
 table(s,[['Instrucción','PC final','ACC final','Mem[20]'],['LOAD 10','1','10','0'],['ADD 11','2','30','0'],['STORE 20','3','30','30'],['OUTPUT','4','30','30'],['HALT','5','30','30']],[5.0,2.2,2.3,2.43],1.55,22);
 line(s,'Datos iniciales: Mem[10] = 10 y Mem[11] = 20   ·   Salida: 30',6.08,{fontSize:22,color:C.teal});
}
// 9 Captura real
{
 const s=page('Demostración de la interfaz',9);
 image(s,'docs/evidencias/capturas/vm_suma.png',.78,1.3,11.78,5.55);
}
// 10 Saltos
{
 const s=page('Saltos y bucles',10);
 text(s,'JZ: salto condicional',.8,1.65,5.5,.65,{fontSize:27,bold:true,color:C.teal});
 text(s,'20 − 20 = 0\nZ = 1\nJZ 6 toma el salto\nSalida: 111',.8,2.62,5.45,2.72,{fontFace:'Consolas',fontSize:25,breakLine:false});
 text(s,'JNZ: repetición',7.05,1.65,5.5,.65,{fontSize:27,bold:true,color:C.teal});
 text(s,'Contador: 3, 2, 1, 0\nRepetir mientras Z = 0\nAcumular 3 + 2 + 1\nSalida: 6',7.05,2.62,5.5,2.72,{fontFace:'Consolas',fontSize:24});
 line(s,'Tener HALT en el archivo no garantiza alcanzarlo: el límite protege la ejecución.',6.05,{fontSize:22});
}
// 11 Dispositivos
{
 const s=page('Dispositivos virtuales',11);
 table(s,[['Controlador','Interacción','Resultado observable'],['Teclado','INPUT recibe un entero','ACC = 7'],['Disco','Leer y analizar un archivo ASM','Programa instalado en memoria'],['Impresora','OUTPUT emite ACC','Salida virtual: [7]']],[3.3,4.7,3.93],1.8,23);
 text(s,'Cancelar INPUT conserva la instrucción pendiente\ny permite reintentar sin sumar un ciclo.',.75,5.42,11.8,.95,{fontSize:25,color:C.teal});
}
// 12 Errores
{
 const s=page('Manejo de errores',12);
 image(s,'docs/evidencias/capturas/vm_error.png',.7,1.58,7.6,5.2);
 text(s,'Durante la carga',8.65,1.85,3.85,.5,{fontSize:24,bold:true,color:C.teal});
 text(s,'MULT 10\nCarga rechazada.\nSe conserva lo anterior.',8.65,2.55,3.85,1.45,{fontSize:21});
 text(s,'Durante la ejecución',8.65,4.25,3.9,.55,{fontSize:23,bold:true,color:C.teal});
 text(s,'LOAD 0 lee código\ncomo un número.\nERROR · PC = 0',8.65,4.98,3.9,1.45,{fontSize:21});
}
// 13 Reportes
{
 const s=page('Reportes de ejecución',13);
 image(s,'docs/evidencias/capturas/vm_reporte.png',.7,1.45,7.6,5.35);
 text(s,'HTML',8.65,1.85,3.9,.5,{fontSize:28,bold:true,color:C.teal});
 text(s,'Consultar e imprimir\nsin conexión',8.65,2.45,3.9,.8,{fontSize:22});
 text(s,'CSV',8.65,3.6,3.9,.5,{fontSize:28,bold:true,color:C.teal});
 text(s,'Revisar registros y\npasos en Excel',8.65,4.2,3.9,.8,{fontSize:22});
 text(s,'JSON',8.65,5.32,3.9,.5,{fontSize:28,bold:true,color:C.teal});
 text(s,'Conservar la evidencia\nestructurada completa',8.65,5.9,3.9,.8,{fontSize:22});
}
// 14 Resultados reales
{
 const s=page('Pruebas y resultados',14);
 table(s,[['Caso','Esperado y obtenido','Estado'],['Suma','ACC = 30; Mem[20] = 30','Correcto'],['Resta','ACC = 20; Mem[20] = 20','Correcto'],['Almacenamiento','Mem[20] = 30','Correcto'],['Condicional','Salida = 111','Correcto'],['Bucle','ACC = 6; Mem[53] = 6','Correcto'],['Entrada y salida','Entrada 7 → salida 7','Correcto']],[3.4,6.2,2.33],1.4,20);
 text(s,`${summary.pruebas_regresion} pruebas automatizadas correctas · 9 errores de carga comprobados · GUI verificada`,.75,6.48,11.85,.45,{fontSize:19,color:C.teal,bold:true});
}
// 15 Estructura
{
 const s=page('Organización del código',15);
 text(s,'src/vm_studio/\n  motor.py\n  interfaz.py\n  consola.py\n  reportes.py',.85,1.66,5.8,3.45,{fontFace:'Consolas',fontSize:27});
 text(s,'Motor: instrucciones y estado\nInterfaz: interacción visual\nConsola: terminal y archivos\nReportes: exportación de evidencia',7.0,1.85,5.5,2.9,{fontSize:24});
 text(s,'examples/     tests/     docs/     output/',.85,5.63,11.7,.65,{fontFace:'Consolas',fontSize:24,color:C.teal});
}
// 16 Cierre
{
 const s=page('Conclusiones y límites',16,true);
 text(s,'Cada resultado conserva\nel recorrido que lo explica.',.8,1.65,11.7,1.55,{fontSize:38,bold:true,color:'FFFFFF'});
 text(s,'Memoria y registros observables\nEjecución por pasos y automática\nPruebas reproducibles y reportes',.85,3.62,11.6,1.7,{fontSize:27,color:'A9E5D9'});
 text(s,'Alcance didáctico: 100 celdas y 10 instrucciones.\nNo simula concurrencia, interrupciones ni una CPU física.',.85,5.72,11.6,.9,{fontSize:21,color:'D6E3EC'});
}
const destination=path.join(ROOT,'output/presentacion/DEFENSA_GRUPO13.pptx');
fs.mkdirSync(path.dirname(destination),{recursive:true});
await pptx.writeFile({fileName:destination});
// El exportador 4.0.1 declara masters que no genera. Eliminar únicamente esas
// declaraciones huérfanas mantiene el paquete OOXML coherente con sus partes.
const JSZip=require('jszip');
const archive=await JSZip.loadAsync(fs.readFileSync(destination));
const types=await archive.file('[Content_Types].xml').async('string');
archive.file('[Content_Types].xml', types.replace(/<Override\b[^>]*\/>/g, entry => {
  const part=entry.match(/PartName="([^"]+)"/);
  return part && !archive.file(part[1].replace(/^\//,'')) ? '' : entry;
}));
// Las tablas de este exportador pueden reutilizar el identificador de una caja
// de texto previa. No hay conectores ni animaciones: renumerar las formas locales
// evita colisiones sin cambiar contenido, posición ni edición de las tablas.
for (const [name, part] of Object.entries(archive.files)) {
  if (/^ppt\/slides\/slide\d+\.xml$/.test(name)) {
    let id=0;
    const xml=await part.async('string');
    archive.file(name,xml.replace(/<p:cNvPr\b[^>]*>/g, tag => tag.replace(/\bid="\d+"/, `id="${++id}"`)));
  }
}
fs.writeFileSync(destination,await archive.generateAsync({type:'nodebuffer',compression:'DEFLATE'}));
if (process.platform==='win32') {
  const native=spawnSync('powershell.exe',['-NoProfile','-ExecutionPolicy','Bypass','-File',
    path.join(ROOT,'scripts/normalizar_presentacion_windows.ps1'),'-Presentacion',destination],{encoding:'utf8',windowsHide:true});
  if (native.status!==0) throw new Error('No se pudo normalizar el PowerPoint: '+native.stderr);
}
console.log(destination);
