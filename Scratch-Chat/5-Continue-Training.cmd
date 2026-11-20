@echo off
cd /d "%~dp0"
".venv\Scripts\python.exe" -m vardath_chat train --data data\starter.jsonl --out checkpoints\starter.pt --steps 800 --resume
pause
