# Manual de usuario - VM Studio

## Inicio
Ejecuta `python simulador_vm.py`. Para consola: `python simulador_vm.py --cli`.
Python esta autorizado por el docente. No requiere librerias externas; utiliza Tkinter.

## Interfaz
- Encabezado: estado de ejecucion.
- Tarjetas: PC, IR, ACC, FLAGS y ciclos completados.
- Fases: FETCH, DECODE y EXECUTE de la ultima instruccion. Cada paso completa una instruccion; las tarjetas explican las fases, no son micro pasos independientes.
- Memoria: 100 celdas, filtros de codigo y datos no cero. La fila verde corresponde al siguiente PC.
- Traza: operaciones y cambios de estado. Impresora: valores emitidos por OUTPUT.
- Cada instrucción completada incluye una explicación en palabras simples, resaltada en verde: qué número se lee, qué cuenta se realiza, dónde se guarda el resultado y por qué se toma o no un salto. Estas explicaciones también se exportan en la evidencia JSON.
- Editor ASM: escribir, guardar y cargar programas. Ayuda: sintaxis y atajos.

## Ejemplo autocontenido
```asm
DATA 90 10
DATA 91 20
LOAD 90
ADD 91
STORE 92
OUTPUT
HALT
```
DATA declara datos sin consumir direcciones de instrucciones. Las direcciones de codigo empiezan en cero y solo cuentan las instrucciones. No se permiten datos iniciales sobre el codigo ni declaraciones duplicadas.

## Controles
Carga un ejemplo o archivo, o pulsa Cargar desde editor. F7 ejecuta un paso, F5 ejecuta automaticamente y F6 pausa. El deslizador establece milisegundos entre instrucciones. El limite corresponde al total de ciclos desde la carga o reinicio, incluidas las ejecuciones por pasos. HALT en el ultimo ciclo permitido termina normalmente.

Reiniciar restaura el programa y sus datos iniciales. Una edicion de datos antes del primer paso se conserva al reiniciar. Una edicion durante la ejecucion es temporal. El codigo se modifica desde el editor. Pulsar Ejecutar despues de HALT no repite el programa; pulsa Reiniciar.

Cancelar INPUT deja el PC, ACC y contador de ciclos sin cambios y permite reintentar. Un error de ejecucion conserva el PC de la instruccion fallida y bloquea nuevos pasos hasta reiniciar. Una carga invalida conserva el programa anterior.

## Evidencias
Exportar evidencia guarda JSON con codigo, datos iniciales, registros, memoria completa, impresora, traza y las fases de la ultima instruccion. Exporta al finalizar para entregar resultados reproducibles. El editor debe cargarse antes de ejecutarse; guardar ASM guarda el texto actual.

## Consola
El menu permite cargar, ejecutar, ver registros/memoria y editar datos. Las operaciones se imprimen como traza. La opcion Reiniciar de consola vacia la maquina: vuelve a cargar el programa. El modo consola tiene limite de 10000 ciclos por llamada a Ejecutar Todo.

## Programa adicional
examples/multiplicacion.asm multiplica dos enteros mediante sumas: el segundo debe ser no negativo. El decremento es constante 1; ya no solicita una tercera entrada. Un segundo entero negativo genera un bucle y se detiene al alcanzar el limite.
