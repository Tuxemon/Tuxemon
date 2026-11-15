@echo off
setlocal enabledelayedexpansion

echo === Building Tuxemon Windows Installer ===
echo.

rem ------------------------------------------------------------
rem  Determine script directory and NSIS script path
rem ------------------------------------------------------------
set "ScriptDir=%~dp0"
set "ScriptPath=%ScriptDir%setup_windows.nsi"

echo Script directory: "%ScriptDir%"
echo NSIS script:      "%ScriptPath%"
echo.

rem ------------------------------------------------------------
rem  Locate the cx_Freeze build directory
rem  cx_Freeze typically outputs something like:
rem      build/exe.win-amd64-3.10
rem  We search for any folder matching exe.*
rem ------------------------------------------------------------
echo Searching for cx_Freeze build directory...
for /d %%a in ("%ScriptDir%..\build\exe.*") do (
    set "TXMNBuildDir=%%~fa"
    goto :found
)

echo [ERROR] No cx_Freeze build directory found under build\exe.*
exit /b 1

:found
echo Found build directory: "!TXMNBuildDir!"
echo.

rem ------------------------------------------------------------
rem  Validate that the directory actually exists
rem ------------------------------------------------------------
if not exist "!TXMNBuildDir!\" (
    echo [ERROR] Build directory does not exist: "!TXMNBuildDir!"
    exit /b 1
)

rem ------------------------------------------------------------
rem  Check NSIS availability
rem ------------------------------------------------------------
echo Checking for NSIS (makensis.exe)...
where makensis.exe >nul 2>&1
if errorlevel 1 (
    echo [ERROR] NSIS not found. Install NSIS or ensure it is in PATH.
    exit /b 1
)
echo NSIS found.
echo.

rem ------------------------------------------------------------
rem  Run NSIS to build the installer
rem  We pass TXMNBuildDir as a define so NSIS can access it
rem ------------------------------------------------------------
echo Running NSIS to build installer...
makensis.exe /DTXMNBuildDir="!TXMNBuildDir!" "!ScriptPath!" /V4
if errorlevel 1 (
    echo [ERROR] NSIS build failed.
    exit /b 1
)

echo.
echo === Installer build completed successfully ===
echo Installer output should now exist as:
echo     %ScriptDir%tuxemon-installer.exe
echo.

endlocal
exit /b 0
