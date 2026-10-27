"""Pruebas de los flujos públicos de consola y ejecución sin interacción."""
import io
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from src.vm_studio import consola
from src.vm_studio.motor import VirtualMachine


class ConsoleTests(unittest.TestCase):
    def execute(self, args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = consola.main(args)
        return result, stdout.getvalue(), stderr.getvalue()

    def test_archivo_con_entradas_repetidas_no_solicita_dialogos(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'suma.asm'
            path.write_text('INPUT\nSTORE 90\nINPUT\nADD 90\nOUTPUT\nHALT', encoding='utf-8')
            with patch('builtins.input', side_effect=AssertionError('No debe pedir entrada')):
                result, stdout, stderr = self.execute(
                    ['--archivo', str(path), '--entrada', '-4', '--entrada', '11'])
        self.assertEqual(result, 0)
        self.assertIn('HALTED (Detenido)', stdout)
        self.assertIn('IMPRESORA: 7', stdout)
        self.assertEqual(stderr, '')

    def test_falta_entrada_conserva_error_y_exporta_sin_bloquear(self):
        snapshots = []
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'entrada.asm'
            report = Path(folder) / 'error.json'
            path.write_text('INPUT\nHALT', encoding='utf-8')
            def export(vm, destination):
                snapshots.append((vm.get_state_summary(), list(vm.history), list(vm.input_values)))
                return destination
            with patch('builtins.input', side_effect=AssertionError('No debe pedir entrada')), \
                    patch.object(consola, '_export_report', side_effect=export) as save:
                result, stdout, stderr = self.execute(['--archivo', str(path), '--reporte', str(report)])
                self.assertEqual(save.call_count, 1)
        self.assertEqual(result, 1)
        self.assertIn('Faltan valores para INPUT', stderr)
        self.assertRegex(stdout, r'ESTADO\s+: ERROR')
        self.assertEqual(snapshots[0][0]['pc'], 0)
        self.assertEqual(snapshots[0][0]['cycles'], 0)
        self.assertEqual(snapshots[0][1:], ([], []))

    def test_bucle_batch_termina_y_exporta_error_en_limite_total(self):
        snapshots = []
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'bucle.asm'
            path.write_text('JMP 0\nHALT', encoding='utf-8')
            def export(vm, destination):
                snapshots.append(vm.get_state_summary())
                return destination
            with patch.object(consola, '_export_report', side_effect=export):
                result, stdout, stderr = self.execute([
                    '--archivo', str(path), '--max-ciclos', '4', '--reporte', str(Path(folder) / 'error.html')])
        self.assertEqual(result, 1)
        self.assertIn('Límite de ciclos', stderr)
        self.assertEqual(snapshots[0]['cycles'], 4)
        self.assertFalse(snapshots[0]['halted'])

    def test_carga_fallida_da_codigo_de_error_y_reporte_si_se_pidio(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'inexistente.asm'
            with patch.object(consola, '_export_report', side_effect=lambda vm, dest: dest) as export:
                result, stdout, stderr = self.execute([
                    '--archivo', str(path), '--reporte', str(Path(folder) / 'error.csv')])
        self.assertEqual(result, 1)
        self.assertIn('no encontrado', stderr)
        self.assertFalse(export.call_args.args[0].program_loaded)
        self.assertIn('ERROR', stdout)

    def test_argumentos_incompatibles_se_rechazan_antes_de_ejecutar(self):
        for args in (['--entrada', '7'], ['--reporte', 'dato.html'], ['--max-ciclos', '2'],
                     ['--archivo', 'x.asm', '--cli'], ['--archivo', 'x.asm', '--max-ciclos', '0'],
                     ['--archivo', 'x.asm', '--max-ciclos', '-1'],
                     ['--archivo', 'x.asm', '--max-ciclos', 'texto'],
                     ['--archivo', 'x.asm', '--reporte', 'dato.exe']):
            with self.subTest(args=args), patch.object(VirtualMachine, 'load_program') as load:
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                    consola.main(args)
                self.assertEqual(error.exception.code, 2)
                load.assert_not_called()

    def test_menu_fin_de_archivo_y_ctrl_c_salen_sin_traceback(self):
        for signal in (EOFError(), KeyboardInterrupt()):
            with self.subTest(signal=type(signal).__name__), \
                    patch('builtins.input', side_effect=signal), redirect_stdout(io.StringIO()) as output:
                self.assertEqual(consola.run_cli(), 0)
                self.assertIn('Sesión finalizada', output.getvalue())

    def test_menu_reinicia_datos_y_repite_programa(self):
        # Carga suma, cambia un dato antes del primer paso y verifica dos recorridos.
        vm = VirtualMachine(output_handler=lambda _: None)
        responses = ['1', '1', '7', '10', '15', '4', '8', '4', '0']
        with patch.object(consola, 'VirtualMachine', return_value=vm), \
                patch('builtins.input', side_effect=responses), redirect_stdout(io.StringIO()):
            self.assertEqual(consola.run_cli(), 0)
        self.assertTrue(vm.halted)
        self.assertEqual(vm.acc, 35)
        self.assertEqual(vm.outputs, [35])
        self.assertEqual(vm.cycles, 5)
        self.assertEqual(vm.initial_data[10], 15)

    def test_menu_no_permite_editar_codigo_y_continua_utilizable(self):
        vm = VirtualMachine(output_handler=lambda _: None)
        responses = ['1', '1', '7', '0', '20', '4', '0']
        with patch.object(consola, 'VirtualMachine', return_value=vm), \
                patch('builtins.input', side_effect=responses), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(consola.run_cli(), 0)
        self.assertIn('La celda contiene código', output.getvalue())
        self.assertEqual(vm.outputs, [30])

    def test_menu_consulta_sin_carga_no_inutiliza_maquina(self):
        vm = VirtualMachine(output_handler=lambda _: None)
        with patch.object(consola, 'VirtualMachine', return_value=vm), \
                patch('builtins.input', side_effect=['3', '1', '1', '4', '0']), \
                redirect_stdout(io.StringIO()) as output:
            self.assertEqual(consola.run_cli(), 0)
        self.assertIn('No hay un programa cargado', output.getvalue())
        self.assertTrue(vm.halted)
        self.assertEqual(vm.outputs, [30])


if __name__ == '__main__':
    unittest.main(verbosity=2)
