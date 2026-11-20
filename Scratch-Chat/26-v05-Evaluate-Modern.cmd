@echo off
cd /d "%~dp0"
.venv\Scripts\python.exe -m capability.modern_train evaluate --corpus data\prepared --tokenizer data\tokenizer-bpe.json --checkpoint checkpoints\v05-modern.pt
pause
