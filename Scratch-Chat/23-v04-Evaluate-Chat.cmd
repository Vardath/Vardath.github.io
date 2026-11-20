@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (echo Run 1-Install.cmd first. & exit /b 1)
.venv\Scripts\python.exe -m capability.instruct evaluate --checkpoint checkpoints\v04-instruct-earlystop-best.pt --tokenizer data\tokenizer-bpe.json --data data\instruct-pilot
