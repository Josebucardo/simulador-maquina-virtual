"""Instantáneas y reportes de ejecución sin dependencias externas ni acceso a red."""
from collections import Counter
from copy import deepcopy
import csv
from datetime import datetime, timedelta, timezone
from html import escape
import io
import json
import os
from pathlib import Path
import tempfile


def build_evidence(vm, name=None, code=None, initial_data=None, outputs=None):
    """Captura el estado actual; continuar la VM no modifica esta instantánea."""
    state = dict(vm.get_state_summary())
    loaded = bool(getattr(vm, 'program_loaded', False))
    status = ('ERROR' if state.get('error') else 'FINALIZADA' if state.get('halted')
              else 'SIN PROGRAMA' if not loaded else 'LISTA' if state.get('cycles', 0) == 0 else 'PAUSADA')
    steps = deepcopy(getattr(vm, 'history', []))
    frequencies = Counter(str(step.get('instruccion', '')).split(' ')[0] for step in steps)
    jumps = [s for s in steps if str(s.get('instruccion', '')).split(' ')[0] in ('JMP', 'JZ', 'JNZ')]
    # Las banderas anteriores a un salto se conservan: los saltos no alteran ACC.
    taken = sum(1 for s in jumps if s['instruccion'].startswith('JMP ')
                or (s['instruccion'].startswith('JZ ') and s.get('z'))
                or (s['instruccion'].startswith('JNZ ') and not s.get('z')))
    statistics = dict(estado=status, ciclos=state.get('cycles', 0),
                      instrucciones=dict(sorted(frequencies.items())),
                      saltos_tomados=taken, saltos_no_tomados=len(jumps)-taken,
                      lecturas_datos=sum(frequencies[op] for op in ('LOAD', 'ADD', 'SUB')),
                      escrituras_datos=frequencies['STORE'],
                      entradas=frequencies['INPUT'], salidas=frequencies['OUTPUT'])
    evidence = dict(
        version=1, fecha=datetime.now(timezone(timedelta(hours=-6))).isoformat(timespec='seconds'),
        zona_horaria='America/Managua',
        programa=name if name is not None else getattr(vm, 'program_name', '') or 'Sin programa',
        codigo=code if code is not None else getattr(vm, 'program_source', ''),
        datos_iniciales=initial_data if initial_data is not None else getattr(vm, 'initial_data', {}),
        estado=state, estado_ejecucion=status,
        memoria=[value if type(value) is int else str(value) for value in vm.memory.cells],
        impresora=outputs if outputs is not None else getattr(vm, 'outputs', []),
        entradas=getattr(vm, 'input_values', []),
        traza=list(vm.execution_log), fases_ultima_instruccion=dict(vm.last_trace),
        pasos=steps, estadisticas=statistics, ediciones_manuales=getattr(vm, 'manual_edits', []),
    )
    return deepcopy(evidence)


def _text(value):
    return escape(str(value), quote=True)


def _rows(values):
    return ''.join('<tr>' + ''.join('<td>' + _text(cell) + '</td>' for cell in row) + '</tr>' for row in values)


def _table(headings, rows):
    return '<div class="table-wrap"><table><thead><tr>' + ''.join('<th>'+_text(h)+'</th>' for h in headings) + '</tr></thead><tbody>' + _rows(rows) + '</tbody></table></div>'


def render_html(evidence):
    """HTML autónomo e imprimible con código, registros, historia y memoria."""
    e = evidence
    state = e['estado']
    status = e['estado_ejecucion']
    statistics = e['estadisticas']
    steps = e.get('pasos', [])
    changes = lambda step: '; '.join(f"Mem[{c['direccion']}]: {c['antes']} → {c['despues']}" for c in step.get('cambios_memoria', [])) or 'Sin cambios'
    summary = _table(['Registro', 'Valor'], [(key, state.get(key)) for key in ('pc', 'ir', 'acc', 'flag_z', 'flag_n', 'cycles')])
    metrics = _table(['Medida', 'Resultado'], [(key.replace('_', ' ').capitalize(), statistics[key]) for key in ('ciclos', 'saltos_tomados', 'saltos_no_tomados', 'lecturas_datos', 'escrituras_datos', 'entradas', 'salidas')])
    history = _table(['Paso', 'Instrucción', 'PC antes → después', 'ACC antes → después', 'Z / N', 'Memoria'],
                     [(s['ciclo'], s['instruccion'], f"{s['pc_antes']} → {s['pc_despues']}",
                       f"{s['acc_antes']} → {s['acc_despues']}", f"{int(s['z'])} / {int(s['n'])}", changes(s)) for s in steps]) if steps else '<p>No se han completado instrucciones.</p>'
    memory = _table(['Dirección', 'Tipo', 'Contenido'], [(f'{i:02d}', 'Dato' if type(value) is int else 'Instrucción', value) for i, value in enumerate(e['memoria'])])
    initial = _table(['Dirección', 'Valor'], sorted(e.get('datos_iniciales', {}).items(), key=lambda x: int(x[0])))
    manual = _table(['Ciclo', 'Dirección', 'Antes', 'Después'], [(v.get('ciclo'), v.get('direccion'), v.get('antes'), v.get('despues')) for v in e.get('ediciones_manuales', [])]) if e.get('ediciones_manuales') else '<p>No se registraron ediciones manuales.</p>'
    phases = _table(['Fase', 'Descripción'], e.get('fases_ultima_instruccion', {}).items())
    frequency_table = _table(['Instrucción', 'Ejecuciones'], statistics.get('instrucciones', {}).items())
    detail = ''.join('<details><summary>Paso '+_text(s['ciclo'])+' · '+_text(s['instruccion'])+'</summary><p>'+_text(s.get('explicacion', ''))+'</p>'+_table(['Fase', 'Descripción'], s.get('fases', {}).items())+'</details>' for s in steps)
    error = '<p class="error"><strong>Diagnóstico:</strong> '+_text(state['error'])+'</p>' if state.get('error') else ''
    code = '\n'.join(f'{n:>3}  {line}' for n, line in enumerate(e.get('codigo', '').splitlines(), 1))
    return '''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Reporte de ejecución VM Studio</title><style>
*{box-sizing:border-box}body{margin:0;background:#eef2f6;color:#172737;font:15px/1.55 'Segoe UI',Arial,sans-serif}main{max-width:1100px;margin:32px auto;background:white;padding:40px 48px}h1{font-size:32px;line-height:1.15;margin:8px 0 20px}h2{font-size:22px;margin-top:34px;color:#173e54}h3{font-size:17px}.eyebrow{letter-spacing:2px;font-size:12px;color:#286b70}.meta{color:#5b6874}table{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0 20px}th,td{padding:9px 11px;border:1px solid #d7e0e7;text-align:left;vertical-align:top;overflow-wrap:anywhere}th{background:#18384e;color:white}tbody tr:nth-child(even){background:#f1f5f8}.table-wrap{overflow-x:auto}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f5f7;padding:16px;font:12px/1.6 Consolas,monospace}.status{font-size:19px;font-weight:700}.error{padding:15px;border-left:4px solid #bc2949;background:#fff1f4;color:#822036}.columns{display:grid;grid-template-columns:1fr 1fr;gap:28px}details{border-top:1px solid #d7e0e7;padding:10px 0}summary{font-weight:600;cursor:pointer}.outputs{font:20px Consolas,monospace}footer{margin-top:36px;font-size:12px;color:#667783}@media(max-width:700px){main{margin:0;padding:22px}.columns{display:block}h1{font-size:27px}}@media print{@page{size:A4;margin:15mm}body{background:white;font-size:10pt}main{padding:0;margin:0;max-width:none}h1{font-size:24pt}h2{font-size:16pt;break-after:avoid}table{font-size:8pt}thead{display:table-header-group}tr{break-inside:avoid}pre{font-size:8pt}details{display:block}details>summary{display:block}details>*{display:block!important}.columns{display:block}.table-wrap{overflow:visible}a{color:inherit}}
</style></head><body><main><p class="eyebrow">VM STUDIO · GRUPO 13</p><h1>Reporte de ejecución</h1>''' + \
        '<p><strong>Programa:</strong> '+_text(e['programa'])+'</p><p class="meta">'+_text(e['fecha'])+' · '+_text(e['zona_horaria'])+'</p><p class="status">Estado: '+_text(status)+'</p>'+error + \
        '<p>Este reporte es una instantánea de la ejecución. Un estado pausado o con error no equivale a un programa finalizado correctamente.</p><div class="columns"><section><h2>Registros</h2>'+summary+'</section><section><h2>Estadísticas</h2>'+metrics+'</section></div>'+ \
        '<h2>Entrada y salida</h2><p>Entradas registradas: <span class="outputs">'+_text(e.get('entradas', []))+'</span></p><p>Impresora virtual: <span class="outputs">'+_text(e['impresora'])+'</span></p>'+ \
        '<h2>Programa ASM</h2><p>La numeración siguiente corresponde a líneas del archivo. Las direcciones de código cuentan solo instrucciones, excluyendo comentarios y DATA.</p><pre>'+_text(code)+'</pre><h3>Datos iniciales</h3>'+initial+ \
        '<h2>Historial de instrucciones</h2>'+history+'<h3>Frecuencia de operaciones</h3>'+frequency_table+ \
        '<h2>Fases de la última instrucción</h2>'+phases+'<h2>Detalle de cada paso</h2>'+detail+ \
        '<h2>Ediciones manuales de memoria</h2>'+manual+'<h2>Memoria completa</h2>'+memory+ \
        '<h2>Traza de ejecución</h2><pre>'+_text('\n'.join(e.get('traza', [])))+'</pre><footer>Arquitectura de Sistemas Operativos · Máquina virtual didáctica de 100 celdas · Sin servicios externos</footer></main></body></html>'


def _csv_safe(value):
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    value = str(value)
    return "'" + value if value.lstrip().startswith(('=', '+', '-', '@', '\t', '\r')) else value


def render_csv(evidence):
    """CSV de registros homogéneos; los textos no ejecutan fórmulas en Excel."""
    stream = io.StringIO(newline='')
    writer = csv.writer(stream, delimiter=';', lineterminator='\r\n')
    header = ['tipo', 'ciclo', 'instruccion', 'pc_antes', 'pc_despues', 'acc_antes', 'acc_despues', 'z', 'n', 'direccion', 'antes', 'despues', 'detalle']
    writer.writerow(header)

    def row(kind, **fields):
        writer.writerow([_csv_safe(kind if col == 'tipo' else fields.get(col, '')) for col in header])

    row('programa', detalle=evidence['programa'])
    row('fecha', detalle=evidence['fecha'])
    row('estado', detalle=evidence['estado_ejecucion'])
    for key, value in evidence['estado'].items():
        row('registro', instruccion=key, detalle=value)
    for step in evidence.get('pasos', []):
        fields = {key: step.get(key, '') for key in ('ciclo', 'instruccion', 'pc_antes', 'pc_despues', 'acc_antes', 'acc_despues', 'z', 'n')}
        row('paso', **fields, detalle=step.get('explicacion', ''))
        for change in step.get('cambios_memoria', []):
            row('escritura', ciclo=step['ciclo'], **change)
    for index, value in enumerate(evidence['memoria']):
        row('memoria', direccion=index, detalle=value)
    for value in evidence.get('entradas', []):
        row('entrada', detalle=value)
    for value in evidence.get('impresora', []):
        row('salida', detalle=value)
    for edit in evidence.get('ediciones_manuales', []):
        row('edicion_manual', **edit)
    return stream.getvalue()


def save_report(evidence, path):
    """Valida formato y reemplaza el archivo de forma atómica tras escribirlo."""
    destination = Path(path)
    extension = destination.suffix.lower()
    if extension not in {'.html', '.htm', '.json', '.csv'}:
        raise ValueError('Formato de reporte no válido. Utilice .html, .csv o .json.')
    snapshot = deepcopy(evidence)
    if extension == '.json':
        content = json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n'
    elif extension == '.csv':
        content = render_csv(snapshot)
    else:
        content = render_html(snapshot)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', dir=destination.parent,
                                         suffix='.tmp', delete=False,
                                         encoding='utf-8-sig' if extension == '.csv' else 'utf-8', newline='') as stream:
            temporary_path = Path(stream.name)
            stream.write(content)
        os.replace(temporary_path, destination)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
    return destination.resolve()
