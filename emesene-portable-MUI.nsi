#--------------------------------
# Compressor Type
    SetCompressor /SOLID lzma

#--------------------------------
# Includes

    ; Modern UI
    !include "MUI2.nsh"

    ; Logic Lib (select and if statements)
    !include "LogicLib.nsh"

#--------------------------------
# Defines

    ; Program info
    !define PROGRAM_NAME "emesene"
    !define PROGRAM_VERSION "2.11.6-devel"
    !define /date PROGRAM_BUILDTIME "%Y%m%d_%H%M"
    !define PROGRAM_TYPE "portable"
    !define PROGRAM_PUBLISHER "emesene team"
    !define PROGRAM_WEBSITE "http://www.emesene.org"
    !define PROGRAM_ISSUE "https://github.com/emesene/emesene/issues/"

    ; User info
    !define USER_PRIVILEGES "admin" ; "admin" required to write to 'Program Files'
    !define USER_SHELLCONTEXT "all" ; "all" will write to all, not just current

    #--------------------------------
# General

    ; Name and output file
    Name "${PROGRAM_NAME} ${PROGRAM_VERSION}"
    OutFile "${PROGRAM_NAME}-${PROGRAM_VERSION}-${PROGRAM_BUILDTIME}-${PROGRAM_TYPE}.exe"

    ; Request application privileges for Windows Vista/7
    RequestExecutionLevel ${USER_PRIVILEGES}

#--------------------------------
# MUI Settings

    ; Abort warning, header image, and icons
    !define MUI_ABORTWARNING
    !define MUI_HEADERIMAGE
    !define MUI_HEADERIMAGE_BITMAP "windows\header.bmp"
    !define MUI_ICON "emesene.ico"
    !define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

    ; Finish page configuration
    !define MUI_FINISHPAGE_RUN "$EXEDIR\${PROGRAM_NAME}-${PROGRAM_VERSION}-${PROGRAM_BUILDTIME}-${PROGRAM_TYPE}\emesene.exe"

#--------------------------------
# Pages

    ; Installer pages
    !insertmacro MUI_PAGE_INSTFILES
    !insertmacro MUI_PAGE_FINISH

#--------------------------------
# Languages

    !insertmacro MUI_LANGUAGE "English"
    !insertmacro MUI_LANGUAGE "French"
    !insertmacro MUI_LANGUAGE "Italian"
    !insertmacro MUI_LANGUAGE "Spanish"

#--------------------------------
# Reserve Files

    ; Reserves language files
    !insertmacro MUI_RESERVEFILE_LANGDLL

#--------------------------------
# Functions

    ; Runs before before everything else during installation
    Function ".onInit"
        ; Select language on installer start
        !insertmacro MUI_LANGDLL_DISPLAY
    FunctionEnd

#--------------------------------
# Installer Sections

    ; Main installation (Required)
    Section "${PROGRAM_NAME} ${PROGRAM_VERSION}" secInstall
        SetOutPath "$EXEDIR\${PROGRAM_NAME}-${PROGRAM_VERSION}-${PROGRAM_BUILDTIME}-${PROGRAM_TYPE}"
        SetOverwrite on
        File /r "dist\*.*"

        SetOutPath "$EXEDIR\${PROGRAM_NAME}-${PROGRAM_VERSION}-${PROGRAM_BUILDTIME}-${PROGRAM_TYPE}"
    SectionEnd

    ; Shortcut
    Section "Shortcut"  secShortcut
        ; Creates shortcut
        CreateShortCut "$EXEDIR\${PROGRAM_NAME}-${PROGRAM_VERSION}-${PROGRAM_BUILDTIME}-${PROGRAM_TYPE}.lnk" "$EXEDIR\${PROGRAM_NAME}-${PROGRAM_VERSION}-${PROGRAM_BUILDTIME}-${PROGRAM_TYPE}\emesene.exe"
    SectionEnd

    /*
    ; Plug-ins (Optional)
    Section "Plug-ins" SecPlugins
        ;Plug-ins here :)
    SectionEnd
    */