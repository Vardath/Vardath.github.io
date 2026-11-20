@echo off
cd /d "%~dp0"
if not exist "data\prepared\train.jsonl" (
 echo First prepare a substantial legally usable text corpus.
 pause
 exit /b 1
)
.venv\Scripts\python.exe -m capability.modern_train train --corpus data\prepared --tokenizer data\tokenizer-bpe.json --checkpoint checkpoints\v05-modern.pt --steps 500 --width 256 --layers 8 --heads 8 --context-size 2048 --seq-len 256 --batch 2 --grad-accum 4 --min-train-tokens 1000000
pause
