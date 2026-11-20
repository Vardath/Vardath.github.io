@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (echo Run 1-Install.cmd first. & exit /b 1)
".venv\Scripts\python.exe" -m capability.chat_quality --checkpoint checkpoints\v06-modern-instruct-pilot-best.pt --tokenizer data\tokenizer-bpe.json --output reports\v07_actual_chat.json
pause
