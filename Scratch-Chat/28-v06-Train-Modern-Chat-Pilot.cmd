@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (echo Run 1-Install.cmd first. & exit /b 1)
if not exist checkpoints\v05-modern-smoke.pt (echo Missing pretraining checkpoint. & exit /b 1)
echo TRAINING ON THE 51-EXAMPLE PILOT. THIS IS NOT A CAPABLE LANGUAGE MODEL.
.venv\Scripts\python.exe -m capability.modern_instruct train --base checkpoints\v05-modern-smoke.pt --tokenizer data\tokenizer-bpe.json --data data\instruct-pilot --checkpoint checkpoints\v06-modern-instruct-new.pt --steps 150 --batch 4 --eval-every 25 --save-every 25 --patience-evals 3
pause
