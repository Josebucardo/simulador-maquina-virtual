"""Comprueba los controles reales de Tkinter sin intervención manual."""
import json
import csv
import os
import sys
import tempfile
import time
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from unittest.mock import patch
import simulador_vm


def verificar(root):
    callback_errors = []
    root.report_callback_exception = lambda exc_type, exc, tb: callback_errors.append(exc)
    root.update_idletasks()
    widgets = []
    def visit(widget):
        widgets.append(widget)
        for child in widget.winfo_children():
            visit(child)
    visit(root)
    def button(label):
        return next(w for w in widgets if isinstance(w, ttk.Button) and w.cget('text') == label)
    def click(label):
        button(label).invoke()
        root.update_idletasks()
        assert not callback_errors, callback_errors
    def metric(value):
        return any(isinstance(w, tk.Label) and w.cget('text') == value for w in widgets)
    tree = next(w for w in widgets if isinstance(w, ttk.Treeview))
    notebook = next(w for w in widgets if isinstance(w, ttk.Notebook))
    editor = next(w for w in widgets if isinstance(w, tk.Text) and w.cget('undo'))
    memory_filter = next(w for w in widgets if isinstance(w, ttk.Combobox) and 'Datos' in w.cget('values'))
    limit_widget = next(w for w in widgets if isinstance(w, ttk.Spinbox))
    def labels():
        return [str(w.cget('text')) for w in widgets if isinstance(w, (tk.Label, ttk.Label))]
    def snapshot(path):
        click('Exportar evidencia')
        result = json.loads(path.read_text(encoding='utf-8'))
        result.pop('fecha', None)
        return result
    def set_source(source):
        notebook.select(2)
        editor.delete('1.0', 'end')
        editor.insert('1.0', source)
        root.update()
        click('Cargar desde editor')
    def capture(name):
        if '--capturas' not in sys.argv and os.environ.get('VM_GUI_CAPTURAS') != '1':
            return
        from PIL import ImageGrab
        directory = Path(__file__).resolve().parents[1] / 'docs/evidencias/capturas'
        directory.mkdir(parents=True, exist_ok=True)
        root.lift()
        root.update()
        time.sleep(0.15)
        # Windows puede virtualizar las coordenadas Tk por el escalado de pantalla.
        # ImageGrab devuelve píxeles físicos: convertir evita capturas recortadas.
        screen = ImageGrab.grab()
        scale_x = screen.width / root.winfo_screenwidth()
        scale_y = screen.height / root.winfo_screenheight()
        box = tuple(round(value) for value in (
            root.winfo_rootx() * scale_x, root.winfo_rooty() * scale_y,
            (root.winfo_rootx() + root.winfo_width()) * scale_x,
            (root.winfo_rooty() + root.winfo_height()) * scale_y))
        screen.crop(box).save(directory / name)
    # La resolución de demostración debe mantener todos los botones dentro de la ventana.
    root.geometry('1024x700+20+20')
    root.update()
    for widget in widgets:
        if isinstance(widget, ttk.Button) and widget.winfo_ismapped():
            x = widget.winfo_rootx() - root.winfo_rootx()
            y = widget.winfo_rooty() - root.winfo_rooty()
            assert x >= 0 and y >= 0, (widget.cget('text'), x, y)
            assert x + widget.winfo_width() <= root.winfo_width(), widget.cget('text')
            assert y + widget.winfo_height() <= root.winfo_height(), widget.cget('text')
    assert button('Ejecutar  F5').instate(['disabled'])
    assert button('Exportar reporte').instate(['disabled'])
    with tempfile.TemporaryDirectory() as folder:
        output = Path(folder) / 'evidencia.json'
        with patch('tkinter.filedialog.asksaveasfilename', return_value=str(output)):
            with patch.object(simulador_vm.DiskController, 'read_source',
                              wraps=simulador_vm.DiskController.read_source) as disk_read:
                click('Cargar ejemplo')
                disk_read.assert_called_once()
            assert len(tree.get_children()) == 100
            for _ in range(3):
                click('Paso  F7')
            assert 'changed' in tree.item('20', 'tags')
            tree.see('20')
            capture('vm_suma.png')
            for _ in range(2):
                click('Paso  F7')
            click('Exportar evidencia')
            evidence = json.loads(output.read_text(encoding='utf-8'))
            assert evidence['estado']['acc'] == 30
            assert evidence['estado']['halted']
            assert evidence['impresora'] == [30]
            assert set(evidence['fases_ultima_instruccion']) == {'FETCH', 'DECODE', 'EXECUTE'}
            assert len(evidence['pasos']) == 5
            assert any('CORRECTO' in value for value in labels())
            capture('vm_finalizada.png')
            notebook.select(4)
            root.update()
            capture('vm_reporte.png')
            notebook.select(0)
            # Cada formato se genera desde los mismos resultados del motor.
            html_output = Path(folder) / 'suma.html'
            with patch('tkinter.filedialog.asksaveasfilename', return_value=str(html_output)):
                click('Exportar reporte')
            assert '30' in html_output.read_text(encoding='utf-8')
            assert '<table' in html_output.read_text(encoding='utf-8')
            csv_output = Path(folder) / 'suma.csv'
            with patch('tkinter.filedialog.asksaveasfilename', return_value=str(csv_output)):
                click('Exportar reporte')
            with csv_output.open(encoding='utf-8-sig', newline='') as stream:
                assert len(list(csv.reader(stream, delimiter=';'))) > 5
            memory_filter.set('Instrucciones')
            root.update_idletasks()
            assert len(tree.get_children()) == 5
            memory_filter.set('Datos')
            assert len(tree.get_children()) == 95
            assert tree.exists('99')  # También incluye datos cero.
            memory_filter.set('Datos no cero')
            assert set(tree.get_children()) == {'10', '11', '20'}
            memory_filter.set('Toda la memoria')
            click('Reiniciar')
            click('Ejecutar  F5')
            assert button('Abrir ASM').instate(['disabled'])
            assert button('Reiniciar').instate(['disabled'])
            click('Pausar  F6')
            click('Exportar evidencia')
            assert json.loads(output.read_text(encoding='utf-8'))['estado']['cycles'] == 0
            scale = next(w for w in widgets if isinstance(w, ttk.Scale))
            scale.set(30)
            click('Ejecutar  F5')
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline and button('Pausar  F6').instate(['!disabled']):
                root.update()
                time.sleep(0.01)
            click('Exportar evidencia')
            assert json.loads(output.read_text(encoding='utf-8'))['estado']['halted']
            click('Reiniciar')
            notebook = next(w for w in widgets if isinstance(w, ttk.Notebook))
            notebook.select(2)
            editor = next(w for w in widgets if isinstance(w, tk.Text) and w.cget('undo'))
            editor.delete('1.0', 'end')
            editor.insert('1.0', 'INPUT\nOUTPUT\nHALT')
            click('Cargar desde editor')
            with patch('tkinter.simpledialog.askinteger', return_value=None):
                click('Paso  F7')
            click('Exportar evidencia')
            assert json.loads(output.read_text(encoding='utf-8'))['estado']['pc'] == 0
            with patch('tkinter.simpledialog.askinteger', return_value=-9):
                for _ in range(3):
                    click('Paso  F7')
            click('Exportar evidencia')
            evidence = json.loads(output.read_text(encoding='utf-8'))
            assert evidence['impresora'] == [-9]
            assert evidence['estado']['halted']
            editor.delete('1.0', 'end')
            editor.insert('1.0', 'JMP 0\nHALT')
            click('Cargar desde editor')
            spin = next(w for w in widgets if isinstance(w, ttk.Spinbox))
            spin.set(2)
            with patch('tkinter.messagebox.showerror') as error_dialog:
                click('Ejecutar  F5')
                deadline = time.monotonic() + 3
                while time.monotonic() < deadline and button('Pausar  F6').instate(['!disabled']):
                    root.update()
                    time.sleep(0.01)
                assert error_dialog.called
            click('Exportar evidencia')
            evidence = json.loads(output.read_text(encoding='utf-8'))
            assert evidence['estado']['cycles'] == 2
            assert evidence['estado']['error']
            assert any(value == 'ERROR' for value in labels())

            spin.set(10000)
            program = Path(folder) / 'datos.asm'
            source = 'DATA 90 40\nDATA 91 2\nLOAD 90\nADD 91\nSTORE 92\nOUTPUT\nHALT\n'
            program.write_text(source, encoding='utf-8-sig')
            with patch('tkinter.filedialog.askopenfilename', return_value=str(program)), \
                    patch.object(simulador_vm.DiskController, 'read_source',
                                 wraps=simulador_vm.DiskController.read_source) as disk_read, \
                    patch.object(simulador_vm.DeviceControllers, 'parse_program',
                                 wraps=simulador_vm.DeviceControllers.parse_program) as parse:
                click('Abrir ASM')
                disk_read.assert_called_once_with(str(program))
                parse.assert_called_once_with(source)
            for _ in range(5):
                click('Paso  F7')
            click('Exportar evidencia')
            valid_evidence = json.loads(output.read_text(encoding='utf-8'))
            assert valid_evidence['estado']['halted']
            assert valid_evidence['estado']['acc'] == 42
            assert valid_evidence['memoria'][92] == 42
            assert valid_evidence['impresora'] == [42]
            assert valid_evidence['datos_iniciales'] == {'90': 40, '91': 2}

            for invalid_source in ('LOAD R9\nHALT', 'LOAD 90'):
                program.write_text(invalid_source, encoding='utf-8')
                with patch('tkinter.filedialog.askopenfilename', return_value=str(program)), \
                        patch('tkinter.messagebox.showerror') as error_dialog:
                    click('Abrir ASM')
                    error_dialog.assert_called_once()
                click('Exportar evidencia')
                actual = json.loads(output.read_text(encoding='utf-8'))
                actual.pop('fecha', None)
                expected = dict(valid_evidence)
                expected.pop('fecha', None)
                assert actual == expected

            # El texto editado no debe confundirse con el programa ya cargado.
            click('Reiniciar')
            assert button('Paso  F7').instate(['!disabled'])
            editor.insert('end', '\n# Cambio todavía sin cargar')
            root.update()
            assert button('Paso  F7').instate(['disabled'])
            assert any('CAMBIOS SIN CARGAR' in value for value in labels())
            unloaded = snapshot(output)
            assert '# Cambio todavía sin cargar' not in unloaded['codigo']
            click('Cargar desde editor')
            assert button('Paso  F7').instate(['!disabled'])

            # Un valor de configuración incorrecto se corrige sin bloquear la VM.
            limit_widget.set('no entero')
            with patch('tkinter.messagebox.showerror') as dialog:
                click('Paso  F7')
                dialog.assert_called_once()
            invalid_limit = snapshot(output)
            assert invalid_limit['estado']['cycles'] == 0
            assert invalid_limit['estado']['error'] is None
            limit_widget.set(5)
            for _ in range(5):
                click('Paso  F7')
            assert snapshot(output)['estado']['halted']  # HALT en el último ciclo.

            # Reentradas desde un diálogo de INPUT no deben ejecutar ni cargar otro programa.
            limit_widget.set(10000)
            set_source('INPUT\nOUTPUT\nHALT')
            def input_and_attempt_reentry(*args, **kwargs):
                assert button('Abrir ASM').instate(['disabled'])
                assert button('Cargar ejemplo').instate(['disabled'])
                click('Reiniciar')
                click('Paso  F7')
                root.event_generate('<F5>')
                root.update()
                return 17
            with patch('tkinter.simpledialog.askinteger', side_effect=input_and_attempt_reentry):
                click('Paso  F7')
            entered = snapshot(output)
            assert entered['estado']['cycles'] == 1
            assert entered['entradas'] == [17]
            assert entered['estado']['acc'] == 17

            # Edición inicial se conserva; una edición posterior es temporal.
            click('Cargar ejemplo')
            tree.selection_set('10')
            with patch('tkinter.simpledialog.askinteger', return_value=40):
                click('Editar celda seleccionada')
            initial = snapshot(output)
            assert initial['datos_iniciales']['10'] == 40
            click('Reiniciar')
            assert snapshot(output)['memoria'][10] == 40
            click('Paso  F7')
            tree.selection_set('10')
            with patch('tkinter.simpledialog.askinteger', return_value=99):
                click('Editar celda seleccionada')
            click('Reiniciar')
            assert snapshot(output)['memoria'][10] == 40

            # Un error conserva la instrucción y puede documentarse y recuperarse.
            set_source('LOAD 0\nHALT')
            notebook.select(0)
            with patch('tkinter.messagebox.showerror') as dialog:
                click('Paso  F7')
                dialog.assert_called_once()
            failure = snapshot(output)
            assert failure['estado']['error']
            assert failure['estado']['pc'] == 0
            assert button('Paso  F7').instate(['disabled'])
            capture('vm_error.png')
            with patch('tkinter.filedialog.asksaveasfilename', return_value=str(html_output)):
                click('Exportar reporte')
            assert 'ERROR' in html_output.read_text(encoding='utf-8')
            click('Reiniciar')
            recovered = snapshot(output)
            assert recovered['estado']['error'] is None
            assert recovered['estado']['cycles'] == 0
            # La vista también se adapta al ancho habitual del proyector.
            root.geometry('1366x768+20+20')
            root.update()
            assert tree.winfo_height() >= 180
            assert not callback_errors, callback_errors
    print('GUI OK: carga por controlador, DATA, pasos y pausa, reentrada protegida, editor pendiente, filtros, edición, límites, reinicio, errores y reportes JSON/HTML/CSV; ventana 1024x700 y 1366x768.')
    root.destroy()


if __name__ == '__main__':
    # Los errores deben fallar la prueba, en lugar de abrir un diálogo bloqueante.
    def fail(*args, **kwargs):
        raise AssertionError(str(args))
    with patch.object(tk.Tk, 'mainloop', verificar), patch('tkinter.messagebox.showerror', side_effect=fail):
        simulador_vm.run_gui()
