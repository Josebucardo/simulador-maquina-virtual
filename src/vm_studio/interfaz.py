"""Laboratorio de escritorio para observar la máquina virtual."""
from __future__ import annotations
import os
from pathlib import Path
from .motor import DiskController, EXAMPLES_DIR, InputCancelled, Instruction, TEST_CASES, VirtualMachine


def run_gui():
    """Cada paso completa una instrucción y registra Fetch, Decode y Execute."""
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, simpledialog
    from .reportes import build_evidence, save_report

    root = tk.Tk()
    root.title('VM Studio | Máquina virtual simple | Grupo 13')
    width = min(1280, max(960, root.winfo_screenwidth() - 70))
    height = min(820, max(660, root.winfo_screenheight() - 100))
    root.geometry(f'{width}x{height}+20+20')
    root.minsize(940, 650)
    c = dict(bg='#0b1120', panel='#141f32', field='#0e1728', ink='#e8effb',
             muted='#a5b5cf', accent='#68e0c0', blue='#8bb5ff', line='#2c3c56', red='#ff9aaa')
    root.configure(bg=c['bg'])
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('.', font=('Segoe UI', 9), background=c['panel'], foreground=c['ink'])
    style.configure('TFrame', background=c['bg'])
    style.configure('Panel.TFrame', background=c['panel'])
    style.configure('TLabel', background=c['panel'], foreground=c['ink'])
    style.configure('Muted.TLabel', foreground=c['muted'])
    style.configure('Title.TLabel', font=('Segoe UI', 11, 'bold'))
    style.configure('TButton', padding=(10, 6), background=c['line'], borderwidth=0)
    style.map('TButton', background=[('active', '#3b5274'), ('disabled', c['field'])],
              foreground=[('disabled', '#6e809d')])
    style.configure('Primary.TButton', background=c['accent'], foreground=c['bg'], font=('Segoe UI', 9, 'bold'))
    style.map('Primary.TButton', background=[('active', '#a2eedb'), ('disabled', '#355d61')])
    style.configure('TCombobox', fieldbackground=c['field'], background=c['line'], padding=5)
    style.map('TCombobox', fieldbackground=[('readonly', c['field'])], foreground=[('readonly', c['ink'])])
    style.configure('Treeview', background=c['field'], fieldbackground=c['field'], foreground=c['ink'],
                    rowheight=24, borderwidth=0, font=('Consolas', 10))
    style.configure('Treeview.Heading', background=c['line'], foreground=c['muted'], padding=5)
    style.map('Treeview', background=[('selected', '#355579')], foreground=[('selected', '#ffffff')])
    style.configure('TNotebook', background=c['panel'], borderwidth=0)
    style.configure('TNotebook.Tab', background=c['line'], padding=(11, 7))
    style.map('TNotebook.Tab', background=[('selected', c['panel'])], foreground=[('selected', c['accent'])])
    style.configure('TSpinbox', fieldbackground=c['field'], foreground=c['ink'], background=c['line'])
    root.columnconfigure(0, weight=1)
    root.rowconfigure(4, weight=1)
    source = {'text': None, 'name': 'Sin programa', 'case': None}
    scheduler = {'id': None, 'running': False, 'busy': False, 'input': False}
    view = {'sync': False, 'notice': '', 'report_token': None}
    status = tk.StringVar(value='SIN PROGRAMA')
    hint = tk.StringVar()
    source_label = tk.StringVar(value='SIN PROGRAMA')
    result_label = tk.StringVar()
    editor_status = tk.StringVar()
    memory_count = tk.StringVar()
    speed = tk.DoubleVar(value=300)
    speed_label = tk.StringVar(value='300 ms por instrucción')
    limit = tk.StringVar(value='10000')
    filter_var = tk.StringVar(value='Toda la memoria')
    case_var = tk.StringVar(value='1 - Suma')
    metrics = {key: tk.StringVar(value='0') for key in ('PC', 'IR', 'ACC', 'FLAGS', 'CICLOS')}
    phases = {key: tk.StringVar(value='Esperando una instrucción') for key in ('FETCH', 'DECODE', 'EXECUTE')}
    action_buttons = []

    def panel(parent, padding=9, **kwargs):
        return ttk.Frame(parent, style='Panel.TFrame', padding=padding, **kwargs)

    def button(parent, text, command, **kwargs):
        widget = ttk.Button(parent, text=text, command=command, **kwargs)
        action_buttons.append(widget)
        return widget

    header = tk.Frame(root, bg=c['bg'])
    header.grid(row=0, column=0, sticky='ew', padx=16, pady=(12, 6))
    header.columnconfigure(0, weight=1)
    tk.Label(header, text='VM STUDIO', font=('Segoe UI', 21, 'bold'), bg=c['bg'], fg=c['ink']).grid(row=0, column=0, sticky='w')
    tk.Label(header, text='ARQUITECTURA DE SISTEMAS OPERATIVOS  /  GRUPO 13', font=('Segoe UI', 8),
             bg=c['bg'], fg=c['muted']).grid(row=1, column=0, sticky='w')
    state_widget = tk.Label(header, textvariable=status, font=('Segoe UI', 10, 'bold'),
                            bg=c['panel'], fg=c['accent'], padx=16, pady=8)
    state_widget.grid(row=0, column=1, rowspan=2)
    toolbar = panel(root)
    toolbar.grid(row=1, column=0, sticky='ew', padx=16, pady=4)
    toolbar.columnconfigure(5, weight=1)
    button(toolbar, 'Abrir ASM', lambda: open_file()).grid(row=0, column=0, padx=(0, 6))
    case_combo = ttk.Combobox(toolbar, textvariable=case_var, width=21, state='readonly',
                             values=[f"{key} - {item['name']}" for key, item in TEST_CASES.items()])
    case_combo.grid(row=0, column=1, padx=(0, 6))
    button(toolbar, 'Cargar ejemplo', lambda: load_case()).grid(row=0, column=2, padx=(0, 6))
    export_button = button(toolbar, 'Exportar evidencia', lambda: export_report(True))
    export_button.grid(row=0, column=3, padx=(0, 6))
    report_button = button(toolbar, 'Exportar reporte', lambda: export_report(False))
    report_button.grid(row=0, column=4)
    ttk.Label(toolbar, textvariable=source_label, style='Muted.TLabel').grid(row=1, column=0, columnspan=6, sticky='w', pady=(7, 0))
    cards = ttk.Frame(root)
    cards.grid(row=2, column=0, sticky='ew', padx=16, pady=5)
    for index, (key, variable) in enumerate(metrics.items()):
        cards.columnconfigure(index, weight=1, uniform='metric')
        card = panel(cards, padding=(10, 7))
        card.grid(row=0, column=index, sticky='nsew', padx=(0 if index == 0 else 4, 0))
        ttk.Label(card, text=key, style='Muted.TLabel').pack(anchor='w')
        tk.Label(card, textvariable=variable, width=10, anchor='w', font=('Consolas', 16, 'bold'),
                 bg=c['panel'], fg=c['accent'] if key == 'ACC' else c['ink']).pack(anchor='w', fill='x', pady=(2, 0))
    phase_area = ttk.Frame(root)
    phase_area.grid(row=3, column=0, sticky='ew', padx=16, pady=(0, 5))
    phase_widgets = []
    for index, (key, variable) in enumerate(phases.items()):
        phase_area.columnconfigure(index, weight=1, uniform='phase')
        card = panel(phase_area, padding=(10, 7))
        card.grid(row=0, column=index, sticky='nsew', padx=(0 if index == 0 else 4, 0))
        ttk.Label(card, text=f'{index + 1:02d}  {key}', foreground=c['blue'], font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        label = ttk.Label(card, textvariable=variable, wraplength=290, style='Muted.TLabel')
        label.pack(anchor='w', fill='x', pady=(4, 0))
        phase_widgets.append((card, label))
    phase_area.bind('<Configure>', lambda _: [label.configure(wraplength=max(180, card.winfo_width() - 24)) for card, label in phase_widgets])
    workspace = ttk.Panedwindow(root, orient='horizontal')
    workspace.grid(row=4, column=0, sticky='nsew', padx=16, pady=2)
    left, right = panel(workspace), panel(workspace)
    workspace.add(left, weight=4)
    workspace.add(right, weight=6)
    left.columnconfigure(0, weight=1)
    left.rowconfigure(1, weight=1)
    mem_header = ttk.Frame(left, style='Panel.TFrame')
    mem_header.grid(row=0, column=0, sticky='ew', pady=(0, 6))
    mem_header.columnconfigure(0, weight=1)
    ttk.Label(mem_header, text='Memoria principal', style='Title.TLabel').grid(row=0, column=0, sticky='w')
    memory_combo = ttk.Combobox(mem_header, textvariable=filter_var, state='readonly', width=17,
                               values=['Toda la memoria', 'Instrucciones', 'Datos', 'Datos no cero'])
    memory_combo.grid(row=0, column=1, padx=(5, 0))
    mem_box = ttk.Frame(left, style='Panel.TFrame')
    mem_box.grid(row=1, column=0, sticky='nsew')
    mem_box.rowconfigure(0, weight=1)
    mem_box.columnconfigure(0, weight=1)
    tree = ttk.Treeview(mem_box, columns=('address', 'type', 'value'), show='headings', selectmode='browse')
    for key, title, col_width in [('address', 'DIR.', 49), ('type', 'TIPO', 65), ('value', 'CONTENIDO', 180)]:
        tree.heading(key, text=title)
        tree.column(key, width=col_width, minwidth=40, anchor='w', stretch=key == 'value')
    yscroll = ttk.Scrollbar(mem_box, command=tree.yview)
    xscroll = ttk.Scrollbar(mem_box, orient='horizontal', command=tree.xview)
    tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
    tree.grid(row=0, column=0, sticky='nsew')
    yscroll.grid(row=0, column=1, sticky='ns')
    xscroll.grid(row=1, column=0, sticky='ew')
    tree.tag_configure('pc', background='#214c50', foreground='#b7ffeb')
    tree.tag_configure('changed', background='#50442b', foreground='#ffe3ac')
    tree.tag_configure('code', foreground=c['blue'])
    tree.tag_configure('data', foreground='#ffd796')
    ttk.Label(left, textvariable=memory_count, style='Muted.TLabel').grid(row=2, column=0, sticky='w', pady=(4, 0))
    edit_button = button(left, 'Editar celda seleccionada', lambda: edit_memory())
    edit_button.grid(row=3, column=0, sticky='ew', pady=(6, 0))
    right.rowconfigure(0, weight=1)
    right.columnconfigure(0, weight=1)
    notebook = ttk.Notebook(right)
    notebook.grid(row=0, column=0, sticky='nsew')

    def text_tab(title, editable=False):
        frame = ttk.Frame(notebook, style='Panel.TFrame')
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        notebook.add(frame, text=title)
        widget = tk.Text(frame, bg=c['field'], fg=c['ink'], insertbackground=c['accent'],
                         selectbackground='#365075', font=('Consolas', 10), wrap='word',
                         relief='flat', padx=10, pady=10, undo=editable)
        widget.grid(row=0, column=0, sticky='nsew')
        scrollbar = ttk.Scrollbar(frame, command=widget.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        widget.configure(yscrollcommand=scrollbar.set)
        if not editable:
            widget.configure(state='disabled')
        return frame, widget

    _, log = text_tab('Traza')
    log.tag_configure('explanation', foreground=c['accent'], spacing1=6, spacing3=6)
    _, printer = text_tab('Impresora')
    editor_frame, editor = text_tab('Editor ASM', True)
    editor.insert('1.0', '# DATA inicializa datos y no ocupa direcciones de código.\nDATA 10 10\nDATA 11 20\nLOAD 10\nADD 11\nSTORE 20\nOUTPUT\nHALT\n')
    editor_actions = ttk.Frame(editor_frame, style='Panel.TFrame')
    editor_actions.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(6, 0))
    button(editor_actions, 'Cargar desde editor', lambda: load_editor(), style='Primary.TButton').pack(side='left', padx=(0, 6))
    button(editor_actions, 'Guardar ASM', lambda: save_editor()).pack(side='left')
    ttk.Label(editor_frame, textvariable=editor_status, style='Muted.TLabel', wraplength=440).grid(row=2, column=0, columnspan=2, sticky='w', pady=(5, 0))
    _, help_text = text_tab('Ayuda')
    _, report_text = text_tab('Reporte')

    def append(widget, message):
        widget.configure(state='normal')
        tag = ('explanation',) if widget is log and message.lstrip().startswith('EXPLICACIÓN') else ()
        widget.insert('end', message + '\n', tag)
        widget.see('end')
        widget.configure(state='disabled')

    def replace_text(widget, value):
        widget.configure(state='normal')
        widget.delete('1.0', 'end')
        widget.insert('1.0', value)
        widget.configure(state='disabled')

    append(help_text, 'VM STUDIO · GUÍA RÁPIDA\n\n1. Carga un ejemplo o escribe ASM y pulsa Cargar desde editor.\n2. F7 completa una instrucción; F5 ejecuta; F6 pausa.\n3. Revisa memoria, registros, traza y Reporte.\n\nLOAD dir    Mem[dir] -> ACC\nSTORE dir   ACC -> Mem[dir]\nADD dir     ACC + Mem[dir]\nSUB dir     ACC - Mem[dir]\nJMP dir     Salto incondicional\nJZ / JNZ    Salto según Z\nINPUT       Leer un entero\nOUTPUT      Emitir ACC\nHALT        Detener\n\nDATA dir valor inicializa un dato sin ocupar dirección de código. Direcciones: 0 a 99. Comentarios: # o //. ACC es implícito: LOAD ACC no es válido.\n\nUna carga inválida conserva el programa previo. El editor pendiente no se ejecuta: primero cárgalo. Reiniciar restaura la fuente y los datos iniciales.\n\nCancelar INPUT permite reintentar. Un error exige reiniciar o cargar otro programa. El límite cuenta todos los ciclos desde la carga, incluidos pasos manuales.\n\nMemoria: verde indica el siguiente PC; ámbar, los cambios del último paso. Datos incluye ceros.\n\nReportes: HTML imprimible; CSV para Excel; JSON con toda la evidencia. No requieren Internet.')

    def output(message):
        append(log, message)
        if message.startswith('[DISPOSITIVO IMPRESORA]'):
            append(printer, f'> {vm.acc}')

    def keyboard():
        scheduler['input'] = True
        refresh()
        try:
            value = simpledialog.askinteger('Teclado virtual', 'Número entero para INPUT:', parent=root)
        finally:
            scheduler['input'] = False
        if value is None:
            raise InputCancelled('Entrada cancelada')
        return value

    vm = VirtualMachine(input_handler=keyboard, output_handler=output)
    controls = panel(root)
    controls.grid(row=5, column=0, sticky='ew', padx=16, pady=(6, 4))
    controls.columnconfigure(4, weight=1)
    step_button = ttk.Button(controls, text='Paso  F7', command=lambda: single_step())
    step_button.grid(row=0, column=0, padx=(0, 6))
    run_button = ttk.Button(controls, text='Ejecutar  F5', command=lambda: run(), style='Primary.TButton')
    run_button.grid(row=0, column=1, padx=(0, 6))
    pause_button = ttk.Button(controls, text='Pausar  F6', command=lambda: pause())
    pause_button.grid(row=0, column=2, padx=(0, 6))
    reset_button = button(controls, 'Reiniciar', lambda: reset())
    reset_button.grid(row=0, column=3, padx=(0, 10))
    speed_box = ttk.Frame(controls, style='Panel.TFrame')
    speed_box.grid(row=0, column=4, sticky='ew', padx=(0, 10))
    speed_box.columnconfigure(0, weight=1)
    ttk.Label(speed_box, textvariable=speed_label, style='Muted.TLabel').grid(row=0, column=0)
    ttk.Scale(speed_box, from_=30, to=1000, variable=speed,
              command=lambda value: speed_label.set(f'{int(float(value))} ms por instrucción')).grid(row=1, column=0, sticky='ew')
    ttk.Label(controls, text='Límite de ciclos', style='Muted.TLabel').grid(row=0, column=5, padx=(0, 6))
    limit_widget = ttk.Spinbox(controls, from_=1, to=100000, textvariable=limit, width=7)
    limit_widget.grid(row=0, column=6)
    footer = tk.Frame(root, bg=c['bg'])
    footer.grid(row=6, column=0, sticky='ew', padx=16, pady=(0, 8))
    footer.columnconfigure(0, weight=1)
    result_widget = tk.Label(footer, textvariable=result_label, bg=c['bg'], fg=c['muted'],
                             anchor='w', font=('Segoe UI', 9), justify='left')
    result_widget.grid(row=0, column=0, sticky='ew')
    hint_widget = tk.Label(footer, textvariable=hint, bg=c['bg'], fg=c['muted'], anchor='w',
                           font=('Segoe UI', 9), justify='left', wraplength=900)
    hint_widget.grid(row=1, column=0, sticky='ew', pady=(3, 0))
    footer.bind('<Configure>', lambda event: [widget.configure(wraplength=max(400, event.width - 12)) for widget in (hint_widget, result_widget)])

    def dirty():
        return source['text'] is not None and editor.get('1.0', 'end-1c') != source['text']

    def brief(value, length=18):
        text = str(value)
        return text if len(text) <= length else text[:length - 1] + '…'

    def enabled(widget, value):
        widget.configure(state='normal' if value else 'disabled')

    def result_summary():
        key = source['case']
        if key is None:
            return 'Programa propio · Comprueba registros, memoria e impresora.', c['muted']
        expected = TEST_CASES[key]['expected']
        if not vm.halted:
            return f'Esperado: {expected}', c['muted']
        targets = {'1': (30, {20: 30}), '2': (20, {20: 20}), '3': (30, {20: 30}), '4': (111, {}), '5': (6, {53: 6})}
        if key == '6':
            if len(vm.input_values) != 1:
                return 'La prueba requiere una entrada válida.', c['red']
            acc, cells = vm.input_values[0], {20: vm.input_values[0]}
            expected = f'ACC y Mem[20] iguales a la entrada ({acc})'
        else:
            acc, cells = targets[key]
        correct = (vm.error is None and vm.acc == acc and vm.outputs == [acc]
                   and all(vm.memory.read(address) == value for address, value in cells.items()))
        return (f"{'CORRECTO' if correct else 'REVISAR'} · ACC={brief(vm.acc)} · salida={brief(vm.outputs)} · {expected}",
                c['accent'] if correct else c['red'])

    def update_report(force=False):
        selected = notebook.tab(notebook.select(), 'text')
        token = (vm.cycles, vm.error, vm.halted, vm.program_name, len(vm.manual_edits), vm.last_trace.get('EXECUTE'), scheduler['running'])
        if not force and (selected != 'Reporte' or token == view['report_token']):
            return
        view['report_token'] = token
        if not vm.program_loaded:
            replace_text(report_text, 'REPORTE DE EJECUCIÓN\n\nCarga un programa para registrar su ejecución.\nDespués puedes exportar HTML, CSV o JSON desde la barra superior.')
            return
        state = 'ERROR' if vm.error else 'FINALIZADA' if vm.halted else 'EN EJECUCIÓN' if scheduler['running'] else 'PAUSADA' if vm.cycles else 'LISTA'
        lines = [f'REPORTE · {source["name"]}', '', f'Estado: {state}', f'PC: {vm.pc:02d}   IR: {vm.ir or "NINGUNO"}',
                 f'ACC: {vm.acc}   Z: {int(vm.flag_z)}   N: {int(vm.flag_n)}', f'Ciclos completados: {vm.cycles}',
                 f'Entradas: {vm.input_values}', f'Impresora: {vm.outputs}', f'Datos iniciales: {vm.initial_data}']
        if vm.error:
            lines.extend(['', f'DIAGNÓSTICO: {vm.error}'])
        lines.extend(['', 'HISTORIAL POR INSTRUCCIÓN'])
        if len(vm.history) > 200:
            lines.append(f'Últimos 200 de {len(vm.history)} pasos. La exportación conserva todos.')
        for item in vm.history[-200:]:
            changes = '; '.join(f'Mem[{change["direccion"]}] {change["antes"]} -> {change["despues"]}' for change in item['cambios_memoria']) or 'Memoria sin cambios'
            lines.extend([f'{item["ciclo"]:04d}  {item["instruccion"]} | PC {item["pc_antes"]:02d} -> {item["pc_despues"]:02d}',
                          f'      ACC {item["acc_antes"]} -> {item["acc_despues"]} | Z={int(item["z"])} N={int(item["n"])}', f'      {changes}'])
        if not vm.history:
            lines.append('No hay instrucciones completadas todavía.')
        lines.extend(['', 'Exportar reporte: HTML imprimible · CSV para Excel · JSON completo.'])
        replace_text(report_text, '\n'.join(lines))

    def refresh():
        loaded = vm.program_loaded
        pending = dirty()
        locked = scheduler['running'] or scheduler['busy']
        metrics['PC'].set(f'{vm.pc:02d}')
        metrics['IR'].set(brief(vm.ir or 'NINGUNO', 16))
        metrics['ACC'].set(brief(vm.acc, 16))
        metrics['FLAGS'].set(f'Z {int(vm.flag_z)}   N {int(vm.flag_n)}')
        metrics['CICLOS'].set(str(vm.cycles))
        status.set('ERROR' if vm.error else 'FINALIZADA' if vm.halted else
                   'ESPERANDO INPUT' if scheduler['input'] else 'EJECUTANDO' if scheduler['running'] else
                   'SIN PROGRAMA' if not loaded else 'LISTA' if not vm.cycles else 'PAUSADA')
        state_widget.configure(fg=c['red'] if vm.error else c['accent'])
        for phase, variable in phases.items():
            variable.set(vm.last_trace.get(phase, 'Esperando una instrucción'))
        selection, old_scroll = tree.selection(), tree.yview()[0]
        tree.delete(*tree.get_children())
        changed = {item['direccion'] for item in vm.history[-1]['cambios_memoria']} if vm.history else set()
        count = 0
        for address, value in enumerate(vm.memory.cells):
            code = isinstance(value, Instruction)
            mode = filter_var.get()
            if mode == 'Instrucciones' and not code or mode == 'Datos' and code or mode == 'Datos no cero' and (code or value == 0):
                continue
            tag = 'pc' if address == vm.pc and loaded and not vm.halted else 'changed' if address in changed else 'code' if code else 'data'
            tree.insert('', 'end', iid=str(address), values=(f'{address:02d}', 'CÓDIGO' if code else 'DATO', str(value)), tags=(tag,))
            count += 1
        if selection and tree.exists(selection[0]):
            tree.selection_set(selection[0])
        tree.yview_moveto(old_scroll)
        if scheduler['running'] and tree.exists(str(vm.pc)):
            tree.see(str(vm.pc))
        memory_count.set(f'{count} de 100 celdas · verde: PC · ámbar: cambio')
        for widget in action_buttons:
            enabled(widget, not locked)
        enabled(reset_button, loaded and not locked)
        enabled(edit_button, loaded and not locked and not vm.error)
        enabled(export_button, loaded and not locked)
        enabled(report_button, loaded and not locked)
        can_execute = loaded and not vm.error and not vm.halted and not locked and not pending
        enabled(step_button, can_execute)
        enabled(run_button, can_execute)
        enabled(pause_button, scheduler['running'] and not scheduler['busy'])
        case_combo.configure(state='disabled' if locked else 'readonly')
        limit_widget.configure(state='disabled' if locked else 'normal')
        editor.configure(state='disabled' if locked else 'normal')
        source_label.set((source['name'] if loaded else 'SIN PROGRAMA') + (' · CAMBIOS SIN CARGAR' if pending else ''))
        lines = int(editor.index('end-1c').split('.')[0])
        editor_status.set(f'{lines} líneas · ' + ('Cambios sin cargar. Pulsa Cargar desde editor.' if pending else 'Programa cargado en la máquina.' if loaded else 'Pulsa Cargar desde editor para comenzar.'))
        result, color = result_summary()
        result_label.set(result)
        result_widget.configure(fg=color)
        if vm.error:
            hint.set(vm.error + ' · Reinicia o carga otro programa válido.')
        elif pending:
            hint.set('El editor tiene cambios sin cargar. Cárgalos antes de ejecutar; el reporte conserva el programa activo.')
        elif view['notice']:
            hint.set(view['notice'])
        elif vm.last_trace.get('EXECUTE', '').startswith('Entrada cancelada'):
            hint.set('Entrada cancelada. Pulsa Paso o Ejecutar para reintentar la misma instrucción.')
        elif vm.halted:
            hint.set('HALT completado. Revisa el Reporte, exporta resultados o reinicia para repetir.')
        elif not loaded:
            hint.set('Comienza con Cargar ejemplo o abre Editor ASM. Cada paso ejecuta una instrucción completa.')
        else:
            hint.set(f'{vm.cycles} instrucciones completadas · PC señala la siguiente · F7 paso / F5 ejecutar / F6 pausa')
        update_report()

    def pause():
        if scheduler['busy']:
            return
        if scheduler['id'] is not None:
            root.after_cancel(scheduler['id'])
        scheduler.update(id=None, running=False)
        refresh()

    def guarded(action, title='VM Studio'):
        if scheduler['busy'] or scheduler['running']:
            return
        scheduler['busy'] = True
        refresh()
        try:
            action()
        except Exception as exc:
            view['notice'] = str(exc)
            messagebox.showerror(title, str(exc), parent=root)
        finally:
            scheduler['busy'] = False
            refresh()

    def set_editor(text):
        view['sync'] = True
        editor.configure(state='normal')
        editor.delete('1.0', 'end')
        editor.insert('1.0', text)
        editor.edit_reset()
        editor.edit_modified(False)
        view['sync'] = False

    def after_load(name, text, case=None):
        source.update(name=name, text=text, case=case)
        view.update(notice='', report_token=None)
        replace_text(log, '\n'.join(vm.execution_log) + '\n')
        replace_text(printer, '')
        set_editor(text)
        update_report(True)

    def install(text, name, case=None):
        vm.load_source(text, name)
        after_load(name, text, case)

    def open_file():
        def action():
            path = filedialog.askopenfilename(parent=root, filetypes=[('Programa ASM', '*.asm'), ('Texto', '*.txt'), ('Todos', '*.*')])
            if path:
                install(DiskController.read_source(path), os.path.basename(path))
        guarded(action)

    def load_case():
        def action():
            key = case_var.get().split(' - ')[0]
            case = TEST_CASES[key]
            text = DiskController.read_source(os.path.join(EXAMPLES_DIR, case['file']))
            install(text, case['name'], key)
        guarded(action)

    def load_editor():
        text = editor.get('1.0', 'end-1c')
        guarded(lambda: install(text, 'Programa del editor'))

    def save_editor():
        def action():
            path = filedialog.asksaveasfilename(parent=root, defaultextension='.asm', filetypes=[('Programa ASM', '*.asm')])
            if path:
                Path(path).write_text(editor.get('1.0', 'end-1c'), encoding='utf-8')
                view['notice'] = 'ASM guardado: ' + str(Path(path).resolve())
        guarded(action)

    def reset():
        if not vm.program_loaded:
            return
        def action():
            vm.restart()
            after_load(source['name'], vm.program_source, source['case'])
        guarded(action)

    def validate_limit():
        try:
            number = int(limit.get().strip())
        except (ValueError, TypeError):
            raise ValueError('El límite de ciclos debe ser un entero positivo, por ejemplo 10000.') from None
        if number <= 0:
            raise ValueError('El límite de ciclos debe ser mayor que cero.')
        return number

    def advance():
        if scheduler['busy']:
            return False
        scheduler['busy'] = True
        view['notice'] = ''
        try:
            ceiling = validate_limit()
            if vm.cycles >= ceiling:
                vm.error = 'Límite de ciclos alcanzado: posible bucle infinito.'
                raise TimeoutError(vm.error)
            refresh()
            vm.step()
        except InputCancelled:
            scheduler['running'] = False
            view['notice'] = 'Entrada cancelada. Pulsa Paso o Ejecutar para reintentar.'
            return False
        except Exception as exc:
            scheduler['running'] = False
            view['notice'] = str(exc)
            append(log, f'ERROR: {exc}')
            messagebox.showerror('Ejecución detenida', str(exc), parent=root)
            return False
        finally:
            scheduler['busy'] = False
            refresh()
        return not vm.halted

    def single_step():
        if scheduler['busy'] or scheduler['running'] or not vm.program_loaded or vm.error or vm.halted:
            return
        if dirty():
            refresh()
            return
        advance()

    def tick():
        scheduler['id'] = None
        if not scheduler['running'] or scheduler['busy']:
            return
        if advance() and scheduler['running']:
            scheduler['id'] = root.after(max(30, int(float(speed.get()))), tick)
        else:
            scheduler['running'] = False
            refresh()

    def run():
        if scheduler['busy'] or scheduler['running'] or not vm.program_loaded or vm.error or vm.halted or dirty():
            return
        try:
            validate_limit()
        except ValueError as exc:
            view['notice'] = str(exc)
            messagebox.showerror('Límite inválido', str(exc), parent=root)
            refresh()
            return
        view['notice'] = ''
        scheduler['running'] = True
        refresh()
        scheduler['id'] = root.after(0, tick)

    def edit_memory():
        def action():
            selected = tree.selection()
            if not selected:
                view['notice'] = 'Selecciona una celda de datos antes de editar.'
                return
            address = int(selected[0])
            value = vm.memory.read(address)
            if isinstance(value, Instruction):
                messagebox.showinfo('Celda de código', 'Modifica las instrucciones en Editor ASM y vuelve a cargarlo.', parent=root)
                return
            number = simpledialog.askinteger('Memoria', f'Nuevo entero para Mem[{address:02d}]:', initialvalue=value, parent=root)
            if number is not None:
                vm.edit_data(address, number)
                view['notice'] = f'Mem[{address:02d}] = {number}. ' + ('Se conservará al reiniciar.' if vm.cycles == 0 else 'Cambio de esta ejecución.')
                view['report_token'] = None
        guarded(action)

    def export_report(evidence_only):
        if not vm.program_loaded:
            view['notice'] = 'Carga un programa antes de exportar un reporte.'
            refresh()
            return
        def action():
            extension = '.json' if evidence_only else '.html'
            choices = [('Evidencia JSON', '*.json')] if evidence_only else [
                ('Reporte HTML imprimible', '*.html'), ('CSV para Excel', '*.csv'), ('Evidencia JSON', '*.json')]
            path = filedialog.asksaveasfilename(parent=root, defaultextension=extension,
                                              initialfile='reporte_vm' + extension, filetypes=choices)
            if path:
                result = save_report(build_evidence(vm), path)
                view['notice'] = 'Reporte guardado: ' + str(Path(result).resolve())
        guarded(action, 'Exportar reporte')

    def modified(_=None):
        if not editor.edit_modified():
            return
        editor.edit_modified(False)
        if not view['sync'] and not scheduler['busy']:
            view['notice'] = ''
            refresh()

    def callback_error(exc_type, exc, traceback):
        scheduler.update(running=False, busy=False)
        if scheduler['id'] is not None:
            root.after_cancel(scheduler['id'])
            scheduler['id'] = None
        view['notice'] = f'No se pudo completar la acción: {exc}'
        refresh()
        messagebox.showerror('VM Studio', view['notice'], parent=root)

    def close():
        if scheduler['busy']:
            return
        pause()
        root.destroy()

    root.report_callback_exception = callback_error
    editor.bind('<<Modified>>', modified)
    editor.edit_modified(False)
    notebook.bind('<<NotebookTabChanged>>', lambda _: update_report(True))
    filter_var.trace_add('write', lambda *_: refresh())
    root.bind('<F7>', lambda _: single_step())
    root.bind('<F5>', lambda _: run())
    root.bind('<F6>', lambda _: pause())
    root.protocol('WM_DELETE_WINDOW', close)
    refresh()
    root.mainloop()
