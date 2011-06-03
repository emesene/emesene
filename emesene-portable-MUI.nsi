;--------------------------------
# Compressor Type
    SetCompressor /SOLID lzma

;--------------------------------
# Includes

    ; Modern UI
    !include "MUI2.nsh"

;--------------------------------
# Defines

    ;Program info
    !define PROGRAM_NAME "emesene" ; emesene
    !define PROGRAM_VERSION "2.11.6-devel"
    !define PROGRAM_TYPE "portable"
    !define PROGRAM_PUBLISHER "emesene team"
    !define PROGRAM_WEBSITE "http://www.emesene.org"
    !define PROGRAM_ISSUE "https://github.com/emesene/emesene/issues/"

    ;--------------------------------
# General

    ; Name and output file
    Name "${PROGRAM_NAME} ${PROGRAM_VERSION}"
    OutFile "${PROGRAM_NAME}-${PROGRAM_VERSION}-${PROGRAM_TYPE}.exe"

    ; No user interaction required
    SilentInstall silent

    ; Request application privileges for Windows Vista/7
    RequestExecutionLevel admin

;--------------------------------
# MUI Settings

    !define MUI_ABORTWARNING
    !define MUI_HEADERIMAGE
    !define MUI_HEADERIMAGE_BITMAP "windows\header.bmp"
    !define MUI_ICON "windows\emesene.ico"
    !define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

;--------------------------------
# Languages

    !insertmacro MUI_LANGUAGE "English"
    !insertmacro MUI_LANGUAGE "French"
    !insertmacro MUI_LANGUAGE "Italian"
    !insertmacro MUI_LANGUAGE "Spanish"

;--------------------------------
# Installer Sections

    ; Main installation (Required)
    Section "${PROGRAM_NAME} ${PROGRAM_VERSION}" secInstall
        SetOutPath "$EXEDIR\Portable"
        SetOverwrite on
        File /r "dist\*.*"

        SetOutPath "$EXEDIR\Portable"
        ExecWait "$EXEDIR\Portable\emesene.exe"
        ;nsExec::Exec "$EXEDIR\Portable\emesene.exe"
    SectionEnd

    /*
    ; Plug-ins (Optional)
    Section "Plug-ins" SecPlugins
        ;Plug-ins here :)
    SectionEnd
    */