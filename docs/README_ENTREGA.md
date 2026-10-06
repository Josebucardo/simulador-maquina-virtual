# Entrega Grupo 13 - Simulador de Máquina Virtual Simple

Este paquete contiene la implementación, casos de prueba, verificador automático y documentación del proyecto.

## Archivos principales

- `simulador_vm.py`: simulador principal con modo gráfico Tkinter y modo consola.
- `verificar_entrega.py`: verificador automático de casos de prueba y errores.
- `test1_suma.asm` a `test6_entrada_salida.asm`: programas de prueba en lenguaje de instrucciones.
- `docs/DOCUMENTO_TECNICO_GRUPO13.md`: documento técnico del Entregable 1.
- `docs/MANUAL_USUARIO.md`: guía para ejecutar y usar el simulador.
- `docs/MANUAL_TECNICO.md`: explicación interna del código.
- `docs/EVIDENCIAS_PRUEBAS.md`: resultados obtenidos en pruebas.
- `docs/GUIA_DEFENSA.md`: guía breve para exponer el proyecto.

## Comandos útiles

```bash
python simulador_vm.py
python simulador_vm.py --cli
python -m tests.verificar_entrega
```

## Lenguaje autorizado

Python está autorizado por el docente, según la confirmación del grupo. La entrega completa permanece en Python 3 y usa Tkinter, incluido con las distribuciones habituales de Python para Windows.

## VM Studio

La interfaz incluye tarjetas de registros, fases Fetch/Decode/Execute de la última instrucción, memoria filtrable, editor ASM, pestañas de traza e impresora, velocidad ajustable, límite de ciclos y exportación de evidencias JSON. F7 ejecuta una instrucción, F5 inicia o continúa y F6 pausa. Reiniciar restaura el código y los datos iniciales. Los errores de ejecución bloquean la máquina hasta reiniciar; cancelar INPUT permite reintentar.

Los programas pueden declarar datos: `DATA 90 12`. DATA no consume una dirección de código y no permite sobrescribir las instrucciones iniciales. Los seis ejemplos son autocontenidos. `ASO/simulador_vm.py` abre la implementación oficial de la raíz.

## Verificación ampliada

```bash
python -m tests.verificar_entrega
python -m unittest discover -s tests -v
python -m tests.verificar_gui
```

El último comando abre brevemente Tkinter y verifica sus controles. No sustituye una revisión visual manual de la ventana en la resolución de la computadora de la defensa.
