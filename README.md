# VM Studio — Máquina virtual simple del grupo 13

Proyecto de Arquitectura de Sistemas Operativos. Simula una memoria de 100 celdas, los registros PC, IR y ACC, las banderas Z/N y el ciclo Fetch → Decode → Execute. Incluye escritorio Tkinter, consola, ejecución de archivos ASM y reportes HTML, CSV y JSON.

El proyecto conserva Python según autorización consignada por el grupo. La propuesta enumera Python y también contiene indicaciones de Java; debe conservarse el respaldo real de la decisión del docente.

## Comenzar

Requiere Python 3.10 o superior con Tkinter. La aplicación y los reportes utilizan la biblioteca estándar y no necesitan internet ni paquetes adicionales. Desde esta carpeta:

```powershell
python simulador_vm.py
```

En Windows se puede sustituir `python` por `py`. `python -m tkinter` comprueba la instalación gráfica. El menú de consola se abre con:

```powershell
python simulador_vm.py --cli
```

## Descargar y compartir con el grupo

- [Descargar el proyecto completo con código y materiales](https://github.com/Josebucardo/simulador-maquina-virtual/raw/refs/heads/main/output/compartir/VM_STUDIO_GRUPO13.zip).
- [Manual de usuario en PDF](output/manual/MANUAL_USUARIO_VM_STUDIO.pdf) y [Word editable](output/manual/MANUAL_USUARIO_VM_STUDIO.docx).
- [Diapositivas PowerPoint](output/presentacion/DEFENSA_GRUPO13.pptx) y [guion de los tres integrantes](output/exposicion/GUIA_TRES_INTEGRANTES.docx).

Para trabajar con Git:

```powershell
git clone https://github.com/Josebucardo/simulador-maquina-virtual.git
cd simulador-maquina-virtual
python simulador_vm.py
```

Si descargaste el ZIP, primero extrae la carpeta completa. Conserva juntos el punto de entrada, `src/` y `examples/`. Los documentos y las diapositivas ya están generados; no necesitas instalar sus herramientas para abrirlos.

## Preparar la exposición de tres integrantes

Abrir el PowerPoint, repartir los guiones y ensayar una exposición completa de 15 a 20 minutos. Los integrantes deben comprender el ciclo y los errores, aunque cada uno conduzca una parte distinta.

| Material | Ubicación |
|---|---|
| Diapositivas editables con imágenes | `output/presentacion/DEFENSA_GRUPO13.pptx` |
| Guion editable para tres integrantes | `output/exposicion/GUIA_TRES_INTEGRANTES.docx` |
| Fuente del guion | `docs/exposicion/GUIA_TRES_INTEGRANTES.md` |
| Documento técnico editable | `output/word/ENTREGA_GRUPO13.docx` |
| Documento técnico para imprimir | `output/pdf/ENTREGA_GRUPO13.pdf` |
| Manual de usuario independiente | `output/manual/MANUAL_USUARIO_VM_STUDIO.docx` y `.pdf` |
| Reporte de suma para mostrar | `output/reportes/suma.html` |
| Paquete para compartir | `output/compartir/VM_STUDIO_GRUPO13.zip` |

La portada mantiene campos para completar institución, integrantes, docente y fecha de entrega. La fecha de revisión del material no sustituye la fecha de entrega.

Distribución: integrante 1 presenta el problema, la arquitectura y los registros (diapositivas 1 a 5); integrante 2 explica el lenguaje, demuestra el ciclo, los saltos y los dispositivos (6 a 11); integrante 3 explica errores, reportes, pruebas y conclusiones (12 a 16). El guion contiene los tiempos, transiciones y preguntas de defensa.

## Probar antes de presentar

```powershell
python -m tests.verificar_entrega
python -m unittest discover -s tests -v
python -m tests.verificar_gui
python scripts/generar_evidencias.py --incluir-gui
```

La última ejecución actualiza `docs/EVIDENCIAS_PRUEBAS.md` y `docs/evidencias/` con resultados reales. Las verificaciones de Tkinter abren ventanas brevemente y necesitan un escritorio. Sin `--incluir-gui`, el informe identifica que esa comprobación no fue ejecutada. Los resultados corresponden al código y equipo comprobados; también se debe ensayar la aplicación en la resolución del proyector.

## Demostración rápida

En la aplicación, cargar Suma y ejecutar cinco pasos con F7. Mostrar ACC = 30, Mem[20] = 30 y salida 30. F5 ejecuta automáticamente; F6 pausa. Reiniciar restaura programa y datos iniciales. El límite corresponde al total de ciclos desde carga o reinicio, incluyendo pasos manuales.

```asm
DATA 10 10
DATA 11 20
LOAD 10
ADD 11
STORE 20
OUTPUT
HALT
```

DATA declara enteros sin consumir direcciones de código. Los destinos de salto cuentan instrucciones ejecutables, no líneas del archivo. Las diez instrucciones son LOAD, STORE, ADD, SUB, JMP, JZ, JNZ, INPUT, OUTPUT y HALT. Un paso completa las tres fases de una instrucción; las tarjetas no son controles para detenerse entre fases.

## Ejecutar y generar reportes sin diálogos

```powershell
python simulador_vm.py --archivo examples/test1_suma.asm --reporte output/reportes/suma.html
python simulador_vm.py --archivo examples/test6_entrada_salida.asm --entrada 7 --reporte output/reportes/entrada.csv
python simulador_vm.py --archivo examples/multiplicacion.asm --entrada -4 --entrada 3 --reporte output/reportes/multiplicacion.json
```

Se repite `--entrada ENTERO` por cada INPUT. Si faltan entradas, el comando termina con error y puede conservar el diagnóstico en el reporte; no abre un diálogo ni espera teclado. `--max-ciclos 10000` establece el límite total. Un resultado correcto devuelve código 0; una falla de carga, ejecución o guardado devuelve 1. `--help` muestra las opciones.

HTML se abre en un navegador y puede imprimirse; CSV se abre en Excel y organiza registros por tipo; JSON conserva la instantánea completa. Los reportes distinguen LISTA, PAUSADA, FINALIZADA y ERROR: una exportación pausada no es una aprobación de la prueba.

## Estructura del código

```text
simulador_vm.py                 Entrada habitual
src/vm_studio/
  __main__.py                  Entrada como módulo
  simulador_vm.py              API pública compatible
  motor.py                     Memoria, instrucciones, CPU y controladores
  interfaz.py                  Escritorio Tkinter
  consola.py                   Menú y argumentos de terminal
  reportes.py                  Instantáneas y exportación HTML/CSV/JSON
examples/                      Seis pruebas y multiplicación adicional
tests/                         Motor, consola, reportes y controles GUI
scripts/                       Generación de evidencias y documentos; empaquetado
docs/                          Diseño, manuales, guiones y evidencias
output/                        Documentos, diapositivas, reportes y ZIP para compartir
```

Cada interfaz utiliza el mismo motor. `reset()` vacía el motor; `restart()` restaura el programa cargado y es la operación de los controles de reinicio. El historial contiene las instrucciones completadas y sus cambios de PC, ACC, banderas y memoria. Las entradas canceladas y los errores no generan pasos ficticios. La lectura de archivos pasa por el controlador de disco.

`archive/` y `ASO/` conservan material histórico local y quedan fuera del paquete de entrega. Los temporales y las cachés tampoco se incluyen.

## Regenerar documentos y paquete

La aplicación sigue sin dependencias externas. Solo las herramientas de documentos necesitan paquetes adicionales:

```powershell
python -m pip install -r scripts/requirements_documento.txt
python -m pip install python-docx pypdfium2
python scripts/generar_documento.py
python scripts/generar_word.py
python scripts/preparar_entrega.py
```

La generación PDF usa ReportLab; Word usa python-docx y las herramientas de imágenes indicadas. Las fuentes editables del diseño y de los manuales permanecen en `docs/`. Regenerar los artefactos después de cambiar la portada, el código o las evidencias.

El manual independiente también está disponible en `output/manual/`. En Windows se puede iniciar la aplicación con doble clic en `INICIAR_VM.cmd` y comprobarla con `VERIFICAR_PROYECTO.cmd`.

Para regenerar únicamente las diapositivas, se necesita Node.js y Microsoft PowerPoint en Windows:

```powershell
npm ci --prefix presentation
node scripts/generar_presentacion.mjs
```

Estas herramientas no son necesarias para abrir el PowerPoint ya entregado ni para ejecutar la aplicación.

El ZIP de `output/compartir/` reúne la versión seleccionada del código y los materiales finales. Para compartirlo, adjuntar ese archivo o el Word/PowerPoint específico en el servicio habitual. Los compañeros deben descomprimir todo el proyecto antes de ejecutar el simulador.

## Alcance del modelo

Es una máquina virtual didáctica: no implementa procesos concurrentes, interrupciones, caché ni ancho de palabra fijo. El programa adicional de multiplicación usa sumas sucesivas y exige que el segundo entero sea no negativo; uno negativo provoca un bucle detenido por el límite. No forma parte de las diez instrucciones de CPU.
