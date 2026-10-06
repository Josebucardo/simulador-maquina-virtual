"""Punto de entrada del simulador. Ejecuta: python simulador_vm.py."""
import sys
from src.vm_studio.simulador_vm import *  # Compatibilidad para los verificadores.


if __name__ == "__main__":
    if "--cli" in sys.argv:
        run_cli()
    else:
        run_gui()
