"""
Simulador de Máquina Virtual Simple - Arquitectura de Sistemas Operativos
Grupo 13
Lenguaje: Python 3
Incluye: Memoria virtual, Registros (PC, IR, ACC, FLAGS), Ciclo Fetch-Decode-Execute,
         Controladores de dispositivos (Teclado, Impresora, Disco), Modo Consola y Modo GUI (Tkinter).
"""

import sys
import os
from typing import Optional

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
    def __init__(self):
        super().__init__()
        self.initial_data = {}


class Instruction:
    def __init__(self, opcode: str, operand: Optional[int] = None):
        self.opcode = opcode.upper()
        self.operand = operand

    def __str__(self):
        return f"{self.opcode} {self.operand}" if self.operand is not None else self.opcode

    def __repr__(self):
        return self.__str__()


class Memory:
    SIZE = 100

    def __init__(self):
        self.cells = [0] * self.SIZE

    def _check_bounds(self, address: int):
        if address < 0 or address >= self.SIZE:
            raise MemoryOutOfBoundsException(
                f"Acceso ilegal a dirección [{address}]. Rango permitido: 0 a {self.SIZE - 1}."
            )

    def read(self, address: int):
        self._check_bounds(address)
        return self.cells[address]

    def read_int(self, address: int) -> int:
        val = self.read(address)
        if isinstance(val, int):
            return val
        raise InvalidInstructionException(f"La celda [{address}] contiene una instrucción ('{val}'), no un dato numérico.")

    def write(self, address: int, value):
        self._check_bounds(address)
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
    def load_program_from_disk(filepath: str):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Error en Controlador de Disco: Archivo '{filepath}' no encontrado.")
        
        with open(filepath, "r", encoding="utf-8-sig") as f:
            return DeviceControllers.parse_program(f.read())

    @staticmethod
    def parse_program(source: str):
        instructions = Program()
        for line_num, line in enumerate(source.splitlines(), 1):
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

    def load_instructions(self, instructions, filepath="Editor"):
        if not instructions:
            raise InvalidInstructionException("El programa está vacío o solo contiene comentarios.")

        if len(instructions) > Memory.SIZE:
            raise MemoryOutOfBoundsException(
                f"El programa tiene {len(instructions)} instrucciones y la memoria solo permite {Memory.SIZE}."
            )
        
        has_halt = any(inst.opcode == "HALT" for inst in instructions)
        if not has_halt:
            raise InvalidInstructionException(
                "El programa no contiene instrucción HALT. La carga fue rechazada: se requiere una terminacion explicita."
            )

        initial_data = getattr(instructions, "initial_data", {})
        if any(address < len(instructions) for address in initial_data):
            raise InvalidInstructionException("Una declaración DATA se superpone con el código.")

        self.reset()
        for addr, inst in enumerate(instructions):
            self.memory.write(addr, inst)
        for address, value in initial_data.items():
            self.memory.write(address, value)
        self.log(f"Programa cargado exitosamente desde '{filepath}'. Total instrucciones: {len(instructions)}.")

    def step(self) -> bool:
        """Ejecuta una instrucción y registra sus tres fases."""
        if self.error:
            raise ExecutionFault(f"Reinicie la máquina: {self.error}")
        if self.halted:
            return False
        original_pc = self.pc
        previous_ir = self.ir
        previous_acc = self.acc
        previous_zero = self.flag_z
        self.last_trace = {}
        try:
            raw = self.memory.read(original_pc)
            if not isinstance(raw, Instruction):
                raise InvalidInstructionException(
                    f"FETCH [{original_pc}]: se esperaba una instrucción, se encontró {raw}.")
            self.ir = raw
            self.last_trace["FETCH"] = f"Mem[{original_pc:02d}] -> IR = {raw}"
            self.last_trace["DECODE"] = f"Operación {raw.opcode}; operando {raw.operand if raw.operand is not None else 'ninguno'}"
            self.pc = original_pc + 1
            self._execute(raw, original_pc)
            self._update_flags()
            self.cycles += 1
            explanation = self._explain(raw, previous_acc, previous_zero)
            self.log(f"\nEXPLICACIÓN · Paso {self.cycles}: {raw}\n{explanation}")
            self.last_trace["EXECUTE"] = f"ACC {previous_acc} -> {self.acc} | PC {original_pc:02d} -> {self.pc:02d} | Z={int(self.flag_z)} N={int(self.flag_n)}"
            for phase, description in self.last_trace.items():
                self.log(f"  {phase}: {description}")
            return not self.halted
        except InputCancelled:
            self.pc, self.ir = original_pc, previous_ir
            self.last_trace["EXECUTE"] = "Entrada cancelada. La instrucción sigue pendiente."
            raise
        except Exception as exc:
            self.pc = original_pc
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
        if operand is None:
            raise InvalidInstructionException(f"Error sintaxis: '{opcode}' requiere operando de dirección.")
        return operand

    def _update_flags(self):
        self.flag_z = (self.acc == 0)
        self.flag_n = (self.acc < 0)

    def run_all(self, max_cycles=10000):
        if type(max_cycles) is not int or max_cycles <= 0:
            raise ValueError("El límite de ciclos debe ser un entero positivo.")
        cycles = 0
        while not self.halted:
            if cycles >= max_cycles:
                self.error = "Límite de ciclos excedido: posible bucle infinito."
                raise TimeoutError(self.error)
            self.step()
            cycles += 1

    def get_state_summary(self):
        return {
            "pc": self.pc,
            "ir": str(self.ir) if self.ir else "NINGUNO",
            "acc": self.acc,
            "flag_z": self.flag_z,
            "flag_n": self.flag_n,
            "halted": self.halted,
            "error": self.error,
            "cycles": self.cycles
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
        print(f"  ESTADO                    : {'HALTED (Detenido)' if s['halted'] else 'EJECUTANDO'}")
        print("=" * 52)


def load_test_case(vm: VirtualMachine, option: str):
    case = TEST_CASES.get(str(option))
    if not case:
        raise ValueError("Caso de prueba no válido.")

    filepath = os.path.join(EXAMPLES_DIR, case["file"])
    vm.load_program(filepath)
    for address, value in case["data"].items():
        vm.memory.write(address, value)
    return case


def run_gui():
    """Laboratorio visual con editor, memoria, dispositivos y trazas."""
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, simpledialog
    import json

    root = tk.Tk()
    root.title("Simulador VM")
    root.geometry("1360x900")
    root.minsize(1040, 740)
    c = dict(bg="#0b1120", panel="#131e32", field="#0e1728", ink="#e7eefb",
             muted="#92a5c4", accent="#54dfbe", blue="#7eabff", line="#273751", red="#ff8599")
    root.configure(bg=c['bg'])
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('.', font=('Segoe UI', 10), background=c['panel'], foreground=c['ink'])
    style.configure('TFrame', background=c['bg'])
    style.configure('Panel.TFrame', background=c['panel'])
    style.configure('TLabel', background=c['panel'], foreground=c['ink'])
    style.configure('Muted.TLabel', foreground=c['muted'], font=('Segoe UI',9))
    style.configure('Title.TLabel', font=('Segoe UI',12,'bold'))
    style.configure('TButton', padding=(13,9), background=c['line'], borderwidth=0)
    style.map('TButton', background=[('active','#365075'),('disabled',c['field'])])
    style.configure('Primary.TButton', background=c['accent'], foreground=c['bg'], font=('Segoe UI',10,'bold'))
    style.map('Primary.TButton', background=[('active','#8defd4'),('disabled','#355d61')])
    style.configure('TCombobox', fieldbackground=c['field'], background=c['line'], padding=7)
    style.map('TCombobox', fieldbackground=[('readonly',c['field'])], foreground=[('readonly',c['ink'])])
    style.configure('Treeview', background=c['field'], fieldbackground=c['field'], foreground=c['ink'], rowheight=26, borderwidth=0, font=('Consolas',10))
    style.configure('Treeview.Heading', background=c['line'], foreground=c['muted'], padding=7)
    style.map('Treeview',background=[('selected','#304d70')],foreground=[('selected','#ffffff')])
    style.configure('TNotebook', background=c['panel'], borderwidth=0)
    style.configure('TNotebook.Tab', background=c['line'], padding=(15,9))
    style.map('TNotebook.Tab',background=[('selected',c['panel'])],foreground=[('selected',c['accent'])])
    root.columnconfigure(0,weight=1)
    root.rowconfigure(4,weight=1)
    source = {'text': None, 'data': {}, 'name': 'Sin programa'}
    scheduler = {'id': None, 'running': False}
    status = tk.StringVar(value='EN ESPERA')
    hint = tk.StringVar(value='Carga un ejemplo o escribe tu programa para comenzar.')
    speed = tk.IntVar(value=300)
    limit = tk.IntVar(value=10000)
    filter_var = tk.StringVar(value='Toda la memoria')
    outputs = []
    metrics = {key:tk.StringVar(value='0') for key in ('PC','IR','ACC','FLAGS','CICLOS')}
    metrics['IR'].set('--')
    phase_vars = {key:tk.StringVar(value='Esperando una instruccion') for key in ('FETCH','DECODE','EXECUTE')}

    def panel(parent, **kwargs):
        return ttk.Frame(parent, style='Panel.TFrame', padding=14, **kwargs)

    header = tk.Frame(root,bg=c['bg'])
    header.grid(row=0,column=0,sticky='ew',padx=22,pady=(18,10))
    header.columnconfigure(0,weight=1)
    tk.Label(header,text='VM STUDIO',font=('Segoe UI',25,'bold'),bg=c['bg'],fg=c['ink']).grid(row=0,column=0,sticky='w')
    tk.Label(header,text='LABORATORIO DE ARQUITECTURA  /  GRUPO 13  /  PYTHON',font=('Segoe UI',9),bg=c['bg'],fg=c['muted']).grid(row=1,column=0,sticky='w')
    tk.Label(header,textvariable=status,font=('Segoe UI',11,'bold'),bg=c['panel'],fg=c['accent'],padx=18,pady=10).grid(row=0,column=1,rowspan=2)

    bar = panel(root)
    bar.grid(row=1,column=0,sticky='ew',padx=22,pady=6)
    bar.columnconfigure(4,weight=1)
    ttk.Button(bar,text='Abrir ASM',command=lambda:open_file()).grid(row=0,column=0,padx=(0,8))
    case_var=tk.StringVar(value='1 - Suma')
    ttk.Combobox(bar,textvariable=case_var,values=[f"{k} - {v['name']}" for k,v in TEST_CASES.items()],state='readonly',width=24).grid(row=0,column=1,padx=8)
    ttk.Button(bar,text='Cargar ejemplo',command=lambda:load_case()).grid(row=0,column=2,padx=8)
    ttk.Button(bar,text='Exportar evidencia',command=lambda:export()).grid(row=0,column=3,padx=8)
    source_label=tk.StringVar(value='SIN PROGRAMA')
    ttk.Label(bar,textvariable=source_label,style='Muted.TLabel').grid(row=0,column=4,sticky='e')

    cards=ttk.Frame(root)
    cards.grid(row=2,column=0,sticky='ew',padx=22,pady=8)
    for col,key in enumerate(metrics):
        cards.columnconfigure(col,weight=1,uniform='metric')
        card=panel(cards)
        card.grid(row=0,column=col,sticky='nsew',padx=(0 if col==0 else 5,0 if col==4 else 5))
        ttk.Label(card,text=key,style='Muted.TLabel').pack(anchor='w')
        tk.Label(card,textvariable=metrics[key],font=('Consolas',20,'bold'),bg=c['panel'],fg=c['accent'] if key=='ACC' else c['ink']).pack(anchor='w',pady=(4,0))
    phases=ttk.Frame(root)
    phases.grid(row=3,column=0,sticky='ew',padx=22,pady=(0,8))
    for col,key in enumerate(phase_vars):
        phases.columnconfigure(col,weight=1,uniform='phase')
        card=panel(phases)
        card.grid(row=0,column=col,sticky='nsew',padx=(0 if col==0 else 5,0 if col==2 else 5))
        ttk.Label(card,text=f'{col+1:02d}  {key}',foreground=c['blue'],style='Title.TLabel').pack(anchor='w')
        ttk.Label(card,textvariable=phase_vars[key],wraplength=360,style='Muted.TLabel').pack(anchor='w',pady=(7,0))

    workspace=ttk.Panedwindow(root,orient='horizontal')
    workspace.grid(row=4,column=0,sticky='nsew',padx=22,pady=4)
    left=panel(workspace); right=panel(workspace)
    workspace.add(left,weight=5); workspace.add(right,weight=4)
    left.columnconfigure(0,weight=1); left.rowconfigure(1,weight=1)
    mem_head=ttk.Frame(left,style='Panel.TFrame'); mem_head.grid(row=0,column=0,sticky='ew',pady=(0,10)); mem_head.columnconfigure(0,weight=1)
    ttk.Label(mem_head,text='Memoria principal',style='Title.TLabel').grid(row=0,column=0,sticky='w')
    ttk.Combobox(mem_head,textvariable=filter_var,values=['Toda la memoria','Instrucciones','Datos no cero'],state='readonly',width=19).grid(row=0,column=1)
    mem_box=ttk.Frame(left,style='Panel.TFrame'); mem_box.grid(row=1,column=0,sticky='nsew'); mem_box.columnconfigure(0,weight=1); mem_box.rowconfigure(0,weight=1)
    tree=ttk.Treeview(mem_box,columns=('address','type','value'),show='headings',selectmode='browse')
    for key,title,width in [('address','DIR.',65),('type','TIPO',95),('value','CONTENIDO',230)]:
        tree.heading(key,text=title); tree.column(key,width=width,anchor='w',stretch=key=='value')
    scroll=ttk.Scrollbar(mem_box,command=tree.yview); tree.configure(yscrollcommand=scroll.set)
    tree.grid(row=0,column=0,sticky='nsew'); scroll.grid(row=0,column=1,sticky='ns')
    tree.tag_configure('pc',background='#214c50',foreground='#b7ffeb')
    tree.tag_configure('code',foreground=c['blue'])
    tree.tag_configure('data',foreground='#ffd58b')
    ttk.Button(left,text='Editar celda seleccionada',command=lambda:edit_memory()).grid(row=2,column=0,sticky='ew',pady=(10,0))
    right.columnconfigure(0,weight=1); right.rowconfigure(0,weight=1)
    notebook=ttk.Notebook(right); notebook.grid(row=0,column=0,sticky='nsew')

    def text_tab(title, editable=False):
        frame=ttk.Frame(notebook,style='Panel.TFrame'); frame.columnconfigure(0,weight=1); frame.rowconfigure(0,weight=1)
        notebook.add(frame,text=title)
        widget=tk.Text(frame,bg=c['field'],fg=c['ink'],insertbackground=c['accent'],selectbackground='#365075',font=('Consolas',11),wrap='word',relief='flat',padx=14,pady=14,undo=editable)
        widget.grid(row=0,column=0,sticky='nsew')
        scrollbar=ttk.Scrollbar(frame,command=widget.yview); scrollbar.grid(row=0,column=1,sticky='ns'); widget.configure(yscrollcommand=scrollbar.set)
        if not editable: widget.configure(state='disabled')
        return frame,widget

    log_frame,log=text_tab('Traza')
    log.tag_configure('explanation', foreground=c['accent'], spacing1=8, spacing3=8)
    printer_frame,printer=text_tab('Impresora')
    editor_frame,editor=text_tab('Editor ASM',True)
    editor.insert('1.0','# Escribe instrucciones; inicializa datos con INPUT.\nINPUT\nSTORE 20\nOUTPUT\nHALT\n')
    editor_actions=ttk.Frame(editor_frame,style='Panel.TFrame'); editor_actions.grid(row=1,column=0,columnspan=2,sticky='ew',pady=8)
    ttk.Button(editor_actions,text='Cargar desde editor',style='Primary.TButton',command=lambda:load_editor()).pack(side='left',padx=5)
    ttk.Button(editor_actions,text='Guardar ASM',command=lambda:save_editor()).pack(side='left',padx=5)
    help_frame,help_text=text_tab('Ayuda')
    def append(widget,message):
        widget.configure(state='normal')
        widget.insert('end', message+'\n', ('explanation',) if widget is log and message.lstrip().startswith('EXPLICACIÓN') else ())
        widget.see('end'); widget.configure(state='disabled')
    append(help_text,'INSTRUCCIONES\n\nLOAD dir  - Memoria -> ACC\nSTORE dir - ACC -> Memoria\nADD / SUB dir - Aritmetica\nJMP dir - Salto incondicional\nJZ / JNZ dir - Salto segun Z\nINPUT - Leer entero\nOUTPUT - Imprimir ACC\nHALT - Detener\n\nDirecciones: 0 a 99. Comentarios: # o //.\n\nF7: siguiente instruccion\nF5: ejecutar / continuar\nF6: pausar\n\nEl editor carga codigo. Para datos iniciales usa INPUT o edita celdas de datos. Reiniciar restaura el programa cargado y sus datos iniciales. Los errores requieren reinicio. Cancelar INPUT conserva la instruccion pendiente.')
    def output(message):
        append(log,message)
        if 'IMPRESORA' in message:
            outputs.append(vm.acc); append(printer,f'{len(outputs):02d}  >  {vm.acc}')
    def keyboard():
        value=simpledialog.askinteger('Teclado virtual','Entero para INPUT:',parent=root)
        if value is None: raise InputCancelled('Entrada cancelada')
        return value
    vm=VirtualMachine(input_handler=keyboard,output_handler=output)

    controls=panel(root); controls.grid(row=5,column=0,sticky='ew',padx=22,pady=(10,6))
    controls.columnconfigure(4,weight=1)
    step_button=ttk.Button(controls,text='Paso  F7',command=lambda:single_step()); step_button.grid(row=0,column=0,padx=(0,8))
    run_button=ttk.Button(controls,text='Ejecutar  F5',style='Primary.TButton',command=lambda:run()); run_button.grid(row=0,column=1,padx=8)
    pause_button=ttk.Button(controls,text='Pausar  F6',command=lambda:pause()); pause_button.grid(row=0,column=2,padx=8)
    ttk.Button(controls,text='Reiniciar',command=lambda:reset()).grid(row=0,column=3,padx=8)
    speed_label=tk.StringVar(value='300 ms / instruccion')
    speed_box=ttk.Frame(controls,style='Panel.TFrame'); speed_box.grid(row=0,column=4,sticky='ew',padx=16); speed_box.columnconfigure(0,weight=1)
    ttk.Label(speed_box,textvariable=speed_label,style='Muted.TLabel').grid(row=0,column=0)
    ttk.Scale(speed_box,from_=30,to=1000,variable=speed,command=lambda v:speed_label.set(f'{int(float(v))} ms / instruccion')).grid(row=1,column=0,sticky='ew')
    ttk.Label(controls,text='Limite de ciclos',style='Muted.TLabel').grid(row=0,column=5,padx=8)
    ttk.Spinbox(controls,from_=1,to=100000,textvariable=limit,width=8).grid(row=0,column=6)
    tk.Label(root,textvariable=hint,bg=c['bg'],fg=c['muted'],anchor='w',font=('Segoe UI',9)).grid(row=6,column=0,sticky='ew',padx=24,pady=(2,12))

    def pause():
        if scheduler['id'] is not None: root.after_cancel(scheduler['id'])
        scheduler.update(id=None,running=False)
        refresh()
    def refresh():
        state=vm.get_state_summary()
        metrics['PC'].set(f"{vm.pc:02d}"); metrics['IR'].set(state['ir']); metrics['ACC'].set(str(vm.acc))
        metrics['FLAGS'].set(f'Z {int(vm.flag_z)}  N {int(vm.flag_n)}'); metrics['CICLOS'].set(str(vm.cycles))
        status.set('ERROR' if vm.error else 'FINALIZADA' if vm.halted else 'EJECUTANDO' if scheduler['running'] else 'LISTA' if source['text'] is not None and vm.cycles==0 else 'PAUSADA' if source['text'] is not None else 'EN ESPERA')
        for key,var in phase_vars.items(): var.set(vm.last_trace.get(key,'Esperando una instruccion'))
        selection=tree.selection(); old_scroll=tree.yview()[0]
        tree.delete(*tree.get_children())
        for address,value in enumerate(vm.memory.cells):
            is_code=isinstance(value,Instruction)
            if filter_var.get()=='Instrucciones' and not is_code: continue
            if filter_var.get()=='Datos no cero' and (is_code or value==0): continue
            tag='pc' if address==vm.pc and not vm.halted else 'code' if is_code else 'data'
            tree.insert('', 'end',iid=str(address),values=(f'{address:02d}','CODIGO' if is_code else 'DATO',str(value)),tags=(tag,))
        if selection and tree.exists(selection[0]): tree.selection_set(selection[0])
        tree.yview_moveto(old_scroll)
        if scheduler['running'] and tree.exists(str(vm.pc)): tree.see(str(vm.pc))
        can=source['text'] is not None and not vm.error and not vm.halted
        step_button.configure(state='normal' if can and not scheduler['running'] else 'disabled')
        run_button.configure(state='normal' if can and not scheduler['running'] else 'disabled')
        pause_button.configure(state='normal' if scheduler['running'] else 'disabled')
        hint.set(vm.error or ('Programa finalizado. Reinicia para repetir.' if vm.halted else
                 'Entrada cancelada. Pulsa Paso o Ejecutar para reintentar.'
                 if vm.last_trace.get('EXECUTE', '').startswith('Entrada cancelada') else
                 f"{source['name']} | {vm.cycles} instrucciones completadas | PC indica la siguiente instruccion"))
    def clear_outputs():
        outputs.clear()
        for widget in (log,printer): widget.configure(state='normal'); widget.delete('1.0','end'); widget.configure(state='disabled')
    def install(text,name,data=None):
        instructions=DeviceControllers.parse_program(text)
        pause()
        vm.load_instructions(instructions,name)
        clear_outputs()
        source.update(text=text,name=name,data=dict(data or {}))
        for address,value in source['data'].items(): vm.memory.write(address,value)
        source_label.set(name)
        editor.delete('1.0','end'); editor.insert('1.0',text)
        append(log,f'Programa cargado: {name} | {len(instructions)} instrucciones')
        refresh()
    def guarded(action):
        try: action()
        except Exception as exc: messagebox.showerror('VM Studio',str(exc),parent=root)
    def open_file():
        path=filedialog.askopenfilename(parent=root,filetypes=[('Programa ASM','*.asm'),('Texto','*.txt'),('Todos','*.*')])
        if path: guarded(lambda:install(PathRead(path),os.path.basename(path)))
    def PathRead(path):
        with open(path,encoding='utf-8-sig') as stream: return stream.read()
    def load_case():
        key=case_var.get().split(' - ')[0]; case=TEST_CASES[key]
        guarded(lambda:install(PathRead(os.path.join(EXAMPLES_DIR,case['file'])),case['name'],case['data']))
    def load_editor():
        text=editor.get('1.0','end-1c'); guarded(lambda:install(text,'Programa del editor'))
    def save_editor():
        path=filedialog.asksaveasfilename(parent=root,defaultextension='.asm',filetypes=[('Programa ASM','*.asm')])
        if path:
            def save():
                with open(path,'w',encoding='utf-8') as stream: stream.write(editor.get('1.0','end-1c'))
            guarded(save)
    def reset():
        if source['text'] is not None: guarded(lambda:install(source['text'],source['name'],source['data']))
    def advance():
        try:
            ceiling=limit.get()
            if ceiling<=0: raise ValueError('El limite debe ser positivo.')
            if vm.cycles>=ceiling:
                vm.error='Limite de ciclos alcanzado: posible bucle infinito.'
                raise TimeoutError(vm.error)
            vm.step()
        except InputCancelled:
            pause(); hint.set('Entrada cancelada. Pulsa Paso o Ejecutar para reintentar.'); return False
        except Exception as exc:
            pause(); append(log,f'ERROR: {exc}'); messagebox.showerror('Ejecucion detenida',str(exc),parent=root); return False
        finally: refresh()
        return not vm.halted
    def single_step():
        if source['text'] is None or vm.halted or vm.error or scheduler['running']: return
        advance()
    def tick():
        scheduler['id']=None
        if advance() and scheduler['running']: scheduler['id']=root.after(max(1,speed.get()),tick)
        else: pause()
    def run():
        if scheduler['running'] or source['text'] is None or vm.halted or vm.error: return
        scheduler['running']=True; refresh(); scheduler['id']=root.after(0,tick)
    def edit_memory():
        pause()
        selected=tree.selection()
        if not selected: return
        address=int(selected[0]); value=vm.memory.read(address)
        if isinstance(value,Instruction):
            messagebox.showinfo('Celda de codigo','Modifica las instrucciones en el editor ASM y vuelve a cargarlo.',parent=root); return
        number=simpledialog.askinteger('Memoria',f'Nuevo entero para Mem[{address:02d}]:',initialvalue=value,parent=root)
        if number is not None:
            vm.memory.write(address,number)
            if vm.cycles==0: source['data'][address]=number
            refresh()
    def export():
        path=filedialog.asksaveasfilename(parent=root,defaultextension='.json',filetypes=[('Evidencia JSON','*.json')])
        if not path:return
        def write():
            evidence=dict(programa=source['name'],codigo=source['text'],datos_iniciales=source['data'],estado=vm.get_state_summary(),memoria=[str(x) if isinstance(x,Instruction) else x for x in vm.memory.cells],impresora=outputs,traza=vm.execution_log,fases_ultima_instruccion=vm.last_trace)
            with open(path,'w',encoding='utf-8') as stream: json.dump(evidence,stream,ensure_ascii=False,indent=2)
            hint.set('Evidencia exportada: '+os.path.basename(path))
        guarded(write)
    filter_var.trace_add('write',lambda *_:refresh())
    root.bind('<F7>',lambda _:single_step()); root.bind('<F5>',lambda _:run()); root.bind('<F6>',lambda _:pause())
    root.protocol('WM_DELETE_WINDOW',lambda:(pause(),root.destroy()))
    refresh()
    root.mainloop()


def run_cli():
    """Ejecución en consola interactiva."""
    vm = VirtualMachine()
    while True:
        print("\n=== SIMULADOR DE MÁQUINA VIRTUAL SIMPLE (GRUPO 13) ===")
        print("1. Cargar Caso de Prueba (1 al 6)")
        print("2. Cargar Archivo .asm")
        print("3. Ejecutar Siguiente Paso (F-D-E)")
        print("4. Ejecutar Todo (Automático)")
        print("5. Ver Estado de Registros")
        print("6. Ver Volcado de Memoria")
        print("7. Modificar Celda de Memoria")
        print("8. Reiniciar Máquina")
        print("0. Salir")
        opc = input("Seleccione opción: ").strip()

        try:
            if opc == "1":
                print("\nCasos disponibles:")
                for key, case in TEST_CASES.items():
                    print(f"{key}. {case['name']} | Esperado: {case['expected']}")
                p = input("Caso de prueba: ").strip()
                case = load_test_case(vm, p)
                print(f"Caso cargado: {case['name']}. Resultado esperado: {case['expected']}.")
                vm.print_state()
            elif opc == "2":
                path = input("Ruta archivo .asm: ").strip()
                vm.load_program(path)
                vm.print_state()
            elif opc == "3":
                vm.step()
                vm.print_state()
            elif opc == "4":
                vm.run_all()
                vm.print_state()
            elif opc == "5":
                vm.print_state()
            elif opc == "6":
                start = int(input("Inicio (0): ") or "0")
                end = int(input("Fin (20): ") or "20")
                for i in range(start, end + 1):
                    print(f"[{i:02d}]: {vm.memory.read(i)}")
            elif opc == "7":
                addr = int(input("Dirección (0-99): "))
                val = int(input("Valor numérico: "))
                vm.memory.write(addr, val)
            elif opc == "8":
                vm.reset()
                print("VM reiniciada.")
            elif opc == "0":
                break
        except Exception as e:
            print(f"[ERROR]: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        run_cli()
    else:
        try:
            run_gui()
        except Exception:
            print("Entorno gráfico no detectado o display ausente. Iniciando en modo Consola (CLI)...")
            run_cli()
