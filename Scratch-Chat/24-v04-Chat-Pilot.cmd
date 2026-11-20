@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (echo Run 1-Install.cmd first. & exit /b 1)
echo WARNING: this scratch-trained pilot is not a reliable general-purpose chat model.
.venv\Scripts\python.exe -m capability.instruct chat --checkpoint checkpoints\v04-instruct-earlystop-best.pt --tokenizer data\tokenizer-bpe.json
