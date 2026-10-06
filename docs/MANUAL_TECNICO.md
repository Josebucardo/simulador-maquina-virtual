# Manual técnico

## Estructura del proyecto

```text
simulador_vm.py
verificar_entrega.py
test1_suma.asm
test2_resta.asm
test3_almacenamiento.asm
test4_condicional.asm
test5_bucle.asm
test6_entrada_salida.asm
docs/
```

## Componentes principales

### `Instruction`

Representa una instrucción cargada en memoria. Contiene:

- `opcode`: operación en mayúsculas.
- `operand`: dirección de memoria opcional.

### `Memory`

Simula memoria principal con 100 celdas.

Métodos principales:

- `read(address)`: lee cualquier contenido.
- `read_int(address)`: lee únicamente datos enteros.
- `write(address, value)`: escribe instrucciones o datos.
- `_check_bounds(address)`: valida que la dirección esté entre 0 y 99.
- `clear()`: reinicia memoria.

### `DeviceControllers`

Simula controladores de dispositivos:

- `keyboard_input()`: teclado virtual para `INPUT`.
- `printer_output()`: impresora virtual para `OUTPUT`.
- `load_program_from_disk()`: disco virtual para leer programas `.asm`.

### `VirtualMachine`

Contiene los registros y la unidad de control:

- `pc`: contador de programa.
- `ir`: registro de instrucción.
- `acc`: acumulador.
- `flag_z`: bandera cero.
- `flag_n`: bandera negativo.
- `halted`: estado de detención.

Métodos principales:

- `load_program(filepath)`: carga y valida un archivo.
- `step()`: ejecuta una instrucción.
- `_execute(instruction, original_pc)`: ejecuta el opcode.
- `_update_flags()`: actualiza `Z` y `N`.
- `run_all(max_cycles)`: ejecuta hasta `HALT`.
- `get_state_summary()`: devuelve estado actual.

## Validación de programas

El cargador detecta:

- Programa vacío.
- Instrucción inexistente.
- Operando faltante.
- Operando sobrante.
- Operando no numérico.
- Dirección fuera de memoria.
- Programa sin `HALT`.
- Programa con más instrucciones que celdas disponibles.

## Ciclo de ejecución interno

1. `step()` verifica si la máquina está detenida.
2. Lee `Memory[PC]`.
3. Valida que sea una instancia de `Instruction`.
4. Copia la instrucción a `IR`.
5. Incrementa `PC`.
6. Ejecuta la instrucción.
7. Actualiza `FLAGS`.
8. Devuelve si la máquina puede continuar.

## Instrucciones implementadas

| Opcode | Tipo | Efecto |
|---|---|---|
| `LOAD` | Memoria | `ACC = Mem[arg]` |
| `STORE` | Memoria | `Mem[arg] = ACC` |
| `ADD` | Aritmética | `ACC = ACC + Mem[arg]` |
| `SUB` | Aritmética | `ACC = ACC - Mem[arg]` |
| `JMP` | Control | `PC = arg` |
| `JZ` | Control | Si `Z = 1`, `PC = arg` |
| `JNZ` | Control | Si `Z = 0`, `PC = arg` |
| `INPUT` | Entrada | `ACC = valor leído` |
| `OUTPUT` | Salida | Imprime `ACC` |
| `HALT` | Control | `halted = True` |

## Pruebas

El archivo `verificar_entrega.py` ejecuta pruebas funcionales y pruebas de error. Debe terminar con:

```text
TODAS LAS PRUEBAS PASARON.
```

## Decisiones de diseño

- Se usa una memoria única para instrucciones y datos porque simplifica la arquitectura y permite mostrar claramente la diferencia entre código y datos.
- Los datos de prueba se colocan en direcciones separadas de las instrucciones para evitar sobrescribir el programa.
- `PC` se incrementa antes de ejecutar la instrucción; las instrucciones de salto reemplazan ese valor cuando corresponde.
- `FLAGS` se actualiza después de cada instrucción según el valor actual de `ACC`.
- El programa sin `HALT` se rechaza al cargar para exigir una terminacion explicita; el limite de ciclos detecta bucles que no llegan a HALT.


## Actualizacion VM Studio (Python autorizado)

Python fue autorizado por el docente, segun confirmacion del grupo. Se mantienen los componentes y objetivos de la propuesta.

- Estado ERROR: conserva el PC fallido y exige reinicio. Cancelar INPUT conserva la instruccion pendiente sin crear un error permanente.
- Z inicia activa porque ACC inicia en cero. FLAGS se actualiza tras cada instruccion completada.
- El motor registra FETCH, DECODE y EXECUTE en `last_trace`; las tarjetas muestran las fases de la ultima instruccion. El paso ejecuta una instruccion completa.
- `KeyboardController`, `DiskController` y `PrinterController` ofrecen controladores separados sobre las funciones compartidas de dispositivos.
- DATA direccion valor declara enteros iniciales. No cuenta como instruccion. Se rechazan duplicados, direcciones invalidas y superposicion con codigo antes de modificar la VM.
- El limite de ciclos detiene bucles incluso cuando existe HALT. Alcanzar HALT en el ultimo ciclo permitido es correcto.
- La GUI separa editor, traza, impresora y ayuda; permite filtrar memoria, pausar, ajustar velocidad y exportar evidencia JSON.
- El punto de entrada simulador_vm.py abre src/vm_studio/simulador_vm.py; el acceso antiguo se conserva en archive/.

## Recomendaciones

Ejecutar el verificador funcional, las pruebas de regresion y la verificacion de Tkinter antes de entregar. Revisar visualmente la GUI en el equipo de defensa. Exportar evidencia de suma, salto, entrada/salida y error. Renderizar los diagramas Mermaid antes de imprimir el documento. Completar integrantes, docente y fecha en la portada. No afirmar que tener HALT impide todos los bucles.
