@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (echo Run 1-Install.cmd first. & pause & exit /b 1)
echo This is a pretraining pilot, not an instruction-following assistant.
".venv\Scripts\python.exe" -m capability.pretrain sample --weights checkpoints/v02-pilot.pt --tokenizer data/tokenizer-bpe.json --prompt "JANUS is" --max-new-tokens 80
pause
