# Entrega del grupo 13

**Fecha de revisión:** 26 de octubre de 2026.

La entrega contiene el simulador de máquina virtual, su código organizado por responsabilidades, programas ASM, pruebas, reportes y materiales para una exposición de tres integrantes. La implementación oficial está en `src/vm_studio/`; el comando habitual es `python simulador_vm.py`.

## Abrir los materiales

| Producto | Ruta |
|---|---|
| PowerPoint editable | `output/presentacion/DEFENSA_GRUPO13.pptx` |
| Guion para tres integrantes | `output/exposicion/GUIA_TRES_INTEGRANTES.docx` |
| Fuente del guion | `docs/exposicion/GUIA_TRES_INTEGRANTES.md` |
| Documento técnico Word | `output/word/ENTREGA_GRUPO13.docx` |
| Documento técnico PDF | `output/pdf/ENTREGA_GRUPO13.pdf` |
| Manual independiente | `output/manual/MANUAL_USUARIO_VM_STUDIO.docx` y `.pdf` |
| Propuesta original | `docs/requisitos/PROPUESTA_GRUPO13.pdf` |
| Reporte de ejemplo | `output/reportes/suma.html` |
| Paquete para compartir | `output/compartir/VM_STUDIO_GRUPO13.zip` |

Los integrantes, docente, institución y fecha de entrega permanecen como campos editables para completarlos con datos reales. La revisión del material no implica una fecha de entrega.

## Contenido del código

`motor.py` contiene memoria, registros, instrucciones y controladores; `interfaz.py` presenta Tkinter; `consola.py` ofrece el menú y el modo por archivo; `reportes.py` exporta HTML, CSV y JSON. `simulador_vm.py` conserva el punto de acceso compatible. Los ejemplos completos están en `examples/` y las verificaciones en `tests/`.

El diseño formal está en `docs/DOCUMENTO_TECNICO_GRUPO13.md`. Los manuales describen uso y funcionamiento. `docs/EVIDENCIAS_PRUEBAS.md` registra comprobaciones ejecutadas, y `docs/evidencias/` conserva detalle de estados, memoria, entradas, salidas y resultados.

## Ejecutar y validar

Requiere Python 3.10 o superior con Tkinter. El motor, las interfaces y los reportes utilizan la biblioteca estándar.

```powershell
python simulador_vm.py
python simulador_vm.py --cli
python -m tests.verificar_entrega
python -m unittest discover -s tests -v
python -m tests.verificar_gui
python scripts/generar_evidencias.py --incluir-gui
```

Las pruebas GUI necesitan escritorio y abren ventanas brevemente. Revisar los resultados generados y ensayar con la computadora de exposición. No se sustituye una comprobación fallida por una afirmación de funcionamiento.

## Reportes y reproducción

```powershell
python simulador_vm.py --archivo examples/test1_suma.asm --reporte output/reportes/suma.html
python simulador_vm.py --archivo examples/test6_entrada_salida.asm --entrada 7 --reporte output/reportes/entrada.csv
```

En modo por archivo, repetir `--entrada` para cada INPUT. `--max-ciclos` establece el total máximo desde carga o reinicio. Una falta de entradas produce error sin pedir teclado. Los reportes conservan el estado exportado, incluso cuando está pausado o tiene un error.

## Regenerar y compartir

```powershell
python -m pip install -r scripts/requirements_documento.txt
python -m pip install python-docx pypdfium2
python scripts/generar_documento.py
python scripts/generar_word.py
python scripts/preparar_entrega.py
```

Las dependencias de documentos son opcionales para ejecutar la aplicación. El empaquetado excluye cachés, temporales, `.git`, `archive/` y `ASO/`; evita incluir el ZIP dentro de sí mismo. Compartir el paquete final o los documentos específicos. Los compañeros deben extraer el ZIP antes de ejecutar el programa.

## Lenguaje y defensa

El proyecto conserva Python según autorización consignada por el grupo. La propuesta enumera Python y contiene también referencias específicas a Java; conservar el respaldo de esa autorización. La defensa debe demostrar memoria, PC, IR, ACC, ciclo, carga, pasos, automático, error y resultado. Su duración prevista es de 15 a 20 minutos.
