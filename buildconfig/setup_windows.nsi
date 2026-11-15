; ------------------------------------------------------------
;  Tuxemon Windows Installer
;  Builds a Windows installer using NSIS + cx_Freeze output
;  This script expects TXMNBuildDir to be passed in via:
;      makensis.exe /DTXMNBuildDir="path"
; ------------------------------------------------------------

Name "Tuxemon"
Icon "../mods/tuxemon/gfx/icon.ico"
OutFile "tuxemon-installer.exe"

; Request admin rights (required for Program Files installation)
RequestExecutionLevel admin

; Use Unicode installer (modern Windows compatibility)
Unicode True

; Default installation directory
InstallDir $PROGRAMFILES\Tuxemon

; ------------------------------------------------------------
;  Version Information
; ------------------------------------------------------------
!define VERSION "0.4.35"
VIProductVersion "${VERSION}.0"
VIAddVersionKey "ProductName" "Tuxemon"
VIAddVersionKey "FileVersion" "${VERSION}"
VIAddVersionKey "FileDescription" "Tuxemon is a free, open source monster-fighting RPG."
VIAddVersionKey "LegalCopyright" "GNU GPL v3"

; ------------------------------------------------------------
;  Modern UI Setup
; ------------------------------------------------------------
!include "MUI2.nsh"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "${TXMNBuildDir}\LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

; ------------------------------------------------------------
;  Main Installation Section
; ------------------------------------------------------------
Section "Tuxemon (required)"
  SectionIn RO

  ; Set installation output directory
  SetOutPath $INSTDIR

  ; Copy everything from the cx_Freeze build directory
  ; This includes:
  ;   - run_tuxemon.exe
  ;   - Python DLLs
  ;   - mods/
  ;   - LICENSE
  ;   - All frozen dependencies
  File /r "${TXMNBuildDir}\*"

  ; ------------------------------------------------------------
  ;  Start Menu Shortcuts
  ; ------------------------------------------------------------
  CreateDirectory "$SMPROGRAMS\Tuxemon"

  ; Main shortcut to run the game
  CreateShortcut "$SMPROGRAMS\Tuxemon\Tuxemon.lnk" "$INSTDIR\run_tuxemon.exe"

  ; Desktop shortcut
  CreateShortcut "$DESKTOP\Tuxemon.lnk" "$INSTDIR\run_tuxemon.exe"

  ; ------------------------------------------------------------
  ;  Uninstaller
  ; ------------------------------------------------------------
  WriteUninstaller "$INSTDIR\uninstall.exe"

SectionEnd

; ------------------------------------------------------------
;  Uninstall Section
; ------------------------------------------------------------
Section "Uninstall"

  ; Remove uninstaller
  Delete "$INSTDIR\uninstall.exe"

  ; Remove installed files
  RMDir /r "$INSTDIR"

  ; Remove Start Menu shortcuts
  Delete "$SMPROGRAMS\Tuxemon\*.lnk"
  RMDir "$SMPROGRAMS\Tuxemon"

  ; Remove desktop shortcut
  Delete "$DESKTOP\Tuxemon.lnk"

SectionEnd
