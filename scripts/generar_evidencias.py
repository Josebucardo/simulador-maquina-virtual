"""Ejecuta pruebas y produce evidencias reales de la entrega, sin dependencias externas."""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulador_vm import (  # noqa: E402
    DeviceControllers,
    Instruction,
    InvalidInstructionException,
    MemoryOutOfBoundsException,
    TEST_CASES,
    VirtualMachine,
)
from src.vm_studio.reportes import build_evidence, save_report  # noqa: E402


CASES = (
    ("1", "suma", 30, {20: 30}, []),
    ("2", "resta", 20, {20: 20}, []),
    ("3", "almacenamiento", 30, {20: 30}, []),
    ("4", "condicional", 111, {}, []),
    ("5", "bucle", 6, {53: 6}, []),
    ("6", "entrada_salida", 7, {20: 7}, [7]),
)


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def capture_case(number, slug, expected_acc, expected_memory, inputs, folder):
    case = TEST_CASES[number]
    code = (ROOT / "examples" / case["file"]).read_text(encoding="utf-8-sig")
    input_values = iter(inputs)
    printer = []
    vm = None

    def output(message):
        if message.startswith("[DISPOSITIVO IMPRESORA]"):
            printer.append(vm.acc)

    vm = VirtualMachine(input_handler=lambda: next(input_values), output_handler=output)
    # Los ejemplos deben funcionar solos, sin inyectar TEST_CASES['data'].
    vm.load_source(code, case["file"])
    initial_data = dict(DeviceControllers.parse_program(code).initial_data)
    steps = []
    while not vm.halted:
        if vm.cycles >= 10000:
            raise RuntimeError(f"El caso {case['name']} no finaliza en 10000 instrucciones.")
        before = vm.get_state_summary()
        previous_memory = vm.memory.cells.copy()
        vm.step()
        steps.append({
            "paso": vm.cycles,
            "antes": before,
            "despues": vm.get_state_summary(),
            "fases": dict(vm.last_trace),
            "cambios_memoria": [
                {"direccion": address, "antes": old, "despues": new}
                for address, (old, new) in enumerate(zip(previous_memory, vm.memory.cells))
                if old != new
            ],
        })
    correct = (
        vm.acc == expected_acc and vm.halted
        and all(vm.memory.read(address) == value for address, value in expected_memory.items())
        and printer == [expected_acc]
    )
    evidence = {
        "programa": case["name"], "archivo": "examples/" + case["file"],
        "codigo": code, "entradas": inputs, "datos_iniciales": initial_data,
        "esperado": {"acc": expected_acc, "memoria": expected_memory, "impresora": [expected_acc]},
        "resultado": "CORRECTO" if correct else "FALLA",
        "estado": vm.get_state_summary(),
        "memoria": [str(value) if isinstance(value, Instruction) else value for value in vm.memory.cells],
        "impresora": printer, "traza": vm.execution_log,
        "fases_ultima_instruccion": vm.last_trace, "pasos": steps,
    }
    write_json(folder / (slug + ".json"), evidence)
    # Ejemplos del mismo exportador que utilizan la GUI y la consola.
    snapshot = build_evidence(vm, name=case['name'])
    for extension in ('html', 'csv', 'json'):
        save_report(snapshot, ROOT / 'output' / 'reportes' / f'{slug}.{extension}')
    return evidence


def capture_errors(folder):
    cases = (
        ("Instrucción inexistente", "MULT 10\nHALT", InvalidInstructionException),
        ("Programa sin HALT", "LOAD 10\nOUTPUT", InvalidInstructionException),
        ("Dirección superior inválida", "LOAD 100\nHALT", MemoryOutOfBoundsException),
        ("Dirección negativa", "STORE -1\nHALT", MemoryOutOfBoundsException),
        ("Error de sintaxis", "LOAD 10 20\nHALT", InvalidInstructionException),
        ("Registro no válido", "LOAD R9\nHALT", InvalidInstructionException),
        ("Registro usado como dirección", "LOAD ACC\nHALT", InvalidInstructionException),
        ("DATA sobre código", "DATA 0 5\nHALT", InvalidInstructionException),
        ("DATA duplicado", "DATA 90 1\nDATA 90 2\nHALT", InvalidInstructionException),
    )
    results = []
    for name, code, expected in cases:
        vm = VirtualMachine(output_handler=lambda _: None)
        try:
            vm.load_source(code)
        except Exception as exc:
            correct = isinstance(exc, expected)
            detail = str(exc)
        else:
            correct, detail = False, "No se detectó el error."
        results.append({"prueba": name, "codigo": code, "excepcion_esperada": expected.__name__,
                        "estado": "CORRECTO" if correct else "FALLA", "mensaje": detail})
    write_json(folder / "errores_carga.json", results)

    vm = VirtualMachine(output_handler=lambda _: None)
    vm.load_source("LOAD 0\nHALT", "Error controlado: código leído como dato")
    try:
        vm.step()
    except InvalidInstructionException:
        pass
    console = io.StringIO()
    with redirect_stdout(console):
        vm.print_state()
    evidence = {"codigo": "LOAD 0\nHALT", "estado": vm.get_state_summary(),
                "salida_consola": console.getvalue(), "fases": vm.last_trace}
    evidence["resultado"] = "CORRECTO" if vm.error and vm.pc == 0 and "ERROR" in console.getvalue() else "FALLA"
    write_json(folder / "error_ejecucion.json", evidence)
    for extension in ('html', 'json'):
        save_report(build_evidence(vm), ROOT / 'output' / 'reportes' / f'error_ejecucion.{extension}')
    return results, evidence


def run_check(name, args, folder, timeout=120):
    command = [sys.executable, *args]
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    try:
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True,
                                encoding="utf-8", errors="replace", timeout=timeout, check=False)
        content = result.stdout + result.stderr
        success = result.returncode == 0
        code = result.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        content = (stdout.decode("utf-8", "replace") if isinstance(stdout, bytes) else stdout)
        content += (stderr.decode("utf-8", "replace") if isinstance(stderr, bytes) else stderr)
        content += f"\nTiempo de espera agotado: {timeout} segundos.\n"
        success, code = False, None
    (folder / (name + ".txt")).write_text(content, encoding="utf-8")
    return {"comando": "python " + " ".join(args), "estado": "CORRECTO" if success else "FALLA",
            "codigo_salida": code, "salida": content}


def make_markdown(stamp, cases, errors, execution_error, checks):
    lines = ["# Evidencias de pruebas", "", f"Validación ejecutada: {stamp} (America/Managua).", "",
             "Este archivo se genera con resultados obtenidos al ejecutar el código actual. "
             "Los JSON conservan programas, entradas, registros, memoria, salida y fases de cada paso.", "",
             "## Reproducción", "", "```powershell", "python scripts/generar_evidencias.py --incluir-gui", "```", "",
             "Sin `--incluir-gui` se ejecutan las pruebas de consola y se indica que la GUI no fue comprobada en esa ejecución.", "",
             "## Resultados funcionales", "", "| Prueba | Esperado | Obtenido | Estado |", "|---|---|---|---|"]
    for case in cases:
        wanted = f"ACC={case['esperado']['acc']}; impresora={case['esperado']['impresora']}"
        actual = f"ACC={case['estado']['acc']}; PC={case['estado']['pc']}; HALT={case['estado']['halted']}"
        for address, value in case["esperado"]["memoria"].items():
            wanted += f"; Mem[{address}]={value}"
            actual += f"; Mem[{address}]={case['memoria'][address]}"
        lines.append(f"| {case['programa']} | {wanted} | {actual} | {case['resultado']} |")
    lines += ["", "Los seis ejemplos se cargan desde su propio texto, con DATA cuando corresponde; "
              "no se agregan datos desde el catálogo de casos. Entrada del sexto programa: 7.", "",
              "## Traza numérica de suma", "", "| Paso | Instrucción | PC antes | PC después | ACC antes | ACC después | Mem[20] |",
              "|---|---|---|---|---|---|---|"]
    memory_value = 0
    for step in cases[0]["pasos"]:
        for change in step["cambios_memoria"]:
            if change["direccion"] == 20:
                memory_value = change["despues"]
        lines.append(f"| {step['paso']} | {step['despues']['ir']} | {step['antes']['pc']} | "
                     f"{step['despues']['pc']} | {step['antes']['acc']} | {step['despues']['acc']} | {memory_value} |")
    lines += ["", "## Validaciones de carga", "", "| Situación | Programa | Estado |", "|---|---|---|"]
    for error in errors:
        lines.append(f"| {error['prueba']} | `{error['codigo'].replace(chr(10), '; ')}` | {error['estado']} |")
    lines += ["", "Los mensajes completos y el tipo de excepción están en `docs/evidencias/errores_carga.json`.", "",
              "## Error de ejecución y estado de consola", "",
              "El programa `LOAD 0; HALT` intenta leer código como un número. La VM conserva PC=0, "
              "registra la causa y exige reinicio. La consola informa ERROR.", "", "```text",
              execution_error["salida_consola"].strip(), "```", "", f"Resultado: {execution_error['resultado']}."]
    for name, check in checks.items():
        title = {"verificador": "Verificador de entrega", "regresiones": "Pruebas de regresión", "gui": "Interfaz gráfica"}[name]
        lines += ["", "## " + title, "", f"Comando: `{check['comando']}`.", "", f"Estado: {check['estado']}."]
        if check.get("salida"):
            lines += ["", "```text", check["salida"].strip(), "```"]
    lines += ["", "## Archivos de evidencia", "",
              "- `output/reportes/`: reportes HTML imprimibles, CSV para Excel y JSON completos de los seis casos; también se conserva el error de ejecución.",
              "- `docs/evidencias/suma.json`, `resta.json` y `almacenamiento.json`.",
              "- `docs/evidencias/condicional.json`, `bucle.json` y `entrada_salida.json`.",
              "- `docs/evidencias/errores_carga.json` y `error_ejecucion.json`.",
              "- `docs/evidencias/resumen.json`: fecha, resultados y comandos de esta validación.",
              "- `docs/evidencias/verificador.txt` y `regresiones.txt`: salidas completas.",
              "- `docs/evidencias/gui.txt`: resultado de GUI; indica si se omitió.", "",
              "La prueba gráfica comprueba controles reales de Tkinter. La revisión visual del PDF "
              "y el ensayo oral de la defensa se realizan por separado.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--incluir-gui", action="store_true", help="Abre Tkinter brevemente para probar la interfaz.")
    args = parser.parse_args()
    folder = ROOT / "docs" / "evidencias"
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone(timedelta(hours=-6))).isoformat(timespec="seconds")
    cases = [capture_case(*case, folder) for case in CASES]
    errors, execution_error = capture_errors(folder)
    checks = {
        "verificador": run_check("verificador", ["-m", "tests.verificar_entrega"], folder),
        "regresiones": run_check("regresiones", ["-m", "unittest", "discover", "-s", "tests", "-v"], folder),
    }
    if args.incluir_gui:
        checks["gui"] = run_check("gui", ["-m", "tests.verificar_gui"], folder)
    else:
        checks["gui"] = {"comando": "python -m tests.verificar_gui", "estado": "NO EJECUTADA", "salida": ""}
        (folder / "gui.txt").write_text("GUI no ejecutada en esta validación.\n", encoding="utf-8")
    regression_count = re.search(r"Ran (\d+) tests?", checks["regresiones"]["salida"])
    success = all(case["resultado"] == "CORRECTO" for case in cases)
    success = success and all(error["estado"] == "CORRECTO" for error in errors)
    success = success and execution_error["resultado"] == "CORRECTO"
    success = success and all(check["estado"] in ("CORRECTO", "NO EJECUTADA") for check in checks.values())
    summary = {"fecha": stamp, "zona_horaria": "America/Managua", "estado": "CORRECTO" if success else "FALLA",
               "casos_funcionales": len(cases), "errores_carga": len(errors),
               "pruebas_regresion": int(regression_count.group(1)) if regression_count else None,
               "resultados_funcionales": [{"prueba": case["programa"], "estado": case["resultado"]} for case in cases],
               "comprobaciones": checks}
    write_json(folder / "resumen.json", summary)
    (ROOT / "docs" / "EVIDENCIAS_PRUEBAS.md").write_text(
        make_markdown(stamp, cases, errors, execution_error, checks), encoding="utf-8")
    print(f"Evidencias: {folder.relative_to(ROOT)}")
    print(f"Casos: {len(cases)}; errores de carga: {len(errors)}; pruebas automatizadas: {summary['pruebas_regresion']}; "
          f"GUI: {checks['gui']['estado']}; resultado: {summary['estado']}")
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
