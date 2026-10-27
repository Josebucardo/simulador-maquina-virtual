"""
Simulador de Máquina Virtual Simple - Arquitectura de Sistemas Operativos
Grupo 13
Lenguaje: Python 3
Incluye: Memoria virtual, Registros (PC, IR, ACC, FLAGS), Ciclo Fetch-Decode-Execute,
         Controladores de dispositivos (Teclado, Impresora, Disco), Modo Consola y Modo GUI (Tkinter).
"""

import os
from typing import Optional

__all__ = [
    'BASE_DIR', 'EXAMPLES_DIR', 'INSTRUCTION_SPECS', 'TEST_CASES',
    'MemoryOutOfBoundsException', 'InvalidInstructionException', 'InputCancelled',
    'ExecutionFault', 'Program', 'Instruction', 'Memory', 'DeviceControllers',
    'KeyboardController', 'PrinterController', 'DiskController', 'VirtualMachine',
    'load_test_case',
]

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EXAMPLES_DIR = os.path.join(BASE_DIR, "examples")

INSTRUCTION_SPECS = {
    "LOAD": True,
    "STORE": True,
    "ADD": True,
    "SUB": True,
    "JMP": True,
    "JZ": True,
    "JNZ": True,
    "INPUT": False,
    "OUTPUT": False,
    "HALT": False,
}

TEST_CASES = {
    "1": {
        "name": "Suma",
        "file": "test1_suma.asm",
        "data": {10: 10, 11: 20},
        "expected": "ACC = 30 y Mem[20] = 30",
    },
    "2": {
        "name": "Resta",
        "file": "test2_resta.asm",
        "data": {10: 50, 11: 30},
        "expected": "ACC = 20 y Mem[20] = 20",
    },
    "3": {
        "name": "Almacenamiento",
        "file": "test3_almacenamiento.asm",
        "data": {10: 30},
        "expected": "Mem[20] = 30",
    },
    "4": {
        "name": "Condicional JZ",
        "file": "test4_condicional.asm",
        "data": {10: 20, 11: 20, 12: 111, 13: 999},
        "expected": "ACC = 111 porque el salto JZ se cumple",
    },
    "5": {
        "name": "Bucle con JNZ",
        "file": "test5_bucle.asm",
        "data": {50: 3, 51: 1, 52: 0},
        "expected": "ACC = 6 y Mem[53] = 6",
    },
    "6": {
        "name": "Entrada y salida",
        "file": "test6_entrada_salida.asm",
        "data": {},
        "expected": "Con entrada 7, ACC = 7 y Mem[20] = 7",
    },
}

class MemoryOutOfBoundsException(Exception):
    pass

class InvalidInstructionException(Exception):
    pass

class InputCancelled(Exception):
    """La entrada se canceló; la instrucción puede reintentarse."""


class ExecutionFault(Exception):
    """La VM requiere reinicio después de un error."""


class Program(list):
    """Instrucciones y datos declarados sin consumir direcciones de código."""
    def __init__(self, source=None):
        super().__init__()
        self.initial_data = {}
        self.source = source


class Instruction:
    def __init__(self, opcode: str, operand: Optional[int] = None):
        if not isinstance(opcode, str):
            raise InvalidInstructionException("El código de operación debe ser texto.")
        self.opcode = opcode.upper()
        self.operand = operand

    def validate(self):
        if not isinstance(self.opcode, str) or self.opcode not in INSTRUCTION_SPECS:
            raise InvalidInstructionException(f"Instrucción inexistente '{self.opcode}'.")
        if INSTRUCTION_SPECS[self.opcode]:
            if type(self.operand) is not int:
                raise InvalidInstructionException(f"'{self.opcode}' requiere una dirección de memoria entera.")
            Memory()._check_bounds(self.operand)
        elif self.operand is not None:
            raise InvalidInstructionException(f"'{self.opcode}' no acepta operandos.")

    def __str__(self):
        return f"{self.opcode} {self.operand}" if self.operand is not None else self.opcode

    def __repr__(self):
        return self.__str__()


class Memory:
    SIZE = 100

    def __init__(self):
        self.cells = [0] * self.SIZE

    def _check_bounds(self, address: int):
        if type(address) is not int:
            raise MemoryOutOfBoundsException(f"Dirección inválida '{address}': debe ser un entero entre 0 y {self.SIZE - 1}.")
        if address < 0 or address >= self.SIZE:
            raise MemoryOutOfBoundsException(
                f"Acceso ilegal a dirección [{address}]. Rango permitido: 0 a {self.SIZE - 1}."
            )

    def read(self, address: int):
        self._check_bounds(address)
        return self.cells[address]

    def read_int(self, address: int) -> int:
        val = self.read(address)
        if type(val) is int:
            return val
        raise InvalidInstructionException(f"La celda [{address}] contiene '{val}', no un dato numérico entero.")

    def write(self, address: int, value):
        self._check_bounds(address)
        if isinstance(value, Instruction):
            value.validate()
        elif type(value) is not int:
            raise InvalidInstructionException("La memoria solo admite instrucciones o números enteros.")
        self.cells[address] = value

    def clear(self):
        self.cells = [0] * self.SIZE


class DeviceControllers:
    """Controladores simulados de dispositivos E/S y almacenamiento secundario."""
    
    @staticmethod
    def keyboard_input(prompt_fn=None) -> int:
        if prompt_fn:
            return prompt_fn()
        while True:
            val = input("[DISPOSITIVO TECLADO] Ingrese un número entero: ").strip()
            try:
                return int(val)
            except ValueError:
                print("Valor inválido. Intente nuevamente.")

    @staticmethod
    def printer_output(data: int, output_fn=None):
        msg = f"[DISPOSITIVO IMPRESORA] Salida reportada: ACC = {data}"
        if output_fn:
            output_fn(msg)
        else:
            print(msg)

    @staticmethod
    def read_program_source(filepath: str) -> str:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Error en Controlador de Disco: Archivo '{filepath}' no encontrado.")
        
        with open(filepath, "r", encoding="utf-8-sig") as f:
            return f.read()

    @staticmethod
    def load_program_from_disk(filepath: str):
        return DeviceControllers.parse_program(DiskController.read_source(filepath))

    @staticmethod
    def parse_program(source: str):
        if not isinstance(source, str):
            raise InvalidInstructionException("El código fuente ASM debe ser texto.")
        instructions = Program(source)
        for line_num, line in enumerate(source.lstrip('\ufeff').splitlines(), 1):
            clean_line = DeviceControllers._strip_comments(line)
            if not clean_line or clean_line.startswith("#") or clean_line.startswith("//"):
                continue
            
            parts = clean_line.split()
            opcode = parts[0].upper()
            operand = None

            if opcode == "DATA":
                if len(parts) != 3:
                    raise InvalidInstructionException(f"Línea {line_num}: use DATA dirección valor.")
                try:
                    address, value = int(parts[1]), int(parts[2])
                except ValueError:
                    raise InvalidInstructionException(f"Línea {line_num}: DATA requiere dos enteros.")
                Memory()._check_bounds(address)
                if address in instructions.initial_data:
                    raise InvalidInstructionException(f"Línea {line_num}: DATA duplicado en {address}.")
                instructions.initial_data[address] = value
                continue

            if opcode not in INSTRUCTION_SPECS:
                raise InvalidInstructionException(
                    f"Línea {line_num}: Instrucción inexistente '{opcode}'."
                )

            requires_operand = INSTRUCTION_SPECS[opcode]
            if requires_operand and len(parts) == 1:
                raise InvalidInstructionException(
                    f"Línea {line_num}: La instrucción '{opcode}' requiere una dirección de memoria."
                )
            if not requires_operand and len(parts) > 1:
                raise InvalidInstructionException(
                    f"Línea {line_num}: La instrucción '{opcode}' no acepta operandos."
                )
            if len(parts) > 2:
                raise InvalidInstructionException(
                    f"Línea {line_num}: Error de sintaxis. Se esperaba como máximo un operando."
                )

            if requires_operand:
                try:
                    operand = int(parts[1])
                except ValueError:
                    register = parts[1].upper()
                    if register in {"PC", "IR", "ACC", "FLAGS", "Z", "N"} or (
                        register.startswith("R") and register[1:].isdigit()
                    ):
                        raise InvalidInstructionException(
                            f"Línea {line_num}: Registro no válido como operando '{parts[1]}'. "
                            f"ACC se usa implícitamente; '{opcode}' requiere una dirección de memoria entera."
                        )
                    raise InvalidInstructionException(
                        f"Línea {line_num}: El operando '{parts[1]}' debe ser un número entero."
                    )
                if operand < 0 or operand >= Memory.SIZE:
                    raise MemoryOutOfBoundsException(
                        f"Línea {line_num}: Dirección [{operand}] fuera del rango 0 a {Memory.SIZE - 1}."
                    )
            instructions.append(Instruction(opcode, operand))
        return instructions

    @staticmethod
    def _strip_comments(line: str) -> str:
        clean_line = line.strip()
        for marker in ("#", "//"):
            marker_pos = clean_line.find(marker)
            if marker_pos != -1:
                clean_line = clean_line[:marker_pos].strip()
        return clean_line


class KeyboardController:
    read = staticmethod(DeviceControllers.keyboard_input)


class PrinterController:
    write = staticmethod(DeviceControllers.printer_output)


class DiskController:
    read_source = staticmethod(DeviceControllers.read_program_source)
    load = staticmethod(DeviceControllers.load_program_from_disk)


class VirtualMachine:
    def __init__(self, input_handler=None, output_handler=None):
        self.memory = Memory()
        self.pc = 0
        self.ir = None
        self.acc = 0
        self.flag_z = True
        self.flag_n = False
        self.halted = False
        self.input_handler = input_handler
        self.output_handler = output_handler
        self.execution_log = []
        self.error = None
        self.cycles = 0
        self.last_trace = {}
        self.program_source = ""
        self.program_name = ""
        self.initial_data = {}
        self.input_values = []
        self.outputs = []
        self.history = []
        self.manual_edits = []
        self._loaded_instructions = []

    def reset(self):
        self.pc = 0
        self.ir = None
        self.acc = 0
        self.flag_z = True
        self.flag_n = False
        self.halted = False
        self.memory.clear()
        self.execution_log.clear()
        self.error = None
        self.cycles = 0
        self.last_trace = {}
        self.program_source = ""
        self.program_name = ""
        self.initial_data = {}
        self.input_values.clear()
        self.outputs.clear()
        self.history.clear()
        self.manual_edits.clear()
        self._loaded_instructions = []

    @property
    def program_loaded(self):
        return bool(self._loaded_instructions)

    def restart(self):
        """Restaura el programa cargado y los datos iniciales; limpia su ejecución."""
        if not self.program_loaded:
            raise InvalidInstructionException("No hay un programa cargado. Cargue un archivo o un ejemplo.")
        program = Program(self.program_source)
        program.extend(self._loaded_instructions)
        program.initial_data = dict(self.initial_data)
        self.load_instructions(program, self.program_name)

    def edit_data(self, address, value):
        """Edita datos pausados; los cambios anteriores al primer paso son iniciales."""
        if self.error:
            raise ExecutionFault(f"Reinicie la máquina antes de editar datos: {self.error}")
        self.memory._check_bounds(address)
        if isinstance(self.memory.read(address), Instruction):
            raise InvalidInstructionException("La celda contiene código. Modifique el programa ASM y vuelva a cargarlo.")
        if type(value) is not int:
            raise InvalidInstructionException("El dato debe ser un número entero.")
        before = self.memory.read(address)
        self.memory.write(address, value)
        if self.program_loaded and self.cycles == 0:
            self.initial_data[address] = value
        self.manual_edits.append(dict(direccion=address, antes=before, despues=value, ciclo=self.cycles))

    def log(self, message: str):
        self.execution_log.append(message)
        if self.output_handler:
            self.output_handler(message)
        else:
            print(message)

    def load_program(self, filepath: str):
        instructions = DiskController.load(filepath)
        self.load_instructions(instructions, filepath)

    def load_source(self, source: str, name="Editor"):
        self.load_instructions(DeviceControllers.parse_program(source), name)

    def load_instructions(self, instructions, filepath="Editor", *, source=None):
        """Valida el programa completo antes de reemplazar el estado existente."""
        initial_data = getattr(instructions, "initial_data", {})
        if not isinstance(initial_data, dict):
            raise InvalidInstructionException("Los datos iniciales deben ser un diccionario de direcciones y enteros.")
        initial_data = dict(initial_data)
        if source is None:
            source = getattr(instructions, "source", None)
        if source is not None and not isinstance(source, str):
            raise InvalidInstructionException("El código fuente ASM debe ser texto.")
        try:
            name = os.fspath(filepath)
        except TypeError:
            raise InvalidInstructionException("El nombre del programa debe ser texto.") from None
        if not isinstance(name, str):
            raise InvalidInstructionException("El nombre del programa debe ser texto.")
        try:
            instructions = list(instructions)
        except TypeError:
            raise InvalidInstructionException("El programa debe contener una lista de instrucciones.") from None
        if not instructions:
            raise InvalidInstructionException("El programa está vacío o solo contiene comentarios.")

        if len(instructions) > Memory.SIZE:
            raise MemoryOutOfBoundsException(
                f"El programa tiene {len(instructions)} instrucciones y la memoria solo permite {Memory.SIZE}."
            )
        
        for address, inst in enumerate(instructions):
            if not isinstance(inst, Instruction):
                raise InvalidInstructionException(f"La posición {address} no contiene una instrucción válida.")
            inst.validate()
        has_halt = any(inst.opcode == "HALT" for inst in instructions)
        if not has_halt:
            raise InvalidInstructionException(
                "El programa no contiene instrucción HALT. La carga fue rechazada: se requiere una terminacion explicita."
            )

        for address, value in initial_data.items():
            self.memory._check_bounds(address)
            if type(value) is not int:
                raise InvalidInstructionException(f"DATA [{address}] requiere un valor entero.")
            if address < len(instructions):
                raise InvalidInstructionException("Una declaración DATA se superpone con el código.")
        # Evita que el llamador altere después los objetos de instrucciones cargados.
        instructions = [Instruction(inst.opcode, inst.operand) for inst in instructions]
        if source is None:
            source = '\n'.join(
                [f"DATA {address} {value}" for address, value in sorted(initial_data.items())]
                + [str(inst) for inst in instructions]
            )

        self.reset()
        for addr, inst in enumerate(instructions):
            self.memory.write(addr, inst)
        for address, value in initial_data.items():
            self.memory.write(address, value)
        self.program_source = source
        self.program_name = name
        self.initial_data = initial_data
        self._loaded_instructions = [Instruction(inst.opcode, inst.operand) for inst in instructions]
        self.log(f"Programa cargado exitosamente desde '{name}'. Total instrucciones: {len(instructions)}.")

    def step(self) -> bool:
        """Ejecuta una instrucción y registra sus tres fases."""
        if self.error:
            raise ExecutionFault(f"Reinicie la máquina: {self.error}")
        if self.halted:
            return False
        if not self.program_loaded:
            raise InvalidInstructionException("No hay un programa cargado. Cargue un archivo o un ejemplo.")
        original_pc = self.pc
        previous_ir = self.ir
        previous_acc = self.acc
        previous_zero = self.flag_z
        previous_negative = self.flag_n
        previous_memory = list(self.memory.cells)
        previous_halted = self.halted
        previous_cycles = self.cycles
        previous_inputs = len(self.input_values)
        previous_outputs = len(self.outputs)
        previous_history = len(self.history)
        self.last_trace = {}
        try:
            raw = self.memory.read(original_pc)
            if not isinstance(raw, Instruction):
                raise InvalidInstructionException(
                    f"FETCH [{original_pc}]: se esperaba una instrucción, se encontró {raw}.")
            self.ir = raw
            self.last_trace["FETCH"] = f"Mem[{original_pc:02d}] -> IR = {raw}"
            raw.validate()
            self.last_trace["DECODE"] = f"Operación {raw.opcode}; operando {raw.operand if raw.operand is not None else 'ninguno'}"
            self.pc = original_pc + 1
            self._execute(raw, original_pc)
            self._update_flags()
            self.cycles += 1
            explanation = self._explain(raw, previous_acc, previous_zero)
            if raw.opcode == "INPUT":
                self.input_values.append(self.acc)
            elif raw.opcode == "OUTPUT":
                self.outputs.append(self.acc)
            self.log(f"\nEXPLICACIÓN · Paso {self.cycles}: {raw}\n{explanation}")
            self.last_trace["EXECUTE"] = f"ACC {previous_acc} -> {self.acc} | PC {original_pc:02d} -> {self.pc:02d} | Z={int(self.flag_z)} N={int(self.flag_n)}"
            for phase, description in self.last_trace.items():
                self.log(f"  {phase}: {description}")
            def cell_value(value):
                return str(value) if isinstance(value, Instruction) else value
            changes = [dict(direccion=address, antes=cell_value(before), despues=cell_value(after))
                       for address, (before, after) in enumerate(zip(previous_memory, self.memory.cells))
                       if before != after]
            self.history.append(dict(
                ciclo=self.cycles, pc_antes=original_pc, pc_despues=self.pc,
                instruccion=str(raw), acc_antes=previous_acc, acc_despues=self.acc,
                z=self.flag_z, n=self.flag_n, cambios_memoria=changes,
                fases=dict(self.last_trace), explicacion=explanation,
            ))
            return not self.halted
        except InputCancelled:
            self.pc, self.ir, self.acc = original_pc, previous_ir, previous_acc
            self.flag_z, self.flag_n = previous_zero, previous_negative
            self.halted, self.cycles = previous_halted, previous_cycles
            self.memory.cells = previous_memory
            del self.input_values[previous_inputs:]
            del self.outputs[previous_outputs:]
            del self.history[previous_history:]
            self.last_trace["EXECUTE"] = "Entrada cancelada. La instrucción sigue pendiente."
            raise
        except Exception as exc:
            self.pc = original_pc
            self.acc = previous_acc
            self.flag_z, self.flag_n = previous_zero, previous_negative
            self.halted, self.cycles = previous_halted, previous_cycles
            self.memory.cells = previous_memory
            del self.input_values[previous_inputs:]
            del self.outputs[previous_outputs:]
            del self.history[previous_history:]
            self.error = str(exc)
            self.last_trace["EXECUTE"] = f"ERROR: {exc}"
            raise

    def _explain(self, instruction, previous_acc, previous_zero):
        """Describe la operación completada usando los valores reales del paso."""
        op, address = instruction.opcode, instruction.operand
        if op == "LOAD":
            text = (f"Buscamos el número guardado en la casilla {address} de la memoria: {self.acc}. "
                    f"Lo copiamos al acumulador (ACC), que es donde trabajamos con los números. "
                    f"Antes tenía {previous_acc}; ahora tiene {self.acc}. La memoria conserva su valor.")
        elif op == "STORE":
            text = (f"Guardamos el número {self.acc} del acumulador en la casilla {address} de la memoria, "
                    "reemplazando lo que había allí. El acumulador conserva su número.")
        elif op in ("ADD", "SUB"):
            number = self.memory.read_int(address)
            action, symbol = ("Sumamos", "+") if op == "ADD" else ("Restamos", "-")
            text = (f"{action} el número {number}, guardado en la casilla {address}, "
                    f"al número que teníamos en el acumulador. La cuenta es: "
                    f"{previous_acc} {symbol} ({number}) = {self.acc}. El resultado queda en el acumulador.")
        elif op == "JMP":
            text = (f"Cambiamos el orden del programa: la próxima instrucción será la de la casilla {address}. "
                    "Este salto se realiza siempre. El acumulador no cambia.")
        elif op in ("JZ", "JNZ"):
            taken = previous_zero if op == "JZ" else not previous_zero
            condition = "cero" if op == "JZ" else "distinto de cero"
            result = "era cero" if previous_zero else "no era cero"
            text = (f"Comprobamos si el resultado anterior es {condition}. "
                    f"El acumulador tenía {previous_acc} y la bandera Z indica que {result}. "
                    + (f"La condición se cumple: saltamos a la casilla {address}." if taken else
                       f"La condición no se cumple: seguimos con la casilla {self.pc}.")
                    + " El acumulador no cambia.")
        elif op == "INPUT":
            text = f"Leímos el número {self.acc} que escribió el usuario y lo colocamos en el acumulador para poder usarlo en las siguientes operaciones."
        elif op == "OUTPUT":
            text = f"Enviamos el número {self.acc} del acumulador a la impresora virtual para mostrar el resultado. El número permanece en el acumulador."
        else:  # HALT
            return f"Llegamos al final del programa. La máquina se detiene y deja de ejecutar instrucciones. El acumulador terminó con {self.acc}. Puedes revisar la memoria y los resultados o reiniciar para repetir."
        return text + f"\nLa próxima instrucción está en la casilla {self.pc} (eso indica el contador de programa, PC)."

    def _execute(self, instruction: Instruction, original_pc: int):
        op = instruction.opcode
        arg = instruction.operand

        if op == "LOAD":
            arg = self._require_operand(op, arg)
            self.acc = self.memory.read_int(arg)
            self.log(f"Paso PC={original_pc:02d}: LOAD Mem[{arg}] -> ACC={self.acc}")

        elif op == "STORE":
            arg = self._require_operand(op, arg)
            self.memory.write(arg, self.acc)
            self.log(f"Paso PC={original_pc:02d}: STORE ACC={self.acc} -> Mem[{arg}]")

        elif op == "ADD":
            arg = self._require_operand(op, arg)
            val = self.memory.read_int(arg)
            prev = self.acc
            self.acc += val
            self.log(f"Paso PC={original_pc:02d}: ADD Mem[{arg}] ({val}) -> ACC={prev} + {val} = {self.acc}")

        elif op == "SUB":
            arg = self._require_operand(op, arg)
            val = self.memory.read_int(arg)
            prev = self.acc
            self.acc -= val
            self.log(f"Paso PC={original_pc:02d}: SUB Mem[{arg}] ({val}) -> ACC={prev} - {val} = {self.acc}")

        elif op == "JMP":
            arg = self._require_operand(op, arg)
            self.memory._check_bounds(arg)
            self.pc = arg
            self.log(f"Paso PC={original_pc:02d}: JMP a dirección {arg:02d} -> Nuevo PC={self.pc:02d}")

        elif op == "JZ":
            arg = self._require_operand(op, arg)
            self.memory._check_bounds(arg)
            if self.flag_z:
                self.pc = arg
                self.log(f"Paso PC={original_pc:02d}: JZ se cumple (Z=1) -> Salto a {arg:02d}")
            else:
                self.log(f"Paso PC={original_pc:02d}: JZ no se cumple (Z=0) -> Continúa a {self.pc:02d}")

        elif op == "JNZ":
            arg = self._require_operand(op, arg)
            self.memory._check_bounds(arg)
            if not self.flag_z:
                self.pc = arg
                self.log(f"Paso PC={original_pc:02d}: JNZ se cumple (Z=0) -> Salto a {arg:02d}")
            else:
                self.log(f"Paso PC={original_pc:02d}: JNZ no se cumple (Z=1) -> Continúa a {self.pc:02d}")

        elif op == "INPUT":
            val = KeyboardController.read(self.input_handler)
            if type(val) is not int:
                raise InvalidInstructionException("INPUT requiere un entero.")
            self.acc = val
            self.log(f"Paso PC={original_pc:02d}: INPUT teclado -> ACC={self.acc}")

        elif op == "OUTPUT":
            PrinterController.write(self.acc, self.output_handler)
            self.log(f"Paso PC={original_pc:02d}: OUTPUT impreso -> {self.acc}")

        elif op == "HALT":
            self.halted = True
            self.log(f"Paso PC={original_pc:02d}: HALT -> Finalización de ejecución.")

        else:
            raise InvalidInstructionException(f"Error DECODE: Instrucción no reconocida '{op}' en PC={original_pc}")

    def _require_operand(self, opcode: str, operand: Optional[int]) -> int:
        if type(operand) is not int:
            raise InvalidInstructionException(f"Error sintaxis: '{opcode}' requiere operando de dirección.")
        self.memory._check_bounds(operand)
        return operand

    def _update_flags(self):
        self.flag_z = (self.acc == 0)
        self.flag_n = (self.acc < 0)

    def run_all(self, max_cycles=10000):
        if type(max_cycles) is not int or max_cycles <= 0:
            raise ValueError("El límite de ciclos debe ser un entero positivo.")
        if not self.program_loaded:
            raise InvalidInstructionException("No hay un programa cargado. Cargue un archivo o un ejemplo.")
        while not self.halted:
            if self.error:
                raise ExecutionFault(f"Reinicie la máquina: {self.error}")
            if self.cycles >= max_cycles:
                self.error = "Límite de ciclos excedido: posible bucle infinito."
                raise TimeoutError(self.error)
            self.step()

    def get_state_summary(self):
        return {
            "pc": self.pc,
            "ir": str(self.ir) if self.ir else "NINGUNO",
            "acc": self.acc,
            "flag_z": self.flag_z,
            "flag_n": self.flag_n,
            "halted": self.halted,
            "error": self.error,
            "cycles": self.cycles,
            "program_loaded": self.program_loaded,
        }

    def print_state(self):
        s = self.get_state_summary()
        print("\n" + "=" * 52)
        print("ESTADO DE LA MÁQUINA VIRTUAL (GRUPO 13)")
        print("=" * 52)
        print(f"  PC  (Contador Programa)   : {s['pc']:02d}")
        print(f"  IR  (Registro Instrucción): {s['ir']}")
        print(f"  ACC (Acumulador)          : {s['acc']}")
        print(f"  FLAGS                     : [Z={int(s['flag_z'])}, N={int(s['flag_n'])}]")
        status = ('ERROR' if s['error'] else 'HALTED (Detenido)' if s['halted'] else
                  'SIN PROGRAMA' if not self.program_loaded else 'LISTA' if not self.cycles else 'PAUSADA')
        print(f"  ESTADO                    : {status}")
        print(f"  CICLOS                    : {self.cycles}")
        if s['error']:
            print(f"  CAUSA                     : {s['error']}")
        print("=" * 52)


def load_test_case(vm: VirtualMachine, option: str):
    case = TEST_CASES.get(str(option))
    if not case:
        raise ValueError("Caso de prueba no válido.")

    filepath = os.path.join(EXAMPLES_DIR, case["file"])
    vm.load_program(filepath)
    return case


