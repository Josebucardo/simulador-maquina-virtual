@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
    python scripts/generar_evidencias.py --incluir-gui
) else (
    py -3 scripts/generar_evidencias.py --incluir-gui
)
pause
