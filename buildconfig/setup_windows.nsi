
; The name of the installer
Name "Tuxemon"

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

;Include Modern UI

;  !include "MUI2.nsh"

; Pages


;  !insertmacro MUI_PAGE_WELCOME
;  !insertmacro MUI_PAGE_LICENSE "$%TXMNBuildDir%\LICENSE"
;  !insertmacro MUI_PAGE_COMPONENTS
;  !insertmacro MUI_PAGE_DIRECTORY
;  !insertmacro MUI_PAGE_INSTFILES
;  !insertmacro MUI_PAGE_FINISH

; non modernUI
Page license
Page components
Page directory
Page instfiles

UninstPage uninstConfirm
UninstPage instfiles

;--------------------------------
LicenseData "$%TXMNBuildDir%\LICENSE"
;--------------------------------

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
  ; To remove: CreateShortcut "$SMPROGRAMS\Tuxemon\Uninstall.lnk" "$INSTDIR\uninstall.exe"
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
