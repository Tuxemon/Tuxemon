@echo off
setlocal enableextensions

set "ROOT_DIR=%~dp0.."
for %%I in ("%ROOT_DIR%") do set "ROOT_DIR=%%~fI"
set "OUT_DIR=%ROOT_DIR%\build\web"
set "PORT=%~1"
set "PY_CMD=py"
if "%PORT%"=="" set "PORT=8000"

where py >nul 2>nul
if errorlevel 1 set "PY_CMD=python"

if not exist "%OUT_DIR%" (
  echo No browser build found at %OUT_DIR%
  echo Run: scripts\build_web_tuxemon.bat
  exit /b 1
)

cd /d "%OUT_DIR%" || exit /b 1
%PY_CMD% -m http.server %PORT% --bind 0.0.0.0
