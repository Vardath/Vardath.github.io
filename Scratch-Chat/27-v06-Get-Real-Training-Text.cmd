@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (echo Run 1-Install.cmd first. & exit /b 1)
echo Downloading verified WikiText-2 text, approximately 8 MB. Internet required.
.venv\Scripts\python.exe -m pip install "pyarrow>=18,<24"
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m capability.wiki_parquet --cache data\wiki-parquet\downloads --out data\wiki-parquet\prepared
if errorlevel 1 exit /b 1
echo WikiText pretraining data is prepared. It is NOT a complete general-purpose training corpus.
pause
