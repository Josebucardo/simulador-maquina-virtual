# Evidencias de pruebas

Validación ejecutada: 2026-10-27T05:59:16-06:00 (America/Managua).

Este archivo se genera con resultados obtenidos al ejecutar el código actual. Los JSON conservan programas, entradas, registros, memoria, salida y fases de cada paso.

## Reproducción

```powershell
python scripts/generar_evidencias.py --incluir-gui
```

Sin `--incluir-gui` se ejecutan las pruebas de consola y se indica que la GUI no fue comprobada en esa ejecución.

## Resultados funcionales

| Prueba | Esperado | Obtenido | Estado |
|---|---|---|---|
| Suma | ACC=30; impresora=[30]; Mem[20]=30 | ACC=30; PC=5; HALT=True; Mem[20]=30 | CORRECTO |
| Resta | ACC=20; impresora=[20]; Mem[20]=20 | ACC=20; PC=5; HALT=True; Mem[20]=20 | CORRECTO |
| Almacenamiento | ACC=30; impresora=[30]; Mem[20]=30 | ACC=30; PC=5; HALT=True; Mem[20]=30 | CORRECTO |
| Condicional JZ | ACC=111; impresora=[111] | ACC=111; PC=9; HALT=True | CORRECTO |
| Bucle con JNZ | ACC=6; impresora=[6]; Mem[53]=6 | ACC=6; PC=14; HALT=True; Mem[53]=6 | CORRECTO |
| Entrada y salida | ACC=7; impresora=[7]; Mem[20]=7 | ACC=7; PC=4; HALT=True; Mem[20]=7 | CORRECTO |

Los seis ejemplos se cargan desde su propio texto, con DATA cuando corresponde; no se agregan datos desde el catálogo de casos. Entrada del sexto programa: 7.

## Traza numérica de suma

| Paso | Instrucción | PC antes | PC después | ACC antes | ACC después | Mem[20] |
|---|---|---|---|---|---|---|
| 1 | LOAD 10 | 0 | 1 | 0 | 10 | 0 |
| 2 | ADD 11 | 1 | 2 | 10 | 30 | 0 |
| 3 | STORE 20 | 2 | 3 | 30 | 30 | 30 |
| 4 | OUTPUT | 3 | 4 | 30 | 30 | 30 |
| 5 | HALT | 4 | 5 | 30 | 30 | 30 |

## Validaciones de carga

| Situación | Programa | Estado |
|---|---|---|
| Instrucción inexistente | `MULT 10; HALT` | CORRECTO |
| Programa sin HALT | `LOAD 10; OUTPUT` | CORRECTO |
| Dirección superior inválida | `LOAD 100; HALT` | CORRECTO |
| Dirección negativa | `STORE -1; HALT` | CORRECTO |
| Error de sintaxis | `LOAD 10 20; HALT` | CORRECTO |
| Registro no válido | `LOAD R9; HALT` | CORRECTO |
| Registro usado como dirección | `LOAD ACC; HALT` | CORRECTO |
| DATA sobre código | `DATA 0 5; HALT` | CORRECTO |
| DATA duplicado | `DATA 90 1; DATA 90 2; HALT` | CORRECTO |

Los mensajes completos y el tipo de excepción están en `docs/evidencias/errores_carga.json`.

## Error de ejecución y estado de consola

El programa `LOAD 0; HALT` intenta leer código como un número. La VM conserva PC=0, registra la causa y exige reinicio. La consola informa ERROR.

```text
====================================================
ESTADO DE LA MÁQUINA VIRTUAL (GRUPO 13)
====================================================
  PC  (Contador Programa)   : 00
  IR  (Registro Instrucción): LOAD 0
  ACC (Acumulador)          : 0
  FLAGS                     : [Z=1, N=0]
  ESTADO                    : ERROR
  CICLOS                    : 0
  CAUSA                     : La celda [0] contiene 'LOAD 0', no un dato numérico entero.
====================================================
```

Resultado: CORRECTO.

## Verificador de entrega

Comando: `python -m tests.verificar_entrega`.

Estado: CORRECTO.

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
Recarga de caso y restauración de datos: OK

TODAS LAS PRUEBAS PASARON.
```

## Pruebas de regresión

Comando: `python -m unittest discover -s tests -v`.

Estado: CORRECTO.

```text
test_archivo_con_entradas_repetidas_no_solicita_dialogos (test_consola.ConsoleTests.test_archivo_con_entradas_repetidas_no_solicita_dialogos) ... ok
test_argumentos_incompatibles_se_rechazan_antes_de_ejecutar (test_consola.ConsoleTests.test_argumentos_incompatibles_se_rechazan_antes_de_ejecutar) ... ok
test_bucle_batch_termina_y_exporta_error_en_limite_total (test_consola.ConsoleTests.test_bucle_batch_termina_y_exporta_error_en_limite_total) ... ok
test_carga_fallida_da_codigo_de_error_y_reporte_si_se_pidio (test_consola.ConsoleTests.test_carga_fallida_da_codigo_de_error_y_reporte_si_se_pidio) ... ok
test_falta_entrada_conserva_error_y_exporta_sin_bloquear (test_consola.ConsoleTests.test_falta_entrada_conserva_error_y_exporta_sin_bloquear) ... ok
test_menu_consulta_sin_carga_no_inutiliza_maquina (test_consola.ConsoleTests.test_menu_consulta_sin_carga_no_inutiliza_maquina) ... ok
test_menu_fin_de_archivo_y_ctrl_c_salen_sin_traceback (test_consola.ConsoleTests.test_menu_fin_de_archivo_y_ctrl_c_salen_sin_traceback) ... ok
test_menu_no_permite_editar_codigo_y_continua_utilizable (test_consola.ConsoleTests.test_menu_no_permite_editar_codigo_y_continua_utilizable) ... ok
test_menu_reinicia_datos_y_repite_programa (test_consola.ConsoleTests.test_menu_reinicia_datos_y_repite_programa) ... ok
test_archivo_con_bom_y_data_pasa_por_controlador_una_vez (test_regresiones.VMTests.test_archivo_con_bom_y_data_pasa_por_controlador_una_vez) ... ok
test_bucle_infinito (test_regresiones.VMTests.test_bucle_infinito) ... ok
test_cancelacion_y_error_no_producen_instrucciones_ficticias (test_regresiones.VMTests.test_cancelacion_y_error_no_producen_instrucciones_ficticias) ... ok
test_cancelar_y_reintentar (test_regresiones.VMTests.test_cancelar_y_reintentar) ... ok
test_carga_api_invalida_conserva_ejecucion_completa (test_regresiones.VMTests.test_carga_api_invalida_conserva_ejecucion_completa) ... ok
test_carga_invalida_preserva_programa (test_regresiones.VMTests.test_carga_invalida_preserva_programa) ... ok
test_cargador_copia_instrucciones_y_preserva_fuente (test_regresiones.VMTests.test_cargador_copia_instrucciones_y_preserva_fuente) ... ok
test_comentarios_y_limite_programa (test_regresiones.VMTests.test_comentarios_y_limite_programa) ... ok
test_consola_muestra_error_y_causa_hasta_recargar (test_regresiones.VMTests.test_consola_muestra_error_y_causa_hasta_recargar) ... ok
test_datos_declarados (test_regresiones.VMTests.test_datos_declarados) ... ok
test_diagnostico_registro_invalido_y_operando_no_entero (test_regresiones.VMTests.test_diagnostico_registro_invalido_y_operando_no_entero) ... ok
test_edicion_respeta_codigo_error_y_recuperacion (test_regresiones.VMTests.test_edicion_respeta_codigo_error_y_recuperacion) ... ok
test_entrada_tipo_invalido (test_regresiones.VMTests.test_entrada_tipo_invalido) ... ok
test_error_conserva_pc_y_bloquea (test_regresiones.VMTests.test_error_conserva_pc_y_bloquea) ... ok
test_explicaciones_reflejan_valores_y_decisiones (test_regresiones.VMTests.test_explicaciones_reflejan_valores_y_decisiones) ... ok
test_flags_iniciales_y_fases (test_regresiones.VMTests.test_flags_iniciales_y_fases) ... ok
test_halt_en_limite (test_regresiones.VMTests.test_halt_en_limite) ... ok
test_historial_registra_entrada_salida_y_cambio_de_memoria (test_regresiones.VMTests.test_historial_registra_entrada_salida_y_cambio_de_memoria) ... ok
test_limite_total_incluye_pasos_manuales (test_regresiones.VMTests.test_limite_total_incluye_pasos_manuales) ... ok
test_limites_y_fetch_invalido (test_regresiones.VMTests.test_limites_y_fetch_invalido) ... ok
test_memoria_rechaza_tipos_invalidos_sin_escribir (test_regresiones.VMTests.test_memoria_rechaza_tipos_invalidos_sin_escribir) ... ok
test_paso_sin_carga_no_bloquea_y_permite_cargar (test_regresiones.VMTests.test_paso_sin_carga_no_bloquea_y_permite_cargar) ... ok
test_reinicio_restaura_datos_editados_antes_del_primer_paso (test_regresiones.VMTests.test_reinicio_restaura_datos_editados_antes_del_primer_paso) ... ok
test_saltos (test_regresiones.VMTests.test_saltos) ... ok
test_csv_uniforme_formula_segura_y_numeros (test_reportes.ReportTests.test_csv_uniforme_formula_segura_y_numeros) ... ok
test_error_y_maquina_vacia (test_reportes.ReportTests.test_error_y_maquina_vacia) ... ok
test_guardado_roundtrip_y_extension_sin_destruir (test_reportes.ReportTests.test_guardado_roundtrip_y_extension_sin_destruir) ... ok
test_html_escapa_nombre_codigo_y_error (test_reportes.ReportTests.test_html_escapa_nombre_codigo_y_error) ... ok
test_salto_destino_secuencial_se_cuenta_por_condicion (test_reportes.ReportTests.test_salto_destino_secuencial_se_cuenta_por_condicion) ... ok
test_snapshot_independiente_y_estados (test_reportes.ReportTests.test_snapshot_independiente_y_estados) ... ok

----------------------------------------------------------------------
Ran 39 tests in 0.221s

OK
```

## Interfaz gráfica

Comando: `python -m tests.verificar_gui`.

Estado: CORRECTO.

```text
GUI OK: carga por controlador, DATA, pasos y pausa, reentrada protegida, editor pendiente, filtros, edición, límites, reinicio, errores y reportes JSON/HTML/CSV; ventana 1024x700 y 1366x768.
```

## Archivos de evidencia

- `output/reportes/`: reportes HTML imprimibles, CSV para Excel y JSON completos de los seis casos; también se conserva el error de ejecución.
- `docs/evidencias/suma.json`, `resta.json` y `almacenamiento.json`.
- `docs/evidencias/condicional.json`, `bucle.json` y `entrada_salida.json`.
- `docs/evidencias/errores_carga.json` y `error_ejecucion.json`.
- `docs/evidencias/resumen.json`: fecha, resultados y comandos de esta validación.
- `docs/evidencias/verificador.txt` y `regresiones.txt`: salidas completas.
- `docs/evidencias/gui.txt`: resultado de GUI; indica si se omitió.

La prueba gráfica comprueba controles reales de Tkinter. La revisión visual del PDF y el ensayo oral de la defensa se realizan por separado.
