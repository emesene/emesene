;SetCompressor lzma

!define PROGRAM_NAME "emesene"
!define PROGRAM_VERSION "2.11.5-devel"
!define PROGRAM_TYPE "install"
!define PROGRAM_DIRECTORY "emesene2"

;--------------------------------

; The name of the installer
Name "${PROGRAM_NAME} ${PROGRAM_VERSION}"

; The icon used
Icon "emesene.ico"

; The file to write
OutFile "${PROGRAM_NAME} ${PROGRAM_VERSION} - ${PROGRAM_TYPE}.exe"

; The default installation directory
InstallDir $PROGRAMFILES\${PROGRAM_DIRECTORY}

; Registry key to check for directory (so if you install again, it will 
; overwrite the old one automatically)
InstallDirRegKey HKLM "Software\${PROGRAM_DIRECTORY}" "Install_Dir"

;--------------------------------

; Pages
Page components
Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

;--------------------------------

; Install (Required)
Section "Install"
    SectionIn RO
    
    ; Set output path to the installation directory.
    SetOutPath $INSTDIR
    
    ; Put file there
    File /r "dist\*.*"
    
    ; Write the installation path into the registry
    WriteRegStr HKLM SOFTWARE\${PROGRAM_DIRECTORY} "Install_Dir" "$INSTDIR"
    
    ; Write the uninstall keys for Windows
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PROGRAM_DIRECTORY}" "DisplayName" "${PROGRAM_NAME} ${PROGRAM_VERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PROGRAM_DIRECTORY}" "UninstallString" '"$INSTDIR\uninstall.exe"'
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PROGRAM_DIRECTORY}" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PROGRAM_DIRECTORY}" "NoRepair" 1
    WriteUninstaller "uninstall.exe" 
SectionEnd

; Optional section (can be disabled by the user)
Section "Start Menu Shortcuts"
    CreateDirectory "$SMPROGRAMS\${PROGRAM_DIRECTORY}"
    CreateShortCut "$SMPROGRAMS\${PROGRAM_DIRECTORY}\emesene2.lnk" "$INSTDIR\emesene.exe" "" "$INSTDIR\emesene.exe" 0
    CreateShortCut "$SMPROGRAMS\${PROGRAM_DIRECTORY}\emesene2 (Debug).lnk" "$INSTDIR\emesene_debug.exe" "" "$INSTDIR\emesene_debug.exe" 0
    CreateShortCut "$SMPROGRAMS\${PROGRAM_DIRECTORY}\Report Issue.lnk" "https://github.com/emesene/emesene/issues"
    CreateShortCut "$SMPROGRAMS\${PROGRAM_DIRECTORY}\Uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0
SectionEnd

; Optional section (can be disabled by the user)
Section "Desktop Shortcuts"
    CreateShortCut "$DESKTOP\emesene2.lnk" "$INSTDIR\emesene.exe" "" "$INSTDIR\emesene.exe" 0
SectionEnd

;--------------------------------

; Uninstall
Section "Uninstall"
    ; Remove registry keys
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PROGRAM_DIRECTORY}"
    DeleteRegKey HKLM SOFTWARE\${PROGRAM_DIRECTORY}
    
    ; Remove files and uninstaller
    Delete $INSTDIR\uninstall.exe
    RMDir /r "$INSTDIR"
    
    ; Remove shortcuts
    RMDir /r "$SMPROGRAMS\${PROGRAM_DIRECTORY}"
    Delete "$DESKTOP\emesene2.lnk"
SectionEnd

Function .onInit
; Auto-uninstall old before installing new
    ReadRegStr $R0 HKLM \
    "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PROGRAM_DIRECTORY}" \
    "UninstallString"
    StrCmp $R0 "" done
    
    MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
    "${PROGRAM_NAME} is already installed. $\n$\nClick `OK` to remove the \
    previous version or `Cancel` to cancel this upgrade." \
    IDOK uninst
    Abort
    
; Run the uninstaller
uninst:
    ClearErrors
    ExecWait '$R0 _?=$INSTDIR' ;Do not copy the uninstaller to a temp file
    
    IfErrors no_remove_uninstaller done
        ;You can either use Delete /REBOOTOK in the uninstaller or add some code
        ;here to remove the uninstaller. Use a registry key to check
        ;whether the user has chosen to uninstall. If you are using an uninstaller
        ;components page, make sure all sections are uninstalled.
    no_remove_uninstaller:
    
done:
FunctionEnd