@echo off
setlocal EnableExtensions
REM Run beside the .blend files, or drag a folder containing .blend files onto this BAT.
set "DIR=%~dp0"
if not "%~1"=="" set "DIR=%~1"
if not exist "%DIR%" (
  echo Folder not found: "%DIR%"
  pause
  exit /b 1
)
set "BLENDER="
if exist "C:\Program Files\Blender Foundation\Blender 5.3\blender.exe" set "BLENDER=C:\Program Files\Blender Foundation\Blender 5.3\blender.exe"
if not defined BLENDER if exist "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe" set "BLENDER=C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"
if not defined BLENDER if exist "C:\Program Files\Blender Foundation\Blender 4.2\blender.exe" set "BLENDER=C:\Program Files\Blender Foundation\Blender 4.2\blender.exe"
if not defined BLENDER (
  echo Blender.exe not found in the usual install paths.
  echo Edit the BLENDER path at the top of this BAT file to point to your blender.exe.
  pause
  exit /b 2
)
set "OUT=%DIR%\X4_Clothing_Audit"
if not exist "%OUT%" mkdir "%OUT%"
echo Read-only X4 clothing model audit
echo Source folder: "%DIR%"
echo Blender: "%BLENDER%"
echo Results: "%OUT%"
set /a COUNT=0
for %%F in ("%DIR%\*.blend") do (
  if exist "%%~fF" (
    echo Inspecting %%~nxF
    "%BLENDER%" -b "%%~fF" --python-exit-code 5 --python "%~dp0inspect_blend.py" -- --out "%OUT%" >> "%OUT%\run.log" 2>&1
    if errorlevel 1 echo FAILED on %%~nxF: see X4_Clothing_Audit\run.log
    set /a COUNT+=1
  )
)
echo Analysed %COUNT% blend files.
powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Path '%OUT%\*' -DestinationPath '%DIR%\X4_Clothing_Diagnostics.zip' -Force"
echo.
echo Upload the resulting X4_Clothing_Diagnostics.zip to this chat.
echo No input .blend file was modified.
pause
