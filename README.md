# Simulador de máquina virtual — Grupo 13

Proyecto de Arquitectura de Sistemas Operativos, desarrollado en **Python** con autorización del docente. Simula memoria, registros y el ciclo Fetch → Decode → Execute con una interfaz gráfica Tkinter y un modo consola.

## Ejecutar

Requiere Python 3.10 o superior con Tkinter. No necesita instalar paquetes externos. Ejecuta los comandos desde la carpeta raíz del proyecto:

```powershell
python simulador_vm.py
```

Modo consola:

```powershell
python simulador_vm.py --cli
```

En Windows, si `python` no está disponible, prueba `py` en su lugar. Comprueba que Tkinter funciona con `python -m tkinter`.

## Estructura

```text
simulador_vm.py               Punto de entrada
src/
  vm_studio/
    simulador_vm.py           Motor, controladores e interfaz
examples/                    Programas ASM autocontenidos
tests/
  verificar_entrega.py        Casos funcionales y errores de carga
  test_regresiones.py         Pruebas del motor y sus explicaciones
  verificar_gui.py           Comprobaciones de controles Tkinter
docs/
  DOCUMENTO_TECNICO_GRUPO13.md Diseño y arquitectura
  MANUAL_USUARIO.md           Uso de la aplicación
  MANUAL_TECNICO.md           Funcionamiento del código
  GUIA_DEFENSA.md             Guion para exponer
  EVIDENCIAS_PRUEBAS.md       Resultados de comprobaciones
  evidencias/suma.json        Ejemplo de evidencia exportada
.gitignore                   Archivos que no se publican
```

El material antiguo se conserva localmente en `archive/`, excluido de Git. La carpeta `ASO/` puede conservar cachés antiguos y también está excluida. La implementación oficial está en `src/vm_studio/`.

## Funciones

- Memoria de 100 celdas, registros PC/IR/ACC y banderas Z/N.
- Diez instrucciones: LOAD, STORE, ADD, SUB, JMP, JZ, JNZ, INPUT, OUTPUT y HALT.
- Directiva DATA para declarar datos iniciales.
- Ejecución por pasos o automática, pausa y velocidad ajustable.
- Explicación sencilla de cada instrucción y tarjetas del ciclo de ejecución.
- Editor ASM, memoria filtrable, salida de impresora y exportación JSON.
- Validación de sintaxis, límites de memoria y detección de bucles por límite de ciclos.

Ejemplo:

```asm
DATA 90 10
DATA 91 20
LOAD 90
ADD 91
STORE 92
OUTPUT
HALT
```

## Pruebas

```powershell
python -m tests.verificar_entrega
python -m unittest discover -s tests -v
python -m tests.verificar_gui
```

La última prueba abre brevemente la interfaz gráfica y necesita una sesión de escritorio. Los compañeros deben ejecutar estas comprobaciones antes de subir cambios.

## Compartir por GitHub

Desde esta carpeta, con Git instalado:

```powershell
git init
git add .
git commit -m "Organizar simulador de máquina virtual en Python"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/TU_REPOSITORIO.git
git push -u origin main
```

Crea primero un repositorio vacío en GitHub y reemplaza la URL por la de ese repositorio. Si el proyecto ya tiene un remoto configurado, usa `git remote -v` antes de agregar otro.

Tus compañeros pueden descargarlo con `git clone URL_DEL_REPOSITORIO`, entrar a esa carpeta y ejecutar `python simulador_vm.py`.

Para trabajar juntos, cada integrante debe crear una rama, probar sus cambios y abrir un pull request. Eviten incluir credenciales, entornos virtuales o archivos temporales. Las evidencias que quieran entregar se guardan en `docs/evidencias/`.
