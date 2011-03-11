SetCompressor lzma
Name "emesene2-portable.exe"
Icon "emesene.ico"
OutFile "emesene2-portable.exe"
SilentInstall silent

Section
    SetOutPath "$EXEDIR\Portable"
    File /r dist\*.*
    SetOutPath "$EXEDIR\Portable"
    nsExec::Exec "$EXEDIR\Portable\emesene.exe"
SectionEnd
