"""Pruebas de ejecución, validación y recuperación de la VM."""
import unittest
from simulador_vm import (
    VirtualMachine, Instruction, InputCancelled, ExecutionFault,
    InvalidInstructionException, MemoryOutOfBoundsException,
)


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


if __name__ == '__main__':
    unittest.main(verbosity=2)
