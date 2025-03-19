@echo off
setlocal

echo Building Tuxemon Windows Installer...

rem Get the script's directory
set ScriptDir=%~dp0

rem Set the installer script path
set ScriptPath="%ScriptDir%setup_windows.nsi"

rem Find the build directory
for /d %%a in ("%ScriptDir%..\build\exe.*") do (
    set "TXMNBuildDir=%%~fa"
)

rem Check if the build directory exists
if not exist "%TXMNBuildDir%\" (
    echo Error: Build directory not found: "%TXMNBuildDir%"
    exit /b 1
)

echo ScriptPath: "%ScriptPath%"
echo TXMNBuildDir: "%TXMNBuildDir%"

rem Check for NSIS installation
where makensis.exe >nul 2>&1
if errorlevel 1 (
    echo Error: NSIS not found. Make sure it's installed and in your PATH.
    exit /b 1
)

rem Build the installer
makensis.exe "%ScriptPath%" /V4
if errorlevel 1 (
    echo Error: NSIS build failed.
    exit /b 1
)

echo Installer build complete.

endlocal
exit /b 0
