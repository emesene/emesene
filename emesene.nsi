SetCompressor /solid lzma
Name "emesene2"
Icon "emesene.ico"
OutFile "emesene2-install.exe"
InstallDir "$PROGRAMFILES\emesene2"
InstallDirRegKey HKLM "Software\emesene2" "Install_Dir"

Section "emesene2"
    SectionIn RO
    SetOutPath "$INSTDIR"
    File /r dist\*.*
    WriteRegStr HKLM SOFTWARE\emesene2 "Install_Dir" "$INSTDIR"
SectionEnd

Section "Start Menu Shortcuts"
    CreateDirectory "$SMPROGRAMS\emesene2"
    CreateShortCut "$SMPROGRAMS\emesene2\emesene2.lnk" "$INSTDIR\emesene.exe" "" "$INSTDIR\emesene.exe" 0
    CreateShortCut "$SMPROGRAMS\emesene2\emesene2debug.lnk" "$INSTDIR\emesene_debug.exe" "" "$INSTDIR\emesene_debug.exe" 0
SectionEnd
