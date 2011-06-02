; This creats a portable version

SetCompressor lzma

!define PROGRAM_NAME "emesene"
!define PROGRAM_VERSION "2.11.6-devel"
!define PROGRAM_TYPE "portable"
!define PROGRAM_DIRECTORY "emesene2"
!define PROGRAM_SHORTCUT "emesene2"

; The name of the installer
Name "${PROGRAM_NAME} ${PROGRAM_VERSION}"

; The icon used
Icon "emesene.ico"

; The file to write
OutFile "${PROGRAM_NAME}-${PROGRAM_VERSION}-${PROGRAM_TYPE}.exe"

; No user interaction required
SilentInstall silent

Section
    ; Set output path to the installation directory.
    SetOutPath $EXEDIR\Portable
    
    ; Put file there
    File /r "dist\*.*"
    
    ; Set output path to the installation directory.
    SetOutPath $EXEDIR\Portable
    
    ; Launch program
    nsExec::Exec "$EXEDIR\Portable\emesene.exe"
SectionEnd
