@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  py -3 -m venv .venv
) else (
  python -m venv .venv
)
if errorlevel 1 (echo Install Python 3.11 or 3.12 first. & pause & exit /b 1)
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 (echo PyTorch install failed. & pause & exit /b 1)
python -m vardath_chat describe
pause
