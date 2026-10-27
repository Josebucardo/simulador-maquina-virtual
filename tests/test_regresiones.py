"""Pruebas de ejecución, validación y recuperación de la VM."""
import io
from copy import deepcopy
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from simulador_vm import (
    VirtualMachine, Instruction, InputCancelled, ExecutionFault,
    InvalidInstructionException, MemoryOutOfBoundsException, DiskController,
    DeviceControllers,
)
from src.vm_studio.motor import Memory, Program


class VMTests(unittest.TestCase):
    def vm(self, source, **kwargs):
        vm = VirtualMachine(output_handler=lambda _: None, **kwargs)
        vm.load_source(source)
        return vm

    def test_halt_en_limite(self):
        vm = self.vm('HALT')
        vm.run_all(1)
        self.assertTrue(vm.halted)
        self.assertEqual(vm.cycles, 1)

    def test_error_conserva_pc_y_bloquea(self):
        vm = self.vm('LOAD 0\nHALT')
        with self.assertRaises(InvalidInstructionException):
            vm.step()
        self.assertEqual(vm.pc, 0)
        with self.assertRaises(ExecutionFault):
            vm.step()
        vm.load_source('HALT')
        vm.run_all()
        self.assertIsNone(vm.error)

    def test_consola_muestra_error_y_causa_hasta_recargar(self):
        vm = self.vm('LOAD 0\nHALT')
        with self.assertRaises(InvalidInstructionException):
            vm.step()
        output = io.StringIO()
        with redirect_stdout(output):
            vm.print_state()
        self.assertRegex(output.getvalue(), r'ESTADO\s+: ERROR')
        self.assertIn(vm.error, output.getvalue())
        self.assertNotIn('EJECUTANDO', output.getvalue())

        vm.load_source('HALT')
        vm.run_all()
        recovered = io.StringIO()
        with redirect_stdout(recovered):
            vm.print_state()
        self.assertIn('HALTED (Detenido)', recovered.getvalue())
        self.assertNotIn('CAUSA', recovered.getvalue())

    def test_cancelar_y_reintentar(self):
        def cancel():
            raise InputCancelled()
        vm = self.vm('INPUT\nHALT', input_handler=cancel)
        with self.assertRaises(InputCancelled):
            vm.step()
        self.assertEqual((vm.pc, vm.acc, vm.cycles), (0, 0, 0))
        self.assertIsNone(vm.error)
        vm.input_handler = lambda: -7
        vm.run_all()
        self.assertEqual(vm.acc, -7)
        self.assertTrue(vm.flag_n)

    def test_bucle_infinito(self):
        vm = self.vm('JMP 0\nHALT')
        with self.assertRaises(TimeoutError):
            vm.run_all(12)
        self.assertEqual(vm.cycles, 12)
        self.assertIsNotNone(vm.error)

    def test_saltos(self):
        for opcode, number, taken in [('JZ', 0, True), ('JZ', 1, False),
                                      ('JNZ', 0, False), ('JNZ', -1, True)]:
            with self.subTest(opcode=opcode, number=number):
                vm = self.vm(f'LOAD 99\n{opcode} 3\nLOAD 98\nHALT')
                vm.memory.write(99, number)
                vm.memory.write(98, 55)
                vm.run_all()
                self.assertEqual(vm.acc, number if taken else 55)
        vm = self.vm('JMP 2\nLOAD 99\nHALT')
        vm.run_all()
        self.assertEqual(vm.acc, 0)

    def test_limites_y_fetch_invalido(self):
        vm = self.vm('HALT')
        for address in (-1, 100):
            with self.assertRaises(MemoryOutOfBoundsException):
                vm.memory.read(address)
        vm.memory.write(99, 42)
        self.assertEqual(vm.memory.read(99), 42)
        vm.load_source('JMP 99\nHALT')
        vm.step()
        with self.assertRaises(InvalidInstructionException):
            vm.step()
        self.assertEqual(vm.pc, 99)

    def test_carga_invalida_preserva_programa(self):
        vm = self.vm('HALT')
        for text in ('', 'LOAD\nHALT', 'OUTPUT 1\nHALT', 'LOAD ACC\nHALT',
                     'MULT 1\nHALT', 'JMP 0'):
            with self.subTest(text=text):
                with self.assertRaises(InvalidInstructionException):
                    vm.load_source(text)
                self.assertEqual(str(vm.memory.read(0)), 'HALT')

    def test_diagnostico_registro_invalido_y_operando_no_entero(self):
        vm = self.vm('HALT')
        for register in ('ACC', 'R9', 'pc', 'IR', 'FLAGS'):
            with self.subTest(register=register):
                with self.assertRaises(InvalidInstructionException) as error:
                    vm.load_source(f'LOAD {register}\nHALT')
                self.assertIn('Registro no válido como operando', str(error.exception))
                self.assertIn('ACC se usa implícitamente', str(error.exception))
                self.assertIn(register, str(error.exception))
        for operand in ('texto', '3.5'):
            with self.subTest(operand=operand):
                with self.assertRaisesRegex(InvalidInstructionException, 'debe ser un número entero'):
                    vm.load_source(f'LOAD {operand}\nHALT')

    def test_archivo_con_bom_y_data_pasa_por_controlador_una_vez(self):
        source = 'DATA 90 40\nDATA 91 2\nLOAD 90\nADD 91\nHALT\n'
        vm = VirtualMachine(output_handler=lambda _: None)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'datos.asm'
            path.write_text(source, encoding='utf-8-sig')
            with patch.object(DiskController, 'read_source', wraps=DiskController.read_source) as read_source, \
                    patch.object(DeviceControllers, 'parse_program', wraps=DeviceControllers.parse_program) as parse:
                vm.load_program(str(path))
                read_source.assert_called_once_with(str(path))
                parse.assert_called_once_with(source)
            vm.run_all()
        self.assertEqual(vm.acc, 42)
        self.assertTrue(vm.halted)

    def test_flags_iniciales_y_fases(self):
        vm = self.vm('HALT')
        self.assertTrue(vm.flag_z)
        vm.step()
        self.assertEqual(set(vm.last_trace), {'FETCH', 'DECODE', 'EXECUTE'})

    def test_entrada_tipo_invalido(self):
        vm = self.vm('INPUT\nHALT', input_handler=lambda: '7')
        with self.assertRaises(InvalidInstructionException):
            vm.step()
        self.assertEqual(vm.pc, 0)

    def test_comentarios_y_limite_programa(self):
        vm = self.vm('# comentario\nhalt // fin')
        vm.run_all()
        with self.assertRaises(MemoryOutOfBoundsException):
            vm.load_source('HALT\n' * 101)

    def test_datos_declarados(self):
        vm = self.vm('DATA 90 12\nDATA 91 -2\nLOAD 90\nADD 91\nHALT')
        vm.run_all()
        self.assertEqual(vm.acc, 10)
        for text in ('DATA 0 7\nHALT', 'DATA 90 1\nDATA 90 2\nHALT',
                     'DATA 90 texto\nHALT'):
            with self.assertRaises(InvalidInstructionException):
                vm.load_source(text)

    def test_explicaciones_reflejan_valores_y_decisiones(self):
        vm = self.vm('DATA 90 10\nDATA 91 20\nLOAD 90\nADD 91\nJZ 4\nOUTPUT\nHALT')
        vm.run_all()
        explanations = [line for line in vm.execution_log if 'EXPLICACIÓN' in line]
        self.assertEqual(len(explanations), vm.cycles)
        self.assertIn('10 + (20) = 30', explanations[1])
        self.assertIn('La condición no se cumple', explanations[2])
        self.assertIn('El acumulador terminó con 30', explanations[-1])

    def test_paso_sin_carga_no_bloquea_y_permite_cargar(self):
        vm = VirtualMachine(output_handler=lambda _: None)
        with self.assertRaisesRegex(InvalidInstructionException, 'No hay un programa'):
            vm.step()
        self.assertIsNone(vm.error)
        self.assertEqual(vm.cycles, 0)
        self.assertEqual(vm.history, [])
        vm.load_source('HALT')
        vm.run_all()
        self.assertTrue(vm.halted)

    def test_limite_total_incluye_pasos_manuales(self):
        vm = self.vm('JMP 0\nHALT')
        vm.step()
        vm.step()
        with self.assertRaises(TimeoutError):
            vm.run_all(3)
        self.assertEqual(vm.cycles, 3)
        self.assertEqual(len(vm.history), 3)
        with self.assertRaises(ExecutionFault):
            vm.run_all(10)
        self.assertEqual(vm.cycles, 3)

        finished = self.vm('LOAD 99\nHALT')
        finished.step()
        finished.run_all(2)
        self.assertTrue(finished.halted)
        self.assertEqual(finished.cycles, 2)

    def test_memoria_rechaza_tipos_invalidos_sin_escribir(self):
        memory = Memory()
        for address in (True, False, 1.5, '1', None):
            with self.subTest(address=address):
                with self.assertRaises(MemoryOutOfBoundsException):
                    memory.read(address)
                with self.assertRaises(MemoryOutOfBoundsException):
                    memory.write(address, 7)
        for value in (True, 2.5, '3', None, [], Instruction('INVENTADA')):
            with self.subTest(value=value):
                with self.assertRaises(InvalidInstructionException):
                    memory.write(99, value)
                self.assertEqual(memory.read(99), 0)

    def test_carga_api_invalida_conserva_ejecucion_completa(self):
        vm = self.vm('DATA 90 5\nLOAD 90\nSTORE 91\nOUTPUT\nHALT')
        vm.run_all()
        previous = deepcopy((vm.get_state_summary(), [str(c) for c in vm.memory.cells],
                             vm.program_source, vm.program_name, vm.initial_data,
                             vm.outputs, vm.input_values, vm.history, vm.manual_edits))
        malformed = []
        for data in ({-1: 7}, {100: 7}, {90: '7'}, {True: 7}, {0: 7}):
            program = Program()
            program.append(Instruction('HALT'))
            program.initial_data = data
            malformed.append(program)
        malformed += [[Instruction('HALT', 1)], [Instruction('LOAD', True), Instruction('HALT')],
                      [Instruction('ADD'), Instruction('HALT')], [3, Instruction('HALT')]]
        for program in malformed:
            with self.subTest(program=program):
                with self.assertRaises((InvalidInstructionException, MemoryOutOfBoundsException)):
                    vm.load_instructions(program)
                after = (vm.get_state_summary(), [str(c) for c in vm.memory.cells],
                         vm.program_source, vm.program_name, vm.initial_data,
                         vm.outputs, vm.input_values, vm.history, vm.manual_edits)
                self.assertEqual(after, previous)

    def test_historial_registra_entrada_salida_y_cambio_de_memoria(self):
        vm = self.vm('INPUT\nSTORE 90\nOUTPUT\nHALT', input_handler=lambda: -4)
        vm.run_all()
        self.assertEqual(vm.input_values, [-4])
        self.assertEqual(vm.outputs, [-4])
        self.assertEqual(len(vm.history), vm.cycles)
        self.assertEqual(vm.history[1]['cambios_memoria'],
                         [{'direccion': 90, 'antes': 0, 'despues': -4}])
        for cycle, row in enumerate(vm.history, 1):
            self.assertEqual(row['ciclo'], cycle)
            self.assertEqual(set(row['fases']), {'FETCH', 'DECODE', 'EXECUTE'})
        self.assertEqual(vm.history[-1]['instruccion'], 'HALT')
        first_trace = deepcopy(vm.history[0]['fases'])
        vm.last_trace['FETCH'] = 'cambio posterior'
        self.assertEqual(vm.history[0]['fases'], first_trace)

    def test_cancelacion_y_error_no_producen_instrucciones_ficticias(self):
        def cancelled():
            raise InputCancelled()
        vm = self.vm('INPUT\nSTORE 90\nLOAD 0\nHALT', input_handler=cancelled)
        with self.assertRaises(InputCancelled):
            vm.step()
        self.assertEqual((vm.history, vm.input_values, vm.outputs), ([], [], []))
        self.assertIsNone(vm.error)
        vm.input_handler = lambda: 9
        vm.step()
        vm.step()
        with self.assertRaises(InvalidInstructionException):
            vm.step()
        self.assertEqual((vm.pc, vm.acc, vm.cycles), (2, 9, 2))
        self.assertEqual(len(vm.history), 2)
        self.assertEqual(vm.input_values, [9])
        self.assertEqual(vm.outputs, [])

    def test_reinicio_restaura_datos_editados_antes_del_primer_paso(self):
        vm = self.vm('DATA 90 5\nLOAD 90\nSTORE 91\nHALT')
        vm.edit_data(90, 8)
        vm.step()
        vm.edit_data(90, 99)
        vm.run_all()
        vm.restart()
        self.assertEqual(vm.memory.read(90), 8)
        self.assertEqual(vm.memory.read(91), 0)
        self.assertEqual((vm.cycles, vm.acc, vm.pc), (0, 0, 0))
        self.assertEqual((vm.history, vm.input_values, vm.outputs, vm.manual_edits), ([], [], [], []))
        vm.run_all()
        self.assertEqual(vm.acc, 8)

    def test_edicion_respeta_codigo_error_y_recuperacion(self):
        vm = self.vm('LOAD 0\nHALT')
        with self.assertRaises(InvalidInstructionException):
            vm.edit_data(0, 12)
        self.assertEqual(str(vm.memory.read(0)), 'LOAD 0')
        with self.assertRaises(InvalidInstructionException):
            vm.step()
        with self.assertRaises(ExecutionFault):
            vm.edit_data(90, 12)
        vm.restart()
        vm.edit_data(90, 12)
        self.assertEqual(vm.memory.read(90), 12)

    def test_cargador_copia_instrucciones_y_preserva_fuente(self):
        source = 'DATA 90 6\nLOAD 90\nHALT'
        program = DeviceControllers.parse_program(source)
        vm = VirtualMachine(output_handler=lambda _: None)
        vm.load_instructions(program, 'Fuente original')
        program[0].operand = 0
        program.initial_data[90] = 999
        vm.run_all()
        self.assertEqual(vm.acc, 6)
        self.assertEqual(vm.program_source, source)
        self.assertEqual(vm.program_name, 'Fuente original')
        vm.restart()
        self.assertEqual(vm.memory.read(90), 6)


if __name__ == '__main__':
    unittest.main(verbosity=2)
