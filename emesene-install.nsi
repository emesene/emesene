SetCompressor /solid lzma
;!include "lnkX64IconFix.nsh"

Name "emesene2"
Icon "emesene.ico"
OutFile "emesene2-install.exe"
InstallDir "$PROGRAMFILES\emesene2"
InstallDirRegKey HKLM "Software\emesene2" "Install_Dir"

Section "Install"  
    SectionIn RO
    SetOutPath $INSTDIR
    File /r "dist\*.*"
    WriteRegStr HKLM "Software\emesene2" "Install_Dir" "$INSTDIR"
    WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

Section "Shortcuts"
    /* Shortcut icons currently dont work on x64 Windows 7 and possible Vista.
       lnkX64IconFix.nsh is a macro file that suppose to fix the problem, but it doesnt seem to.
       All lines related to lnkX64IconFix are commented out. */
    CreateDirectory "$SMPROGRAMS\emesene2"
    CreateShortCut "$SMPROGRAMS\emesene2\emesene2.lnk" "$INSTDIR\emesene.exe" "" "$INSTDIR\emesene.exe"
    ;${lnkX64IconFix} "$SMPROGRAMS\emesene2\emesene2.lnk"
    CreateShortCut "$SMPROGRAMS\emesene2\emesene2 (debug).lnk" "$INSTDIR\emesene_debug.exe" "" "$INSTDIR\emesene_debug.exe"
    ;${lnkX64IconFix} "$SMPROGRAMS\emesene2\emesene2 (debug).lnk"
    CreateShortCut "$SMPROGRAMS\emesene2\uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe"
    ;${lnkX64IconFix} "$SMPROGRAMS\emesene2\uninstall.lnk"
    CreateShortCut "$DESKTOP\emesene2.lnk" "$INSTDIR\emesene.exe" "" "$INSTDIR\emesene.exe"
    ;${lnkX64IconFix} "$DESKTOP\emesene2.lnk"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\uninstall.exe"
    RMDir /r $INSTDIR
    RMDir /r "$PROFILE\emesene2\"
    RMDir /r "$SMPROGRAMS\emesene2"
    Delete "$DESKTOP\emesene2.lnk"
    DeleteRegKey HKLM "Software\emesene2"
SectionEnd