# Evidencias de pruebas

## Validación de VM Studio — 5 de octubre de 2026

- Verificador de entrega: seis casos funcionales, cuatro errores de carga y restauración de caso correctos.
- `python -m unittest discover -s tests -v`: once pruebas correctas. Incluyen HALT en el límite, cancelación y reintento, PC conservado tras error, bloqueo hasta reinicio, bucles, ramas condicionales, JMP, límites de memoria, carga inválida, banderas, fases, validación de entrada y DATA.
- `python -m tests.verificar_gui`: comprobados los controles reales de Tkinter para carga, memoria, pasos, impresora, reinicio, pausa, ejecución automática, editor, cancelación, exportación JSON y límite de ciclos en ejecución gráfica.
- Sintaxis Python validada con `py_compile`.

Estas son comprobaciones funcionales automatizadas. La disposición visual debe revisarse en la resolución del equipo de defensa; no se incluyen capturas de pantalla en esta evidencia.

## Comando usado

```bash
python -m tests.verificar_entrega
```

## Resultado obtenido

```text
=== RESULTADOS DE CASOS DE PRUEBA ===
Suma: ACC=30, PC=5, IR=HALT, HALT=True, memoria={20: 30} -> OK
Resta: ACC=20, PC=5, IR=HALT, HALT=True, memoria={20: 20} -> OK
Almacenamiento: ACC=30, PC=5, IR=HALT, HALT=True, memoria={20: 30} -> OK
Condicional JZ: ACC=111, PC=9, IR=HALT, HALT=True -> OK
Bucle con JNZ: ACC=6, PC=14, IR=HALT, HALT=True, memoria={53: 6} -> OK
Entrada y salida: ACC=7, PC=4, IR=HALT, HALT=True, memoria={20: 7} -> OK

=== VALIDACIÓN DE ERRORES ===
Instrucción inexistente: OK
Programa sin HALT: OK
Dirección inválida: OK
Error de sintaxis: OK

TODAS LAS PRUEBAS PASARON.
```

## Tabla de pruebas funcionales

| Prueba | Resultado esperado | Resultado obtenido | Estado |
|---|---|---|---|
| Suma | `ACC = 30`, `Mem[20] = 30` | `ACC = 30`, `Mem[20] = 30` | Correcto |
| Resta | `ACC = 20`, `Mem[20] = 20` | `ACC = 20`, `Mem[20] = 20` | Correcto |
| STORE | `Mem[20] = 30` | `Mem[20] = 30` | Correcto |
| JZ | Cambia `PC` hacia rutina verdadera | `ACC = 111`, finaliza en `HALT` | Correcto |
| JNZ / Bucle | Repite hasta contador cero | `ACC = 6`, `Mem[53] = 6` | Correcto |
| INPUT / OUTPUT | Lee entrada `7` y la imprime | `ACC = 7`, `Mem[20] = 7` | Correcto |

## Tabla de manejo de errores

| Error probado | Programa usado | Resultado |
|---|---|---|
| Instrucción inexistente | `MULT 10` | Detectado |
| Programa sin `HALT` | `LOAD 10`, `OUTPUT` | Detectado |
| Dirección inválida | `LOAD 200` | Detectado |
| Error de sintaxis | `LOAD 10 20` | Detectado |

## Evidencia de compilación

También se validó sintaxis Python con:

```bash
python -m compileall -q src tests simulador_vm.py
```

El comando finalizó sin errores.
