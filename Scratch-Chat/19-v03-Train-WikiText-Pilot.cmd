@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (echo Run 1-Install.cmd first. & exit /b 1)
if not exist data\wikitext2\token-cache\metadata.json (echo Run 17-v03-Import-WikiText.cmd and 18-v03-Prepare-WikiText-Tokenizer.cmd first. & exit /b 1)
echo This is an EXPERIMENTAL language pretraining run, not a capable assistant.
echo For a 9.5M-parameter model this may take a long time on a CPU.
.venv\Scripts\python.exe -m capability.pretrain train --corpus data\wikitext2\prepared --tokenizer data\wikitext2\tokenizer-bpe.json --token-cache data\wikitext2\token-cache --output checkpoints\v03-wikitext-pilot.pt --steps 200 --width 384 --layers 5 --heads 6 --model-context 1024 --seq-len 128 --batch 2 --grad-accum 4 --min-train-tokens 100000 --min-validation-tokens 1000 --threads 4 --device cpu --save-every 20 --eval-every 20
