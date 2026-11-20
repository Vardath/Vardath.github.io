@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (echo Run 1-Install.cmd first. & exit /b 1)
if not exist data\instruct-pilot\train.jsonl (call 21-v04-Prepare-Chat-Pilot.cmd)
if errorlevel 1 exit /b 1
if exist checkpoints\v04-instruct-earlystop.pt (echo A checkpoint already exists. Rename it or choose a new output before retraining. & exit /b 1)
echo Training a toy-sized original chat model. This is NOT a general-purpose assistant.
.venv\Scripts\python.exe -m capability.instruct train --data data\instruct-pilot --tokenizer data\tokenizer-bpe.json --checkpoint checkpoints\v04-instruct-earlystop.pt --steps 350 --batch 4 --threads 2 --lr 0.001 --eval-every 25 --save-every 50 --early-stop-evals 4
