@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (echo Run 1-Install.cmd first. & exit /b 1)
.venv\Scripts\python.exe -m capability.capacity --parameters 9514368 --tokens 10000000
