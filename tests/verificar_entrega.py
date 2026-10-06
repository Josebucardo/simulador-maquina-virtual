"""Verificador de pruebas para el Simulador de Máquina Virtual - Grupo 13."""

import os
import tempfile

from simulador_vm import (
    InvalidInstructionException,
    MemoryOutOfBoundsException,
    VirtualMachine,
    load_test_case,
)


def ejecutar_caso(numero, acc_esperado, memoria_esperada=None, entrada=None, salida_esperada=None):
    entradas = iter(entrada or [])
    logs = []
    vm = VirtualMachine(
        input_handler=(lambda: next(entradas)) if entrada is not None else None,
        output_handler=logs.append,
    )
    caso = load_test_case(vm, str(numero))
    vm.run_all()

    estado = "OK"
    if vm.acc != acc_esperado or not vm.halted:
        estado = "FALLA"
    if memoria_esperada:
        for direccion, esperado in memoria_esperada.items():
            if vm.memory.read(direccion) != esperado:
                estado = "FALLA"
    if salida_esperada and not any(salida_esperada in mensaje for mensaje in logs):
        estado = "FALLA"

    salida = {
        "prueba": caso["name"],
        "acc": vm.acc,
        "pc": vm.pc,
        "ir": str(vm.ir),
        "halted": vm.halted,
        "estado": estado,
    }
    if memoria_esperada:
        salida["memoria"] = {direccion: vm.memory.read(direccion) for direccion in memoria_esperada}
    return salida


def crear_programa_temporal(contenido):
    archivo = tempfile.NamedTemporaryFile("w", suffix=".asm", delete=False, encoding="utf-8")
    try:
        archivo.write(contenido)
        return archivo.name
    finally:
        archivo.close()


def verificar_error(nombre, contenido, excepcion_esperada):
    path = crear_programa_temporal(contenido)
    try:
        vm = VirtualMachine()
        vm.load_program(path)
    except excepcion_esperada:
        return f"{nombre}: OK"
    except Exception as exc:
        return f"{nombre}: FALLA - excepción incorrecta: {type(exc).__name__}: {exc}"
    else:
        return f"{nombre}: FALLA - no se detectó el error"
    finally:
        os.remove(path)


def verificar_recarga_caso():
    vm = VirtualMachine(input_handler=lambda: 7, output_handler=lambda _: None)
    load_test_case(vm, "1")
    vm.run_all()
    vm.memory.write(10, 999)

    load_test_case(vm, "1")
    estado_restaurado = (
        vm.pc == 0
        and vm.acc == 0
        and not vm.halted
        and vm.memory.read(10) == 10
        and vm.memory.read(11) == 20
    )
    vm.run_all()
    return estado_restaurado and vm.acc == 30 and vm.memory.read(20) == 30


def main():
    resultados = [
        ejecutar_caso(1, 30, {20: 30}),
        ejecutar_caso(2, 20, {20: 20}),
        ejecutar_caso(3, 30, {20: 30}),
        ejecutar_caso(4, 111),
        ejecutar_caso(5, 6, {53: 6}),
        ejecutar_caso(
            6,
            7,
            {20: 7},
            entrada=[7],
            salida_esperada="[DISPOSITIVO IMPRESORA] Salida reportada: ACC = 7",
        ),
    ]

    print("=== RESULTADOS DE CASOS DE PRUEBA ===")
    for item in resultados:
        memoria = f", memoria={item.get('memoria')}" if "memoria" in item else ""
        print(
            f"{item['prueba']}: ACC={item['acc']}, PC={item['pc']}, "
            f"IR={item['ir']}, HALT={item['halted']}{memoria} -> {item['estado']}"
        )

    print("\n=== VALIDACIÓN DE ERRORES ===")
    errores = [
        verificar_error("Instrucción inexistente", "MULT 10\nHALT\n", InvalidInstructionException),
        verificar_error("Programa sin HALT", "LOAD 10\nOUTPUT\n", InvalidInstructionException),
        verificar_error("Dirección inválida", "LOAD 200\nHALT\n", MemoryOutOfBoundsException),
        verificar_error("Error de sintaxis", "LOAD 10 20\nHALT\n", InvalidInstructionException),
    ]
    for resultado in errores:
        print(resultado)

    recarga_correcta = verificar_recarga_caso()
    print(f"Recarga de caso y restauración de datos: {'OK' if recarga_correcta else 'FALLA'}")

    if (
        any(item["estado"] != "OK" for item in resultados)
        or any("FALLA" in item for item in errores)
        or not recarga_correcta
    ):
        raise SystemExit(1)
    print("\nTODAS LAS PRUEBAS PASARON.")


if __name__ == "__main__":
    main()
