@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (echo Run 1-Install.cmd first. & pause & exit /b 1)
".venv\Scripts\python.exe" -m capability.pretrain evaluate --weights checkpoints/v02-pilot.pt --tokenizer data/tokenizer-bpe.json --corpus data/prepared --split test --seq-len 64
pause
