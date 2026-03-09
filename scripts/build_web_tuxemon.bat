@echo off
setlocal enableextensions

REM Build the full Tuxemon pygame client for browsers via pygbag (Windows CMD).
REM Prefer Python Launcher (py) to avoid Microsoft Store python alias issues.

set "ROOT_DIR=%~dp0.."
for %%I in ("%ROOT_DIR%") do set "ROOT_DIR=%%~fI"
set "WEB_APP_DIR=%ROOT_DIR%\web"
set "OUT_DIR=%ROOT_DIR%\build\web"
set "PY_CMD=py"

where py >nul 2>nul
if errorlevel 1 (
  where python >nul 2>nul
  if errorlevel 1 (
    echo Neither 'py' nor 'python' was found on PATH.
    echo Install Python from https://www.python.org/downloads/windows/
    echo and enable the Python Launcher.
    goto :error
  )
  set "PY_CMD=python"
)

if not exist "%OUT_DIR%" mkdir "%OUT_DIR%"

%PY_CMD% -c "import pygbag" >nul 2>nul
if errorlevel 1 (
  echo Installing pygbag...
  %PY_CMD% -m pip install pygbag || goto :error
)

if exist "%WEB_APP_DIR%" rmdir /s /q "%WEB_APP_DIR%"
mkdir "%WEB_APP_DIR%" || goto :error

copy /y "%ROOT_DIR%\run_tuxemon.py" "%WEB_APP_DIR%\main.py" >nul || goto :error
xcopy "%ROOT_DIR%\tuxemon" "%WEB_APP_DIR%\tuxemon" /E /I /Q /Y >nul || goto :error
xcopy "%ROOT_DIR%\mods" "%WEB_APP_DIR%\mods" /E /I /Q /Y >nul || goto :error
copy /y "%ROOT_DIR%\requirements.txt" "%WEB_APP_DIR%\requirements.txt" >nul || goto :error

%PY_CMD% -m pygbag --build --archive --ume_block 0 --app_name Tuxemon --disable-sound-format-error "%WEB_APP_DIR%" || goto :error

if exist "%WEB_APP_DIR%\build\web" (
  if exist "%OUT_DIR%" rmdir /s /q "%OUT_DIR%"
  mkdir "%ROOT_DIR%\build" >nul 2>nul
  move "%WEB_APP_DIR%\build\web" "%OUT_DIR%" >nul || goto :error
)

echo Built browser package at: %OUT_DIR%
exit /b 0

:error
echo Build failed.
exit /b 1
