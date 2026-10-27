# Comandos para abrir y demostrar VM Studio

Abre PowerShell en la carpeta que contiene `simulador_vm.py`. La aplicación necesita Python 3.10 o superior con Tkinter; no necesita instalar paquetes adicionales.

## Abrir la interfaz

```powershell
python simulador_vm.py
```

Si `python` no está disponible, sustituye ese comando por `py -3`. También puedes abrir `INICIAR_VM.cmd` con doble clic.

En la ventana selecciona Suma y pulsa Cargar ejemplo. F7 completa una instrucción, F5 ejecuta automáticamente y F6 pausa. La suma finaliza con ACC = 30, Mem[20] = 30 y salida 30. Reiniciar restaura el programa para repetirlo.

## Abrir el menú de consola

```powershell
python simulador_vm.py --cli
```

Selecciona 1 para cargar un ejemplo, 3 para un paso, 4 para automático, 5 para consultar el estado, 8 para reiniciar, 9 para exportar un reporte y 0 para salir.

## Producir reportes sin diálogos

```powershell
python simulador_vm.py --archivo examples/test1_suma.asm --reporte output/reportes/suma.html
python simulador_vm.py --archivo examples/test6_entrada_salida.asm --entrada 7 --reporte output/reportes/entrada.csv
python simulador_vm.py --archivo examples/multiplicacion.asm --entrada -4 --entrada 3 --reporte output/reportes/multiplicacion.json
```

Los resultados esperados son 30, 7 y -12 respectivamente. Abre `output/reportes/suma.html` en un navegador para mostrar el historial. Los reportes HTML funcionan sin conexión y se pueden imprimir o guardar como PDF desde el navegador.

## Demostrar un error controlado

```powershell
python simulador_vm.py --archivo examples/errores/lectura_de_codigo.asm --reporte output/reportes/error.html
python simulador_vm.py --archivo examples/errores/bucle_controlado.asm --max-ciclos 10 --reporte output/reportes/bucle_error.json
```

Estos dos comandos deben terminar con ERROR y código de salida 1. Son pruebas de detección de fallos: el primero intenta leer código como dato; el segundo no alcanza HALT y agota diez ciclos. No deben presentarse como ejecuciones correctas.

## Comprobar el proyecto

```powershell
python -m tests.verificar_entrega
python -m unittest discover -s tests -v
python -m tests.verificar_gui
```

Las pruebas gráficas abren la ventana brevemente. Para renovar además las evidencias y reportes de muestra:

```powershell
python scripts/generar_evidencias.py --incluir-gui
```

## Compartir

Envía `output/compartir/VM_STUDIO_GRUPO13.zip`. Tus compañeros deben extraer toda la carpeta y conservar juntos `src/`, `examples/` y el punto de entrada. El manual está en `output/manual/`, las diapositivas en `output/presentacion/` y el guion de los tres participantes en `output/exposicion/`.
