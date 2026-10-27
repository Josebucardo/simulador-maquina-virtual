# Guía de defensa del proyecto

**Fecha de revisión:** 26 de octubre de 2026.

## Duración y distribución

La defensa se prepara para 15 a 20 minutos. El recorrido base dura aproximadamente 18 minutos. La versión de ensayo con guiones individuales está en `docs/exposicion/GUIA_TRES_INTEGRANTES.md` y `output/exposicion/GUIA_TRES_INTEGRANTES.docx`. Utilizar `output/presentacion/DEFENSA_GRUPO13.pptx` como apoyo visual y completar los nombres reales.

| Tiempo | Responsable | Contenido y demostración |
|---|---|---|
| 0:00 a 5:30 | Integrante 1 | Diapositivas 1 a 5: problema, objetivo, arquitectura, memoria y registros. |
| 5:30 a 12:00 | Integrante 2 | Diapositivas 6 a 11: instrucciones, ciclo, suma y demostración, saltos y dispositivos. |
| 12:00 a 18:00 | Integrante 3 | Diapositivas 12 a 16: errores, reportes, pruebas, organización y conclusiones. |

Distribuir las intervenciones entre los integrantes reales antes de ensayar. Cada integrante debe poder explicar el programa, los saltos y el estado de error, aunque tenga asignada una sección distinta.

## Preparación individual

**Integrante 1:** debe explicar por qué el proyecto permite observar la ejecución y distinguir simulación de procesador de sistema operativo completo. Mostrar `src/vm_studio/`: `motor.py` resuelve la arquitectura, `interfaz.py` presenta Tkinter, `consola.py` recibe comandos y `reportes.py` conserva evidencia. Evitar leer todo el código durante la exposición. Transición sugerida: «Con los componentes identificados, ahora veremos cómo un programa usa esas reglas».

**Integrante 2:** debe conocer las direcciones de la suma, los valores iniciales y cada cambio de PC, IR y ACC. Ejecutar cinco instrucciones con F7 y señalar la celda 20 después de STORE. Explicar que DATA no es una instrucción ejecutada, y que ADD 11 usa el contenido de la dirección 11. Después presenta JZ, el bucle JNZ y los controladores. Transición sugerida: «Ahora mi compañero mostrará cómo controlamos los errores y conservamos las evidencias».

**Integrante 3:** debe preparar un error de carga y un error de ejecución, explicar su recuperación y mostrar un reporte HTML. Relaciona el reporte con el estado observado, presenta las pruebas y la organización del código, y cierra con las limitaciones reales. No debe afirmar que las pruebas eliminan cualquier falla posible.

## Preparación del equipo

Desde la raíz del proyecto, comprobar antes de la exposición:

```powershell
python -m tests.verificar_entrega
python -m unittest discover -s tests -v
python -m tests.verificar_gui
python scripts/generar_evidencias.py --incluir-gui
python simulador_vm.py
```

Revisar el informe de resultados realmente obtenido en `docs/EVIDENCIAS_PRUEBAS.md`. Comprobar el tamaño de la ventana, la legibilidad y la disponibilidad de los archivos en la computadora que se utilizará. Dejar preparado `output/pdf/ENTREGA_GRUPO13.pdf` y completar la portada con los datos reales.

Generar o conservar un reporte de respaldo:

```powershell
python simulador_vm.py --archivo examples/test1_suma.asm --reporte output/reportes/suma.html
```

La aplicación y sus reportes no necesitan conexión. Abrir el PowerPoint y el reporte antes de empezar, y ensayar el cambio entre ventanas. Las pruebas deben ejecutarse antes de la exposición; durante ella basta con mostrar sus resultados y, si se solicita, ejecutar el verificador funcional.

## Explicación de la arquitectura

La memoria tiene 100 celdas y contiene instrucciones y datos. PC indica dónde buscar la próxima instrucción. IR conserva la instrucción obtenida. ACC guarda los valores con los que se trabaja. La unidad de control coordina la búsqueda, interpretación y ejecución. Z indica si ACC es cero y N si es negativo.

El disco lee programas ASM, el teclado entrega enteros a INPUT y la impresora virtual muestra lo emitido por OUTPUT. La GUI y la consola utilizan el mismo motor.

El código está separado por responsabilidad. Los cambios visibles proceden de la misma instancia de `VirtualMachine`; no existen cálculos diferentes para consola y escritorio. Los reportes toman una instantánea del motor con sus pasos confirmados.

El proyecto conserva Python según autorización consignada por el grupo. La propuesta incluye referencias a Python y también indicaciones de Java. Si se consulta durante la defensa, presentar la constancia real que tenga el grupo; los archivos del proyecto no verifican por sí solos esa autorización.

## Demostración de suma por pasos

Cargar `examples/test1_suma.asm` o el siguiente código completo:

```asm
DATA 10 10
DATA 11 20
LOAD 10
ADD 11
STORE 20
OUTPUT
HALT
```

Antes de empezar, mostrar PC = 0, ACC = 0 y Z = 1. Explicar que DATA instala datos sin ocupar posiciones de código. Las instrucciones ocupan las direcciones 0 a 4.

| Paso | Explicación | Resultado visible |
|---|---|---|
| LOAD 10 | Fetch obtiene LOAD 10; Decode reconoce una carga; Execute copia el dato 10. | PC = 1, IR = LOAD 10, ACC = 10. |
| ADD 11 | Lee 20 de memoria y calcula 10 + 20. | PC = 2, ACC = 30. |
| STORE 20 | Guarda 30 en la celda 20 sin cambiar ACC. | PC = 3, Mem[20] = 30. |
| OUTPUT | Envía el acumulador a la impresora virtual. | PC = 4, salida 30. |
| HALT | Finaliza la ejecución. | PC = 5, IR = HALT, cinco ciclos. |

El PC aumenta después de Decode y antes de Execute. En un salto, Execute puede reemplazar ese valor. Las tarjetas muestran las fases de la última instrucción completa y la traza conserva las anteriores. F7 ejecuta toda la instrucción.

## Saltos, bucle y dispositivos

Cargar `examples/test4_condicional.asm`. Explicar que 20 - 20 deja ACC en cero; JZ salta a la instrucción de dirección 6 e imprime 111. Las declaraciones y comentarios no cuentan para esa dirección.

Cargar `examples/test5_bucle.asm` y ejecutar automáticamente. Mostrar que el contador disminuye y que JNZ repite mientras no sea cero. El resultado es 3 + 2 + 1 = 6.

Cargar `examples/test6_entrada_salida.asm`, introducir 7 y comprobar memoria e impresora. Si hay tiempo, cancelar una solicitud de INPUT y reintentar para mostrar que no se cuenta una instrucción incompleta.

## Error controlado

En el editor, intentar cargar:

```asm
MULT 10
HALT
```

El cargador debe rechazar MULT sin reemplazar el programa previo. Para distinguir un error durante la ejecución, utilizar después:

```asm
LOAD 0
HALT
```

El archivo es sintácticamente válido, pero la celda 0 contiene código. Al ejecutar LOAD, el motor informa que se intentó leer una instrucción como dato. Mostrar el diagnóstico, el PC conservado en 0 y la necesidad de reiniciar o cargar otro programa válido. En consola la consulta de registros también muestra ERROR y su causa.

## Evidencias y resultados

Mostrar la tabla de resultados esperados y obtenidos en `docs/EVIDENCIAS_PRUEBAS.md`, una evidencia JSON y la traza numérica de la suma. Señalar el código, los datos iniciales, PC, IR, ACC, memoria, salida y diagnóstico si corresponde.

En el reporte HTML mostrar primero el estado y los registros; después una fila del historial donde STORE modifica Mem[20]. Explicar que CSV sirve para revisar registros en Excel y JSON conserva datos estructurados. Exportar durante una pausa o un error mantiene esa condición; no se presenta como una ejecución aprobada.

Para una presentación fluida, mostrar los archivos ya generados y ejecutar el verificador funcional por separado. El generador sustituye el informe con los resultados de esa ejecución; si se vuelve a generar sin `--incluir-gui`, esa ejecución no incluye las comprobaciones de ventanas.

## Preguntas probables

**¿Para qué sirve PC?** Indica la dirección de la próxima instrucción. Los saltos permiten sustituir la continuación secuencial.

**¿Para qué sirve IR?** Conserva la instrucción obtenida en Fetch, incluso después de completarla, hasta que se obtenga otra.

**¿Por qué se usa ACC?** Simplifica la arquitectura: las cargas, sumas, restas, entradas y salidas trabajan sobre un registro principal.

**¿Cuándo se activa Z?** Después de una instrucción completada, si ACC es cero. Inicialmente también está activa porque ACC empieza en cero.

**¿DATA es una instrucción de CPU?** No. Es una directiva del cargador para establecer datos iniciales; no ocupa dirección de código ni consume ciclos.

**¿Por qué LOAD ACC produce error?** El acumulador es implícito. LOAD necesita la dirección de la celda que contiene el dato; por ejemplo, LOAD 10.

**¿Tener HALT impide un bucle infinito?** No. La carga exige HALT, pero un salto puede impedir alcanzarlo. El límite de ciclos detecta esa situación durante la ejecución.

**¿Qué ocurre cuando se cancela INPUT?** La instrucción queda pendiente, los registros anteriores se conservan y puede reintentarse.

**¿Qué representa un estado ERROR?** Una instrucción falló; el diagnóstico se conserva y no se permiten nuevos pasos hasta reiniciar o cargar un programa válido.

**¿Qué significa reiniciar?** El control de GUI y el menú de consola restauran el programa y sus datos iniciales con `restart()`. El método interno `reset()` es diferente: vacía el motor.

**¿Cómo se calcula el límite de ciclos?** Cuenta todas las instrucciones completadas desde carga o reinicio, incluidas las ejecutadas manualmente. Pausar o reanudar no devuelve el presupuesto completo. HALT en el último ciclo permitido es correcto.

**¿Qué diferencia hay entre traza e historial?** La traza contiene mensajes y diagnóstico. El historial contiene registros estructurados por instrucción completada, con PC y ACC antes/después, banderas y cambios de memoria. Los intentos cancelados o fallidos no cuentan como instrucciones completadas.

**¿Qué ocurre si se acaba la entrada en modo por archivo?** Se registra un error y el comando termina sin solicitar teclado. Se puede guardar ese estado con `--reporte`.

**¿Qué limita el modelo?** Tiene 100 celdas y diez instrucciones; no simula concurrencia, interrupciones, caché ni ancho de palabra fijo.

## Cierre y recomendaciones

Concluir relacionando el programa con los objetivos: observar el ciclo, comprobar cambios de estado y reproducir resultados. Mencionar como ampliaciones posibles etiquetas simbólicas, nuevas operaciones y un modelo de palabra fija, dejando claro que no forman parte de esta versión.

Entregar el código oficial, seis casos completos, manuales, evidencias reales y el documento impreso con diagramas. Antes de la entrega definitiva, completar portada, revisar la versión PDF y conservar la constancia que tenga el grupo sobre la elección de Python.

## Ensayo y respaldo

Hacer un ensayo completo con cronómetro y cambiar de integrante sin detener la demostración. Si el grupo supera 20 minutos, conservar la suma por pasos y resumir el bucle; no omitir la explicación de PC, IR, ACC o un error. Si falla una ejecución en vivo, leer el diagnóstico, reiniciar y repetir el ejemplo oficial. Si la computadora no permite abrir Tkinter, utilizar la consola y el reporte de respaldo, explicando qué se está mostrando.

Para compartir, utilizar `output/compartir/VM_STUDIO_GRUPO13.zip`. El compañero debe extraerlo y ejecutar desde la carpeta que contiene `simulador_vm.py`; copiar solo ese archivo omite los módulos y los programas de ejemplo.
