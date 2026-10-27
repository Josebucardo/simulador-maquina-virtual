"""Consola interactiva y ejecución reproducible de archivos ASM."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .motor import TEST_CASES, InvalidInstructionException, VirtualMachine, load_test_case


def _export_report(vm: VirtualMachine, path):
    """Importa el exportador solo cuando el usuario solicita un reporte."""
    from .reportes import build_evidence, save_report

    return save_report(build_evidence(vm), path)


def run_cli(max_cycles=10000):
    """Abre el menú; EOF o Ctrl+C terminan sin una excepción de Python visible."""
    vm = VirtualMachine()
    while True:
        print("\n=== MÁQUINA VIRTUAL SIMPLE · GRUPO 13 ===")
        print("1. Cargar caso de prueba (1 al 6)")
        print("2. Cargar archivo .asm")
        print("3. Ejecutar siguiente instrucción (Fetch / Decode / Execute)")
        print("4. Ejecutar automáticamente")
        print("5. Ver registros y estado")
        print("6. Ver memoria")
        print("7. Editar una celda de datos")
        print("8. Reiniciar el programa cargado")
        print("9. Exportar reporte HTML, CSV o JSON")
        print("0. Salir")
        try:
            option = input("Seleccione opción: ").strip()
            if option == "1":
                for key, case in TEST_CASES.items():
                    print(f"{key}. {case['name']} | Esperado: {case['expected']}")
                case = load_test_case(vm, input("Caso de prueba: ").strip())
                print(f"Caso cargado: {case['name']}. Esperado: {case['expected']}.")
                vm.print_state()
            elif option == "2":
                path = input("Ruta del archivo .asm: ").strip().strip('"')
                vm.load_program(path)
                vm.print_state()
            elif option == "3":
                if vm.program_loaded and not vm.halted and vm.cycles >= max_cycles:
                    vm.error = "Límite de ciclos excedido: posible bucle infinito."
                    raise TimeoutError(vm.error)
                vm.step()
                vm.print_state()
            elif option == "4":
                vm.run_all(max_cycles)
                vm.print_state()
            elif option == "5":
                vm.print_state()
            elif option == "6":
                start = int(input("Dirección inicial (0): ") or "0")
                end = int(input("Dirección final (20): ") or "20")
                vm.memory._check_bounds(start)
                vm.memory._check_bounds(end)
                if start > end:
                    raise ValueError("La dirección inicial no puede superar la final.")
                for address in range(start, end + 1):
                    print(f"[{address:02d}]: {vm.memory.read(address)}")
            elif option == "7":
                if not vm.program_loaded:
                    raise InvalidInstructionException("Cargue un programa antes de editar sus datos.")
                address = int(input("Dirección de datos (0-99): "))
                value = int(input("Nuevo entero: "))
                vm.edit_data(address, value)
                print(f"Mem[{address:02d}] = {value}")
            elif option == "8":
                vm.restart()
                print("Programa y datos iniciales restaurados.")
                vm.print_state()
            elif option == "9":
                if not vm.program_loaded:
                    raise InvalidInstructionException("Cargue un programa antes de exportar su reporte.")
                path = input("Ruta del reporte (.html, .csv o .json): ").strip().strip('"')
                saved = _export_report(vm, path)
                print(f"Reporte guardado: {Path(saved).resolve()}")
            elif option == "0":
                print("Sesión finalizada.")
                return 0
            else:
                print("Opción no válida. Elija un número del 0 al 9.")
        except (EOFError, KeyboardInterrupt):
            print("\nSesión finalizada.")
            return 0
        except Exception as exc:
            print(f"[ERROR] {exc}")


def _positive_int(value):
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise argparse.ArgumentTypeError("el límite debe ser un entero positivo") from None
    if number <= 0:
        raise argparse.ArgumentTypeError("el límite debe ser un entero positivo")
    return number


def main(argv=None):
    """Selecciona GUI, consola o ejecución de archivo sin interacción."""
    parser = argparse.ArgumentParser(
        prog="simulador_vm.py",
        description="VM Studio · Máquina virtual simple del grupo 13.",
        epilog=("Ejemplo: python simulador_vm.py --archivo examples/test6_entrada_salida.asm "
                "--entrada 7 --reporte output/reportes/entrada.html"),
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--cli", action="store_true", help="Abrir el menú de consola.")
    mode.add_argument("--archivo", type=Path, help="Ejecutar un archivo ASM sin diálogos.")
    parser.add_argument("--entrada", type=int, action="append", default=[],
                        help="Entero para INPUT; repetir la opción para varias entradas.")
    parser.add_argument("--reporte", type=Path, help="Guardar reporte .html, .csv o .json del archivo.")
    parser.add_argument("--max-ciclos", type=_positive_int, default=None,
                        help="Límite total desde carga o reinicio (10000 por defecto).")
    args = parser.parse_args(argv)
    if not args.archivo and (args.entrada or args.reporte is not None):
        parser.error("--entrada y --reporte requieren --archivo")
    if args.max_ciclos is not None and not (args.archivo or args.cli):
        parser.error("--max-ciclos requiere --archivo o --cli; en GUI se ajusta en la ventana")
    if args.reporte is not None and args.reporte.suffix.lower() not in {".html", ".csv", ".json"}:
        parser.error("el reporte debe terminar en .html, .csv o .json")
    ceiling = args.max_ciclos or 10000
    if args.cli:
        return run_cli(ceiling)
    if not args.archivo:
        from .interfaz import run_gui

        run_gui()
        return 0

    inputs = iter(args.entrada)

    def read_input():
        try:
            return next(inputs)
        except StopIteration:
            raise InvalidInstructionException(
                "Faltan valores para INPUT. Agregue una opción --entrada ENTERO por cada lectura."
            ) from None

    vm = VirtualMachine(input_handler=read_input, output_handler=lambda _: None)
    result = 0
    try:
        vm.load_program(args.archivo)
        vm.run_all(ceiling)
    except Exception as exc:
        # Los errores de carga también se conservan en un reporte solicitado.
        if not vm.error:
            vm.error = str(exc)
        print(f"[ERROR] {exc}", file=sys.stderr)
        result = 1
    except KeyboardInterrupt:
        vm.error = "Ejecución cancelada por el usuario."
        print("[ERROR] Ejecución cancelada por el usuario.", file=sys.stderr)
        result = 1
    vm.print_state()
    if vm.outputs:
        print("IMPRESORA: " + ", ".join(str(value) for value in vm.outputs))
    if args.reporte is not None:
        try:
            saved = _export_report(vm, args.reporte)
            print(f"Reporte guardado: {Path(saved).resolve()}")
        except Exception as exc:
            print(f"[ERROR] No se pudo guardar el reporte: {exc}", file=sys.stderr)
            result = 1
    return result
