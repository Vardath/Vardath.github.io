@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (echo Run 1-Install.cmd first. & pause & exit /b 1)
".venv\Scripts\python.exe" -m vardath_chat train --data data\starter.jsonl --out checkpoints\starter.pt --steps 800
pause
