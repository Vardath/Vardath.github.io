@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Install Python dependencies first using 1-Install.cmd
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m capability.cli prepare --manifest data\corpus\manifest.json --out data\prepared
if errorlevel 1 (pause & exit /b 1)
.venv\Scripts\python.exe -m capability.cli tokenizer --corpus data\prepared --out data\tokenizer-bpe.json --merges 384
if errorlevel 1 (pause & exit /b 1)
.venv\Scripts\python.exe -m capability.cli stats --corpus data\prepared --tokenizer data\tokenizer-bpe.json
pause
