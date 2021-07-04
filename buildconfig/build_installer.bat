@echo off

echo This script is intended to be run in wine, or with nsis already installed in it's default path.

rem Set the installer and the build path ----------------------

set ScriptPath=%cd%\setup_windows.nsi

rem Propably terrible way to get build folder
cd ..
cd build
cd exe*

set TXMNBuildDir=%cd%

rem (Debugging only) print variables

echo ScriptPath: %ScriptPath%
echo TXMNBuildDir: %TXMNBuildDir%



C:
cd "%ProgramFiles(x86)%\NSIS\"

makensis.exe %ScriptPath% /V4
