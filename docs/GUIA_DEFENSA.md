# Guía de defensa del proyecto

## Duración sugerida

15 a 20 minutos.

## Orden recomendado

1. Presentar el objetivo del proyecto.
2. Explicar qué es la máquina virtual y qué componentes simula.
3. Mostrar la memoria de 100 celdas.
4. Explicar los registros `PC`, `IR`, `ACC` y `FLAGS`.
5. Mostrar un programa `.asm` sencillo.
6. Cargar el programa en la interfaz.
7. Ejecutar paso a paso y explicar Fetch, Decode y Execute.
8. Ejecutar automáticamente un caso completo.
9. Mostrar un caso con salto condicional o bucle.
10. Mostrar un error controlado.
11. Ejecutar `python -m tests.verificar_entrega` para enseñar evidencias.
12. Cerrar con conclusiones.

## Explicación corta del ciclo

Cuando se ejecuta una instrucción, la máquina usa `PC` para buscar la instrucción en memoria. Esa instrucción se guarda en `IR`. Luego la unidad de control interpreta el opcode. Si la instrucción necesita datos, lee memoria. Si modifica resultados, cambia `ACC`, memoria o `PC`. Al final actualiza las banderas `Z` y `N`.

## Ejemplo para explicar paso a paso

Programa:

```asm
LOAD 10
ADD 11
STORE 20
OUTPUT
HALT
```

Explicación:

- `LOAD 10`: copia `Mem[10]` al acumulador.
- `ADD 11`: suma `Mem[11]` al acumulador.
- `STORE 20`: guarda el resultado en `Mem[20]`.
- `OUTPUT`: muestra el acumulador en la impresora simulada.
- `HALT`: finaliza la ejecución.

## Preguntas probables y respuestas

**¿Para qué sirve el PC?**  
Indica la dirección de la próxima instrucción a ejecutar.

**¿Para qué sirve el IR?**  
Guarda la instrucción que se está ejecutando actualmente.

**¿Por qué se usa ACC?**  
Porque simplifica las operaciones aritméticas. Las instrucciones cargan, suman, restan y almacenan usando el acumulador.

**¿Qué hace `JZ`?**  
Salta a otra dirección si el acumulador quedó en cero y la bandera `Z` está activa.

**¿Qué pasa si el programa no tiene `HALT`?**  
El simulador rechaza la carga porque el lenguaje exige una terminación explícita. Tener HALT no garantiza alcanzarlo: un límite de ciclos detecta bucles infinitos.

**¿Cómo se simula el disco?**  
Con el controlador que lee archivos `.asm` desde almacenamiento.

**¿Cómo se simula el teclado?**  
Con la instrucción `INPUT`, que pide un número al usuario.

**¿Cómo se simula la impresora?**  
Con `OUTPUT`, que reporta el valor actual de `ACC`.

## Demostración recomendada

- Cargar `test1_suma.asm` y correr paso a paso.
- Cargar `test5_bucle.asm` y ejecutar automático.
- Cargar `test6_entrada_salida.asm` para demostrar teclado e impresora.
- Probar un error escribiendo un archivo con `MULT 10`.


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
