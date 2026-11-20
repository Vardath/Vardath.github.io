@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (echo Run 1-Install.cmd first. & exit /b 1)
.venv\Scripts\python.exe -m capability.cli tokenizer --corpus data\wikitext2\prepared --out data\wikitext2\tokenizer-bpe.json --merges 1024 --max-chars 400000
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m capability.cli stats --corpus data\wikitext2\prepared --tokenizer data\wikitext2\tokenizer-bpe.json
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m capability.token_cache --corpus data\wikitext2\prepared --tokenizer data\wikitext2\tokenizer-bpe.json --output data\wikitext2\token-cache
