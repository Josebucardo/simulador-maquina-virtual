"""Comprueba los controles reales de Tkinter sin intervención manual."""
import json
import tempfile
import time
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from unittest.mock import patch
import simulador_vm


def verificar(root):
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
    def metric(value):
        return any(isinstance(w, tk.Label) and w.cget('text') == value for w in widgets)
    tree = next(w for w in widgets if isinstance(w, ttk.Treeview))
    with tempfile.TemporaryDirectory() as folder:
        output = Path(folder) / 'evidencia.json'
        with patch('tkinter.filedialog.asksaveasfilename', return_value=str(output)):
            click('Cargar ejemplo')
            assert len(tree.get_children()) == 100
            for _ in range(5):
                click('Paso  F7')
            click('Exportar evidencia')
            evidence = json.loads(output.read_text(encoding='utf-8'))
            assert evidence['estado']['acc'] == 30
            assert evidence['estado']['halted']
            assert evidence['impresora'] == [30]
            assert set(evidence['fases_ultima_instruccion']) == {'FETCH', 'DECODE', 'EXECUTE'}
            click('Reiniciar')
            click('Ejecutar  F5')
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
    print('GUI OK: carga, memoria, pasos, impresora, reinicio, pausa, editor, cancelacion y exportacion.')
    root.destroy()


if __name__ == '__main__':
    # Los errores deben fallar la prueba, en lugar de abrir un diálogo bloqueante.
    def fail(*args, **kwargs):
        raise AssertionError(str(args))
    with patch.object(tk.Tk, 'mainloop', verificar), patch('tkinter.messagebox.showerror', side_effect=fail):
        simulador_vm.run_gui()
