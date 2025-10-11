@echo off
setlocal enabledelayedexpansion

echo === Building Tuxemon Windows Installer ===

rem Get the script's directory
set "ScriptDir=%~dp0"

rem Set the installer script path
set "ScriptPath=%ScriptDir%setup_windows.nsi"

rem Find the build directory (first match)
for /d %%a in ("%ScriptDir%..\build\exe.*") do (
    set "TXMNBuildDir=%%~fa"
    goto :found
)
:found

rem Validate build directory
if not exist "!TXMNBuildDir!\" (
    echo [ERROR] Build directory not found: "!TXMNBuildDir!"
    exit /b 1
)

echo ScriptPath: "!ScriptPath!"
echo TXMNBuildDir: "!TXMNBuildDir!"

rem Check for NSIS installation
where makensis.exe >nul 2>&1
if errorlevel 1 (
    echo [ERROR] NSIS not found. Ensure it's installed and added to PATH.
    exit /b 1
)

rem Run NSIS to build the installer
echo Running NSIS...
makensis.exe "!ScriptPath!" /V4
if errorlevel 1 (
    echo [ERROR] NSIS build failed.
    exit /b 1
)

rem Confirm installer was created
set "InstallerPath=%ScriptDir%tuxemon-installer.exe"
if not exist "!InstallerPath!" (
    echo [ERROR] Installer not created: "!InstallerPath!"
    exit /b 1
)

echo Installer build complete: "!InstallerPath!"

endlocal
exit /b 0
