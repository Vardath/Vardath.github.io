@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (echo Run 1-Install.cmd first. & exit /b 1)
echo NOTE: This checkpoint is EXPERIMENTAL and not capable general-purpose chat.
".venv\Scripts\python.exe" -m capability.modern_server --checkpoint checkpoints\v06-modern-instruct-pilot-best.pt --tokenizer data\tokenizer-bpe.json --host 127.0.0.1 --port 8080
