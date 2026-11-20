@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (echo Run 1-Install.cmd first. & exit /b 1)
.venv\Scripts\python.exe -m pip install -r requirements-datasets.txt
