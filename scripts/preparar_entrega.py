"""Empaqueta exclusivamente código, documentación y materiales de entrega."""
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = ('src', 'tests', 'scripts', 'docs', 'examples', 'presentation')
OUTPUTS = ('output/pdf', 'output/word', 'output/manual', 'output/exposicion', 'output/presentacion', 'output/reportes')
EXCLUDED = {'__pycache__', 'node_modules', '.git', '.venv', 'venv', '.pytest_cache'}


def files_to_share():
    for name in ('.gitattributes', '.gitignore', 'README.md', 'simulador_vm.py', 'pyproject.toml', 'INICIAR_VM.cmd', 'VERIFICAR_PROYECTO.cmd'):
        path = ROOT / name
        if path.is_file():
            yield path
    for folder in (*FOLDERS, *OUTPUTS):
        for path in (ROOT / folder).rglob('*'):
            if (path.is_file() and not EXCLUDED.intersection(path.relative_to(ROOT).parts)
                    and path.suffix not in {'.pyc', '.tmp'} and not path.name.startswith('~$')):
                yield path


def main():
    destination = ROOT / 'output/compartir/VM_STUDIO_GRUPO13.zip'
    destination.parent.mkdir(parents=True, exist_ok=True)
    items = sorted(set(files_to_share()))
    with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED) as package:
        for path in items:
            package.write(path, 'VM_STUDIO_GRUPO13/' + path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(destination) as package:
        bad = package.testzip()
        if bad:
            raise RuntimeError(f'El ZIP no pudo verificarse: {bad}')
    print(f'Paquete: {destination}')
    print(f'Archivos: {len(items)} | Tamaño: {destination.stat().st_size:,} bytes')


if __name__ == '__main__':
    main()
