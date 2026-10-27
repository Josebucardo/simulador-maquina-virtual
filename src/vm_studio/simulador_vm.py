"""API compatible y punto de acceso de VM Studio."""
from .motor import *
from .consola import run_cli, main


def run_gui():
    """Carga Tkinter únicamente cuando se solicita la interfaz de escritorio."""
    from .interfaz import run_gui as launch
    return launch()

if __name__ == "__main__":
    raise SystemExit(main())
