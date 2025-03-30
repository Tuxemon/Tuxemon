
; The name of the installer
Name "Tuxemon"

; Set the icon for the installer
Icon "../mods/tuxemon/gfx/icon.ico"

; The file to write
OutFile "tuxemon-installer.exe"

; Request application privileges for Windows Vista and higher
RequestExecutionLevel admin

; Build Unicode installer
Unicode True

; The default installation directory
InstallDir $PROGRAMFILES\Tuxemon

; Registry key to check for directory (so if you install again, it will 
; overwrite the old one automatically)
InstallDirRegKey HKLM "Software\Tuxemon" "Install_Dir"

;--------------------------------

; Include Modern UI
!include "MUI2.nsh"

; MUI Settings
!define MUI_ABORTWARNING

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "$%TXMNBuildDir%\LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Languages
!insertmacro MUI_LANGUAGE "English"

;--------------------------------
LicenseData "$%TXMNBuildDir%\LICENSE"

!define VERSION "0.4.35.0"
VIProductVersion "${VERSION}"
VIAddVersionKey /LANG=${LANG_ENGLISH} "ProductName" "Tuxemon"
VIAddVersionKey /LANG=${LANG_ENGLISH} "FileVersion" "${VERSION}"
VIAddVersionKey /LANG=${LANG_ENGLISH} "FileDescription" "Tuxemon is a free, open source monster-fighting RPG."
VIAddVersionKey /LANG=${LANG_ENGLISH} "LegalCopyright" "GNU GPL v3"

; The stuff to install
Section "Tuxemon (required)"

  SectionIn RO

  ; Set output path to the installation directory.
  SetOutPath $INSTDIR

  ; Put file there
  File "$%TXMNBuildDir%\run_tuxemon.exe"
  File /r "$%TXMNBuildDir%\*"

  ; Write the installation path into the registry
  WriteRegStr HKLM SOFTWARE\Tuxemon "Install_Dir" "$INSTDIR"

  ; Write the uninstall keys for Windows
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Tuxemon" "DisplayName" "Tuxemon"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Tuxemon" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Tuxemon" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Tuxemon" "NoRepair" 1
  WriteUninstaller "$INSTDIR\uninstall.exe"

SectionEnd

; Optional section (can be disabled by the user)
Section "Start Menu Shortcuts"

  CreateDirectory "$SMPROGRAMS\Tuxemon"
  CreateShortcut "$SMPROGRAMS\Tuxemon\Tuxemon.lnk" "$INSTDIR\Tuxemon.nsi"

SectionEnd

;--------------------------------

; Uninstaller

Section "Uninstall"

  ; Remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Tuxemon"
  DeleteRegKey HKLM SOFTWARE\NSIS_Tuxemon

  ; Remove files and uninstaller
  Delete $INSTDIR\run_tuxemon.exe
  Delete $INSTDIR\uninstall.exe
  Delete $INSTDIR\*

  ; Remove shortcuts, if any
  Delete "$SMPROGRAMS\Tuxemon\*.lnk"

  ; Remove directories
  RMDir "$SMPROGRAMS\Tuxemon"
  RMDir "$INSTDIR"

SectionEnd
