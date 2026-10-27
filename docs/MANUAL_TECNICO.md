# Manual técnico — máquina virtual simple

**Fecha de revisión:** 26 de octubre de 2026.

## Entorno y alcance

La aplicación requiere Python 3.10 o superior. Su motor, consola y GUI utilizan la biblioteca estándar; la interfaz gráfica necesita que Python incluya Tkinter. El proyecto conserva Python según autorización consignada por el grupo. La propuesta también contiene referencias a Java; la autorización se registra como antecedente del grupo, sin afirmar una verificación externa.

ReportLab es una dependencia opcional para generar el documento PDF. La generación Word utiliza python-docx y pypdfium2 para las imágenes del documento. No se necesitan estos paquetes para ejecutar la máquina virtual, sus reportes ni sus pruebas del motor.

## Estructura del proyecto

```text
simulador_vm.py                  Punto de entrada
src/
  vm_studio/
    __main__.py                  Entrada como módulo
    simulador_vm.py              API pública compatible
    motor.py                     Memoria, CPU y controladores
    interfaz.py                  Interfaz Tkinter y planificación
    consola.py                   Menú y argumentos de terminal
    reportes.py                  Instantáneas y exportación de reportes
examples/
  test1_suma.asm                 Suma con datos iniciales
  test2_resta.asm                Resta
  test3_almacenamiento.asm       STORE y lectura posterior
  test4_condicional.asm          Salto JZ
  test5_bucle.asm                Bucle JNZ
  test6_entrada_salida.asm       INPUT y OUTPUT
  multiplicacion.asm            Ejemplo adicional por sumas sucesivas
tests/
  verificar_entrega.py           Verificación funcional de entrega
  test_regresiones.py            Pruebas de regresión del motor
  test_consola.py                Flujos de terminal y ejecución por archivo
  test_reportes.py               Exportación, integridad y formatos
  verificar_gui.py              Comprobaciones de controles Tkinter
scripts/
  generar_evidencias.py          Resultados y evidencias reproducibles
  generar_documento.py           Documento PDF con diagramas dibujados
  generar_word.py                Documento técnico y guion editables
  preparar_entrega.py            Paquete seleccionado para compartir
  requirements_documento.txt     Dependencia de generación del PDF
docs/
  DOCUMENTO_TECNICO_GRUPO13.md    Diseño y seis programas completos
  MANUAL_USUARIO.md              Uso de la aplicación
  MANUAL_TECNICO.md              Este documento
  EVIDENCIAS_PRUEBAS.md           Resultados obtenidos
  GUIA_DEFENSA.md                Exposición y demostración
  README_ENTREGA.md              Contenido de la entrega
  evidencias/                   Exportaciones JSON y resultados
  exposicion/                   Guion para tres integrantes y recursos
output/
  pdf/
    ENTREGA_GRUPO13.pdf          Versión preparada para imprimir
  word/                         Documento técnico editable
  exposicion/                   Guía editable para tres integrantes
  presentacion/                 Diapositivas editables con imágenes
  reportes/                     Ejemplos de reportes HTML, CSV y JSON
  compartir/                    ZIP de la entrega
```

La implementación oficial se encuentra en `src/vm_studio/`. El archivo `simulador_vm.py` de la raíz funciona como entrada a ese módulo. El material histórico de `archive/` no es la versión de entrega.

## Modelo de datos

`Instruction` representa una operación mediante `opcode` en mayúsculas y `operand` opcional. Su representación textual conserva una forma como `LOAD 10` o `HALT`.

`Program` amplía una lista de instrucciones y añade `initial_data`, un diccionario que recoge las declaraciones DATA, y `source`, el texto original. Una declaración no se inserta en la lista de instrucciones y no cambia sus direcciones. `Instruction.validate()` comprueba opcode, cantidad y tipo de operandos antes de cargar o ejecutar una instrucción.

`Memory` conserva 100 celdas inicializadas a cero. Sus operaciones son `read(address)`, `read_int(address)`, `write(address, value)`, `_check_bounds(address)` y `clear()`. `read_int()` rechaza instrucciones; `_check_bounds()` exige un entero de 0 a 99 y rechaza tipos como booleanos, decimales y texto. La escritura admite enteros o instrucciones válidas. STORE puede modificar código, por lo que ejecutar después una celda sobrescrita con un entero produce un error de Fetch. La edición manual de la interfaz utiliza `edit_data()` y no permite escribir sobre código.

## Controladores

`DeviceControllers` ofrece las funciones compartidas de entrada, salida, lectura de archivos y análisis del texto. `KeyboardController.read`, `PrinterController.write` y `DiskController.load` exponen los controladores específicos.

El teclado recibe un entero; en consola solicita otra entrada cuando el texto no representa un entero. En GUI se usa un diálogo. Cancelar el diálogo genera `InputCancelled` y permite repetir la instrucción.

El disco lee archivos con codificación `utf-8-sig`, compatible con UTF-8 con o sin marca inicial. `DiskController.read_source()` obtiene el texto para abrirlo en el editor; `DiskController.load()` lo analiza para cargar el motor. La impresora entrega mensajes a la consola o al manejador de salida de la GUI. No se comunica con una impresora física.

## Máquina virtual

`VirtualMachine`, en `motor.py`, conserva `memory`, `pc`, `ir`, `acc`, `flag_z`, `flag_n`, `halted`, `error`, `cycles`, `execution_log` y `last_trace`. También conserva `program_source`, `program_name`, `initial_data`, `input_values`, `outputs`, `history` y `manual_edits`. Puede recibir `input_handler` y `output_handler` para desacoplar el motor de los dispositivos de una interfaz concreta.

| Método | Responsabilidad |
|---|---|
| `reset()` | Vaciar memoria, traza y estado; volver a PC = 0, ACC = 0, Z = 1 y N = 0. |
| `restart()` | Restaurar el código y los datos iniciales del programa cargado; limpiar su ejecución. |
| `edit_data(address, value)` | Editar un entero fuera del código y registrar su cambio; antes del primer paso lo incorpora a los datos iniciales. |
| `load_program(filepath)` | Leer un archivo mediante el controlador de disco y cargarlo. |
| `load_source(source, name)` | Analizar y cargar un texto ASM. |
| `load_instructions(instructions, filepath)` | Validar programa y datos iniciales antes de sustituir el estado anterior. |
| `step()` | Completar un ciclo Fetch-Decode-Execute y registrar su explicación. |
| `_execute(instruction, original_pc)` | Aplicar el efecto del opcode. |
| `_update_flags()` | Calcular Z y N a partir de ACC. |
| `run_all(max_cycles=10000)` | Repetir pasos hasta HALT o un fallo, limitando el total desde carga o reinicio. |
| `get_state_summary()` | Devolver registros, banderas, detención, error y ciclos. |
| `print_state()` | Mostrar el estado y el diagnóstico de error en consola. |

## Carga y validación

El analizador elimina comentarios `#` y `//`, separa tokens y normaliza el opcode. Comprueba que cada instrucción reciba exactamente los operandos previstos y que sus direcciones sean enteros válidos. Una entrada como `LOAD ACC` genera un diagnóstico específico: ACC se utiliza implícitamente y LOAD necesita una dirección de memoria.

`DATA dirección valor` requiere dos enteros. Se rechazan direcciones fuera de rango, duplicadas o superpuestas con las direcciones del código inicial. El cargador también rechaza programas vacíos, más de 100 instrucciones y ausencia de HALT.

La validación ocurre antes de `reset()`. Por ello, un archivo, texto o lista de instrucciones rechazados conservan el programa anterior, sus registros, memoria e historial. Las instrucciones cargadas se copian para que modificar después los objetos del llamador no altere el programa. Tener HALT es una condición del lenguaje, pero no demuestra que el flujo alcance esa instrucción.

## Ciclo interno y errores

1. `step()` rechaza continuar si `error` está activo y devuelve sin ejecutar si ya hubo HALT.
2. Guarda PC, IR y ACC anteriores para la ejecución y su explicación.
3. Fetch lee Mem[PC], comprueba su tipo y copia la instrucción a IR.
4. Decode registra opcode y operando.
5. Prepara PC = PC + 1, después de Decode y antes de Execute.
6. `_execute()` modifica ACC, memoria, PC, dispositivos o detención.
7. Actualiza FLAGS y suma un ciclo completado.
8. Registra explicación, Fetch, Decode y Execute en la traza, y agrega el registro de la instrucción completada a `history`.

Un error de ejecución devuelve PC a la dirección fallida, conserva el diagnóstico en `error` y no suma un ciclo. Las ejecuciones siguientes generan `ExecutionFault` hasta reiniciar o cargar un programa válido. `halted` representa terminación por HALT; un fallo no se convierte en una terminación normal.

Si se cancela INPUT, se restauran PC e IR anteriores y se permite reintentar. ACC y los ciclos no cambian. Las tarjetas pueden indicar la cancelación, pero la máquina no queda bloqueada por un fallo permanente.

El motor, la consola y la GUI aplican el límite al total de ciclos completados desde la carga o reinicio, incluyendo pasos manuales. Reanudar no vuelve a conceder el límite completo. Alcanzar HALT en el último ciclo permitido termina correctamente. Sin programa cargado, `step()` informa la situación sin dejar un error permanente.

Cada elemento de `history` contiene ciclo, instrucción, PC y ACC antes/después, Z/N, cambios de memoria, fases y explicación. Solo se agregan instrucciones completadas; una cancelación o un fallo no inventa pasos, entradas o salidas. `outputs` e `input_values` recogen la salida y entrada confirmadas. `manual_edits` distingue cambios hechos por el usuario de las escrituras de STORE.

## Operaciones de la arquitectura

| Sintaxis | Efecto |
|---|---|
| `LOAD dir` | ACC = Mem[dir] |
| `STORE dir` | Mem[dir] = ACC |
| `ADD dir` | ACC = ACC + Mem[dir] |
| `SUB dir` | ACC = ACC - Mem[dir] |
| `JMP dir` | PC = dir |
| `JZ dir` | PC = dir si Z = 1 |
| `JNZ dir` | PC = dir si Z = 0 |
| `INPUT` | ACC = entero leído |
| `OUTPUT` | Emitir ACC |
| `HALT` | halted = True |

Las direcciones válidas son 0 a 99. No se implementan etiquetas ni valores inmediatos en instrucciones. Los enteros utilizan la representación de Python y no un ancho de palabra fijo.

## Interfaces y reinicio

`run_gui()` construye la ventana Tkinter y programa instrucciones con `after()`. Pausar cancela la próxima ejecución programada. Editor, memoria, tarjetas, traza e impresora se actualizan desde el mismo motor. La velocidad representa milisegundos entre instrucciones completas.

La GUI conserva el texto y los datos iniciales del programa cargado. Su botón Reiniciar vuelve a cargar esa fuente. Una edición de datos antes del primer paso pasa a formar parte de los datos que restaura; una edición posterior solo afecta a la ejecución actual. El código se modifica desde el editor, seguido de Cargar desde editor.

`run_cli()`, en `consola.py`, ofrece carga, paso, ejecución automática, registros, volcado, edición de datos y exportación. La opción Reiniciar llama a `restart()` y restaura el programa y sus datos iniciales, igual que el reinicio de GUI. `reset()` queda reservado al vaciado interno. El diagnóstico de ERROR se muestra también al consultar registros después de un fallo. EOF y Ctrl+C terminan el menú sin un traceback.

`main(argv=None)` valida los argumentos con argparse. Sin opciones abre la GUI; `--cli` abre el menú. El modo `--archivo RUTA` ejecuta sin interacción y recibe un `--entrada ENTERO` por cada INPUT. Si faltan valores, registra un error en lugar de esperar teclado. `--max-ciclos` controla el total y `--reporte RUTA` permite exportar incluso el estado de error. Devuelve 0 al completar correctamente y 1 ante fallo de carga, ejecución o guardado; argparse rechaza las combinaciones inválidas con código 2.

```powershell
python simulador_vm.py --archivo examples/test6_entrada_salida.asm --entrada 7 --reporte output/reportes/entrada.html
```

## Reportes de ejecución

`reportes.build_evidence()` crea una copia independiente del estado actual. El reporte no cambia si la VM continúa después. Incluye código, nombre, fecha, datos iniciales, registros, memoria completa, entrada, salida, historial, ediciones manuales, últimas fases y estadísticas de operaciones y saltos. Diferencia ERROR, SIN PROGRAMA, LISTA, PAUSADA y FINALIZADA; el estado exportado no equivale por sí mismo a una aprobación de la prueba.

`save_report()` selecciona formato por extensión. HTML es autónomo e imprimible, con textos escapados para que el programa ASM no se interprete como contenido activo. CSV utiliza separador de punto y coma, cabecera uniforme y UTF-8 con marca inicial para Excel; sus filas identifican programa, registros, pasos, escrituras, memoria, entradas, salidas y ediciones. Los textos que podrían convertirse en fórmulas se neutralizan. JSON conserva la instantánea estructurada completa. El guardado escribe primero un temporal y reemplaza el destino al completarse, evitando truncarlo ante una falla previa.

## Evidencias y verificaciones

Desde la raíz del proyecto:

```powershell
python -m tests.verificar_entrega
python -m unittest discover -s tests -v
python -m tests.verificar_gui
python scripts/generar_evidencias.py --incluir-gui
```

La verificación de GUI necesita un escritorio disponible. El generador sin `--incluir-gui` evita abrir ventanas e identifica qué verificaciones ejecutó. Los resultados reales quedan en `docs/EVIDENCIAS_PRUEBAS.md` y en `docs/evidencias/`; deben revisarse después de cada regeneración.

Las interfaces de GUI, consola y archivo utilizan el mismo módulo de reportes. La traza y `history` permiten seguir todas las instrucciones; el campo de últimas fases solo describe la última. El generador de evidencias ejecuta los ejemplos y las pruebas; el informe generado indica qué se comprobó y sus resultados sin fijar un conteo estático en este manual.

## Generación del documento imprimible

```powershell
python -m pip install -r scripts/requirements_documento.txt
python scripts/generar_documento.py
python -m pip install python-docx pypdfium2
python scripts/generar_word.py
python scripts/preparar_entrega.py
```

El PDF se guarda en `output/pdf/ENTREGA_GRUPO13.pdf` y el Word en `output/word/ENTREGA_GRUPO13.docx`. La guía para tres integrantes está en `output/exposicion/GUIA_TRES_INTEGRANTES.docx`; el PowerPoint está en `output/presentacion/DEFENSA_GRUPO13.pptx`. Las fuentes Markdown permanecen editables. Antes de entregar deben completarse los datos de portada y volver a generar los documentos.

El empaquetado produce `output/compartir/VM_STUDIO_GRUPO13.zip` con código y materiales seleccionados. Excluye cachés, temporales, material histórico y metadatos de Git; no incluye el ZIP dentro de sí mismo. Los compañeros deben descomprimir la carpeta completa para conservar las rutas de los ejemplos.

## Recomendaciones de mantenimiento

- Cambiar el conjunto de instrucciones junto con el analizador, su ejecución, documentación y verificaciones pertinentes.
- Preservar la validación de carga antes de sustituir la memoria activa.
- Regenerar evidencias cuando cambie una semántica o un programa de ejemplo.
- Comprobar la GUI en el equipo de defensa, además de ejecutar las verificaciones automatizadas.
- Mantener el material histórico fuera de la ruta oficial de ejecución.
