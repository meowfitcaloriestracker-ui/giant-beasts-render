@echo off
setlocal
cd /d "%~dp0"
echo ============================================
echo   Blender GPU test - please wait
echo ============================================
set "BL=%~dp0blender\blender-4.5.0-windows-x64\blender.exe"
if exist "%BL%" goto render
echo [1/3] Downloading Blender 4.5 portable - about 400 MB ...
curl.exe -L -o blender.zip https://download.blender.org/release/Blender4.5/blender-4.5.0-windows-x64.zip
if errorlevel 1 goto fail
echo [2/3] Unzipping ...
mkdir blender 2>nul
tar.exe -xf blender.zip -C blender
del blender.zip
if not exist "%BL%" goto fail
:render
echo [3/3] Rendering 60 test frames at 1920x1080 ...
"%BL%" -b --factory-startup --python "%~dp0dino3d.py" -- bench "%~dp0frames" 60 > log.txt 2>&1
type result.txt
echo.
echo DONE - you can close this window. Tell Claude: done
pause
exit /b 0
:fail
echo FAILED > result.txt
echo Something failed - tell Claude
pause
