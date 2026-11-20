@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (echo Run 1-Install.cmd and 16-v03-Install-Dataset-Tools.cmd first. & exit /b 1)
.venv\Scripts\python.exe -m capability.wikitext --source hf --dataset wikitext-2-raw-v1 --out data\wikitext2\prepared
