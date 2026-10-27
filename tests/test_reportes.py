"""Reportes con datos reales, instantáneas independientes y escape de contenido."""
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest

from src.vm_studio.motor import VirtualMachine, InvalidInstructionException
from src.vm_studio.reportes import build_evidence, render_html, render_csv, save_report


class ReportTests(unittest.TestCase):
    def vm(self):
        vm = VirtualMachine(input_handler=lambda: -7, output_handler=lambda _: None)
        vm.load_source('INPUT\nSTORE 90\nOUTPUT\nHALT', '<script>alert(1)</script>')
        return vm

    def test_snapshot_independiente_y_estados(self):
        vm = self.vm()
        first = build_evidence(vm)
        self.assertEqual(first['estado_ejecucion'], 'LISTA')
        vm.step()
        paused = build_evidence(vm)
        vm.run_all()
        complete = build_evidence(vm)
        self.assertEqual(first['estado']['cycles'], 0)
        self.assertEqual(first['pasos'], [])
        self.assertEqual(paused['estado_ejecucion'], 'PAUSADA')
        self.assertEqual(paused['entradas'], [-7])
        self.assertEqual(len(paused['pasos']), 1)
        self.assertEqual(complete['estado_ejecucion'], 'FINALIZADA')
        self.assertEqual(complete['impresora'], [-7])
        self.assertEqual(complete['estadisticas']['escrituras_datos'], 1)
        self.assertEqual(complete['pasos'][1]['cambios_memoria'], [{'direccion': 90, 'antes': 0, 'despues': -7}])

    def test_html_escapa_nombre_codigo_y_error(self):
        vm = self.vm()
        vm.run_all()
        evidence = build_evidence(vm)
        evidence['codigo'] += '\n# <img src=x onerror=alert(1)>'
        evidence['estado']['error'] = '<b>error</b>'
        html = render_html(evidence)
        self.assertNotIn('<script>', html)
        self.assertNotIn('<img src=x', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertIn('&lt;b&gt;error&lt;/b&gt;', html)
        self.assertIn('@media print', html)
        self.assertIn('Memoria completa', html)

    def test_error_y_maquina_vacia(self):
        vm = VirtualMachine(output_handler=lambda _: None)
        self.assertEqual(build_evidence(vm)['estado_ejecucion'], 'SIN PROGRAMA')
        vm.load_source('LOAD 0\nHALT')
        with self.assertRaises(InvalidInstructionException):
            vm.step()
        evidence = build_evidence(vm)
        self.assertEqual(evidence['estado_ejecucion'], 'ERROR')
        self.assertEqual(evidence['pasos'], [])
        self.assertIn('Diagnóstico', render_html(evidence))

    def test_csv_uniforme_formula_segura_y_numeros(self):
        vm = self.vm()
        vm.run_all()
        evidence = build_evidence(vm, name='=HYPERLINK("bad")')
        parsed = list(csv.reader(io.StringIO(render_csv(evidence)), delimiter=';'))
        self.assertTrue(all(len(row) == len(parsed[0]) for row in parsed))
        self.assertTrue(parsed[1][-1].startswith("'="))
        self.assertIn('-7', [row[-1] for row in parsed if row[0] == 'salida'])
        self.assertEqual(len([row for row in parsed if row[0] == 'memoria']), 100)
        self.assertEqual(len([row for row in parsed if row[0] == 'paso']), 4)

    def test_guardado_roundtrip_y_extension_sin_destruir(self):
        vm = self.vm()
        vm.run_all()
        evidence = build_evidence(vm)
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder) / 'informes'
            path = save_report(evidence, base / 'datos.json')
            saved = json.loads(path.read_text(encoding='utf-8'))
            self.assertEqual(saved['impresora'], [-7])
            self.assertEqual(len(saved['pasos']), 4)
            csv_path = save_report(evidence, base / 'datos.csv')
            self.assertTrue(csv_path.read_bytes().startswith(b'\xef\xbb\xbf'))
            save_report(evidence, base / 'datos.html')
            existing = base / 'datos.txt'
            existing.write_text('conservar', encoding='utf-8')
            with self.assertRaises(ValueError):
                save_report(evidence, existing)
            self.assertEqual(existing.read_text(encoding='utf-8'), 'conservar')

    def test_salto_destino_secuencial_se_cuenta_por_condicion(self):
        vm = VirtualMachine(output_handler=lambda _: None)
        vm.load_source('JZ 1\nHALT')
        vm.run_all()
        statistics = build_evidence(vm)['estadisticas']
        self.assertEqual(statistics['saltos_tomados'], 1)
        self.assertEqual(statistics['saltos_no_tomados'], 0)


if __name__ == '__main__':
    unittest.main()
