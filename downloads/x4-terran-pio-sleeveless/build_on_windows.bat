@echo off
setlocal
set "ROOT=%~dp0"
set "BLENDER="
for %%V in (5.1 4.2 5.3) do (
    if not defined BLENDER if exist "%ProgramFiles%\Blender Foundation\Blender %%V\blender.exe" set "BLENDER=%ProgramFiles%\Blender Foundation\Blender %%V\blender.exe"
)
if not defined BLENDER (
    echo Blender 5.1 was not located. Install it from Blender, or edit this batch file's BLENDER variable.
    pause
    exit /b 1
)
echo Using "%BLENDER%"
echo The Blender project files, including yishabody.blend, must be in the same folder as this batch file or a subfolder.
echo This script uses X4 XAC Tools to write an extension automatically, without modifying the original game archives.
"%BLENDER%" --background --python "%ROOT%tools\auto_edit_and_build.py" -- --sources "%ROOT%"
if errorlevel 1 (
    echo.
    echo Build failed safely. No claim of a completed clothing mod.
    echo See the errors above. You can send a screenshot of them.
    pause
    exit /b 1
)
echo.
echo Done. See Vardath_Terran_PIO_Sleeveless_Dresses.zip in this folder.
echo Test the in-game appearance before relying on the extension.
pause
