@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (echo Run 1-Install.cmd first. & pause & exit /b 1)
echo WARNING: Full 9.5M model training requires a MUCH LARGER approved corpus.
echo This script refuses the tiny bundled example dataset.
".venv\Scripts\python.exe" -m capability.pretrain train --corpus data/prepared --tokenizer data/tokenizer-bpe.json --token-cache data/token-cache --output checkpoints/v02-10m-user.pt --steps 1000 --width 384 --layers 5 --heads 6 --model-context 1024 --seq-len 128 --batch 2 --grad-accum 4 --lr 0.0003 --min-lr 0.00003 --warmup 200 --decay-steps 20000 --save-every 50 --eval-every 50 --threads 4 --device cpu --min-train-tokens 1000000 --min-validation-tokens 10000
pause
