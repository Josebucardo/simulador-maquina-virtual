@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
    python simulador_vm.py
) else (
    py -3 simulador_vm.py
)
if errorlevel 1 pause
