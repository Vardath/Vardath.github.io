@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (echo Run 1-Install.cmd first. & pause & exit /b 1)
".venv\Scripts\python.exe" -m capability.token_cache --corpus data/prepared --tokenizer data/tokenizer-bpe.json --output data/token-cache
pause
