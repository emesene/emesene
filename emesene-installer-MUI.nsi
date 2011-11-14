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
;Variables

    ; Holds user-selected StartMenu Directory
    Var StartMenuDir

#--------------------------------
# Defines

    ; Program info
    !define PROGRAM_NAME "emesene"
    !define PROGRAM_VERSION "2.11.12-devel"
    !define /date PROGRAM_BUILDTIME "%Y%m%d_%H%M"
    !define PROGRAM_TYPE "installer"
    !define PROGRAM_PUBLISHER "emesene team"
    !define PROGRAM_WEBSITE "http://www.emesene.org"
    !define PROGRAM_ISSUE "https://github.com/emesene/emesene/issues/"

    ; File info
    !define FILE_CONFIG "$APPDATA\${PROGRAM_NAME}\${FILE_DIRECTORY}"
    !define FILE_DIRECTORY "emesene2"
    !define FILE_EXE "emesene.exe" ; Include ".exe"
    !define FILE_DEBUG "emesene_debug.exe" ; Include ".exe"
    !define FILE_UNINSTALL "uninstall.exe" ; Include ".exe"

    ; Shortcut info
    !define SHORTCUT_STARTMENU "$SMPROGRAMS\$StartMenuDir"
    !define SHORTCUT_EXE "emesene2.lnk" ; Include ".lnk"
    !define SHORTCUT_DEBUG "emesene2 (Debug).lnk" ; Include ".lnk"
    !define SHORTCUT_REPORT "Report Issue.lnk" ; Include ".lnk"
    !define SHORTCUT_UNINSTALL "Uninstall.lnk" ; Include ".lnk"

    ; Registry info
    !define REG_HIVE "HKLM" ; Sets registry time to local computer, all users
    !define REG_INSTALL "Software\${FILE_DIRECTORY}"
    !define REG_UNINSTALL "Software\Microsoft\Windows\CurrentVersion\Uninstall\${FILE_DIRECTORY}"

    ; User info
    !define USER_PRIVILEGES "admin" ; "admin" required to write to 'Program Files'
    !define USER_SHELLCONTEXT "all" ; "all" will write to all, not just current

    ; Window info
    !define WINDOW_CLASS "gdkWindowToplevel"
    !define WINDOW_TITLE "emesene"

#--------------------------------
# General

    ; Name and output file
    Name "${PROGRAM_NAME} ${PROGRAM_VERSION}"
    OutFile "${PROGRAM_NAME}-${PROGRAM_VERSION}-${PROGRAM_BUILDTIME}-${PROGRAM_TYPE}.exe"

    ; The default installation directory
    InstallDir "$PROGRAMFILES\${FILE_DIRECTORY}"

    ; Get installation folder from registry if available
    InstallDirRegKey ${REG_HIVE} "${REG_INSTALL}" "Install_Dir"

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

    ; Remember the installer language
    !define MUI_LANGDLL_REGISTRY_ROOT "${REG_HIVE}" 
    !define MUI_LANGDLL_REGISTRY_KEY "${REG_INSTALL}" 
    !define MUI_LANGDLL_REGISTRY_VALUENAME "Install_Lang"

    ; StartMenu page configuration
    !define MUI_STARTMENUPAGE_DEFAULTFOLDER "${FILE_DIRECTORY}"
    !define MUI_STARTMENUPAGE_REGISTRY_ROOT "${REG_HIVE}"
    !define MUI_STARTMENUPAGE_REGISTRY_KEY "${REG_INSTALL}"
    !define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "StartMenu_Dir"

    ; Finish page configuration
    !define MUI_FINISHPAGE_RUN "$INSTDIR\${FILE_EXE}"

#--------------------------------
# Pages

    ; Installer pages
    !insertmacro MUI_PAGE_WELCOME
    !insertmacro MUI_PAGE_LICENSE "GPL"
    !insertmacro MUI_PAGE_COMPONENTS
    !insertmacro MUI_PAGE_DIRECTORY
    !insertmacro MUI_PAGE_STARTMENU "Application" $StartMenuDir
    !insertmacro MUI_PAGE_INSTFILES
    !insertmacro MUI_PAGE_FINISH

    ; Uninstaller pages
    !insertmacro MUI_UNPAGE_WELCOME
    !insertmacro MUI_UNPAGE_CONFIRM
    !insertmacro MUI_UNPAGE_COMPONENTS
    !insertmacro MUI_UNPAGE_INSTFILES
    !insertmacro MUI_UNPAGE_FINISH

#--------------------------------
# Languages

    ; List of installer languages
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
        ; Detects if the program is running and asks user to close it
        FindWindow $0 "${WINDOW_CLASS}" "${WINDOW_TITLE}"
        StrCmp $0 0 notRunning
            MessageBox MB_OK|MB_ICONEXCLAMATION "${PROGRAM_NAME} is currently running. Please close it and try again." /SD IDOK
            Abort
        notRunning:

        ; Select language on installer start
        !insertmacro MUI_LANGDLL_DISPLAY
    FunctionEnd

    ; Register uninstaller into Add/Remove panel (for local user only)
    Function "RegisterApplication"
        WriteRegStr ${REG_HIVE} "${REG_UNINSTALL}" "DisplayName" "${PROGRAM_NAME}"
        WriteRegStr ${REG_HIVE} "${REG_UNINSTALL}" "DisplayIcon" "$\"$INSTDIR\${FILE_EXE}$\""
        WriteRegStr ${REG_HIVE} "${REG_UNINSTALL}" "Publisher" "${PROGRAM_PUBLISHER}"
        WriteRegStr ${REG_HIVE} "${REG_UNINSTALL}" "DisplayVersion" "${PROGRAM_VERSION}"
        WriteRegStr ${REG_HIVE} "${REG_UNINSTALL}" "HelpLink" "${PROGRAM_ISSUE}"
        WriteRegStr ${REG_HIVE} "${REG_UNINSTALL}" "URLInfoAbout" "${PROGRAM_WEBSITE}"
        WriteRegStr ${REG_HIVE} "${REG_UNINSTALL}" "InstallLocation" "$\"$INSTDIR$\""
        WriteRegDWORD ${REG_HIVE} "${REG_UNINSTALL}" "NoModify" 1
        WriteRegDWORD ${REG_HIVE} "${REG_UNINSTALL}" "NoRepair" 1
        WriteRegStr ${REG_HIVE} "${REG_UNINSTALL}" "UninstallString" "$\"$INSTDIR\${FILE_UNINSTALL}$\""
    FunctionEnd

    ; Runs before before everything else during uninstallation
    Function "un.onInit"
        ; Detects if the program is running and asks user to close it
        FindWindow $0 "${WINDOW_CLASS}" "${WINDOW_TITLE}"
        StrCmp $0 0 notRunning
            MessageBox MB_OK|MB_ICONEXCLAMATION "${PROGRAM_NAME} is currently running. Please close it and try again." /SD IDOK
            Abort
        notRunning:
    FunctionEnd

    ; Deregister uninstaller from Add/Remove panel
    Function "un.DeregisterApplication"
        DeleteRegKey ${REG_HIVE} "${REG_UNINSTALL}"
    FunctionEnd

#--------------------------------
# Installer Sections

    ; Main installation (Required)
    Section "${PROGRAM_NAME} ${PROGRAM_VERSION}" secInstall
        SectionIn RO

        SetOutPath "$INSTDIR"
        SetOverwrite on
        File /r /x *.py /x *portable* dist\*.*

        ; Store installation folder
        WriteRegStr ${REG_HIVE} "${REG_INSTALL}" "Install_Dir" "$INSTDIR"

        ; StartMenu Shortcuts
        !insertmacro MUI_STARTMENU_WRITE_BEGIN "Application"
            ; Sets the context of shell folders
            SetShellVarContext ${USER_SHELLCONTEXT}

            ; Creates shortcut in the StartMenu
            CreateDirectory "${SHORTCUT_STARTMENU}"
            CreateShortCut "${SHORTCUT_STARTMENU}\${SHORTCUT_EXE}" "$INSTDIR\${FILE_EXE}"
            CreateShortCut "${SHORTCUT_STARTMENU}\${SHORTCUT_DEBUG}" "$INSTDIR\${FILE_DEBUG}"
            CreateShortCut "${SHORTCUT_STARTMENU}\${SHORTCUT_REPORT}" "${PROGRAM_ISSUE}"
            CreateShortCut "${SHORTCUT_STARTMENU}\${SHORTCUT_UNINSTALL}" "$INSTDIR\${FILE_UNINSTALL}"
        !insertmacro MUI_STARTMENU_WRITE_END

        ; Create uninstaller
        Call RegisterApplication
        WriteUninstaller "$INSTDIR\${FILE_UNINSTALL}"
    SectionEnd

    /*
    ; Plug-ins (Optional)
    Section "Plug-ins" secPlugins
        ;Plug-ins here :)
    SectionEnd
    */

    ; Desktop Shortcuts (Optional)
    Section "Desktop Shortcuts"  secDesktop
        ; Sets the context of shell folders
        SetShellVarContext ${USER_SHELLCONTEXT}

        ; Creates shortcut on desktop
        CreateShortCut "$DESKTOP\${SHORTCUT_EXE}" "$INSTDIR\${FILE_EXE}"
    SectionEnd

#--------------------------------
# Uninstaller Sections

    ; Main uninstallation
    Section "un.${PROGRAM_NAME} ${PROGRAM_VERSION}" secUninstall
        ; Sets the context of shell folders
        SetShellVarContext ${USER_SHELLCONTEXT}

        ; Removes install directory (no data is stored there anyway)
        Delete "$INSTDIR\${FILE_UNINSTALL}"
        RMDir /r "$INSTDIR"

        ; Removes Desktop shortcuts
        Delete "$DESKTOP\${SHORTCUT_EXE}"

        ; Removes StartMenu shortcuts
        !insertmacro MUI_STARTMENU_GETFOLDER "Application" $StartMenuDir
        Delete "${SHORTCUT_STARTMENU}\*.*"
        RMDir /r "${SHORTCUT_STARTMENU}"

        ; Remove uninstaller
        Call un.DeregisterApplication

        ; Removes install registry files
        DeleteRegKey /ifempty ${REG_HIVE} "${REG_INSTALL}"
    SectionEnd

    ; Configuration directory (Optional)
    Section "un.Profile/Settings" secConfig
        ; Sets the context of shell folders
        SetShellVarContext current

        ; Removes config folder
        RMDir /r "${FILE_CONFIG}"
    SectionEnd

    ; Cleans up old registry files
    Section "un.Old Registry Files" secRegistry
        ${If} ${REG_HIVE} == "HKLM"
            DeleteRegKey HKCU "${REG_UNINSTALL}"
            DeleteRegKey /ifempty HKCU "${REG_INSTALL}"
        ${ElseIf} ${REG_HIVE} == "HKCU"
            DeleteRegKey HKLM "${REG_UNINSTALL}"
            DeleteRegKey /ifempty HKLM "${REG_INSTALL}"
        ${EndIf}
    SectionEnd

#--------------------------------
# Descriptions

    ; English Language strings
    LangString DESC_secInstall ${LANG_ENGLISH} "Install"
    ;LangString DESC_secPlugins ${LANG_ENGLISH} "Plug-ins"
    LangString DESC_secDesktop ${LANG_ENGLISH} "Desktop Shortcuts"
    LangString DESC_secUninstall ${LANG_ENGLISH} "Uninstall"
    LangString DESC_secConfig ${LANG_ENGLISH} "Configurations"
    LangString DESC_secRegistry ${LANG_ENGLISH} "Old Registry Files"

    ; French Language strings
    LangString DESC_secInstall ${LANG_FRENCH} "Installer"
    ;LangString DESC_secPlugins ${LANG_FRENCH} "Plug-ins (French)"
    LangString DESC_secDesktop ${LANG_FRENCH} "Raccourcis Bureau"
    LangString DESC_secUninstall ${LANG_FRENCH} "Desinstaller"
    LangString DESC_secConfig ${LANG_FRENCH} "Configurations"
    LangString DESC_secRegistry ${LANG_FRENCH} "Anciens fichiers du Registre"

    ; Italian Language strings
    LangString DESC_secInstall ${LANG_ITALIAN} "Installa"
    ;LangString DESC_secPlugins ${LANG_ITALIAN} "Plug-ins (Italian)"
    LangString DESC_secDesktop ${LANG_ITALIAN} "Collegamenti sul desktop"
    LangString DESC_secUninstall ${LANG_ITALIAN} "Disinstalla"
    LangString DESC_secConfig ${LANG_ITALIAN} "Configurazioni"
    LangString DESC_secRegistry ${LANG_ITALIAN} "Vecchi file di registro"

    ; Spanish Language strings
    LangString DESC_secInstall ${LANG_SPANISH} "Instalar"
    ;LangString DESC_secPlugins ${LANG_SPANISH} "Plug-ins (Spanish)"
    LangString DESC_secDesktop ${LANG_SPANISH} "Accesos directos de escritorio"
    LangString DESC_secUninstall ${LANG_SPANISH} "Desinstalar"
    LangString DESC_secConfig ${LANG_SPANISH} "Configuraciones"
    LangString DESC_secRegistry ${LANG_SPANISH} "Antiguo archivos de registro"

    ; Assign language strings to install sections
    !insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
        !insertmacro MUI_DESCRIPTION_TEXT ${secInstall} $(DESC_secInstall)
        ;!insertmacro MUI_DESCRIPTION_TEXT ${secPlugins} $(DESC_secPlugins)
        !insertmacro MUI_DESCRIPTION_TEXT ${secDesktop} $(DESC_secDesktop)
    !insertmacro MUI_FUNCTION_DESCRIPTION_END

    ; Assign language strings to uninstall sections
    !insertmacro MUI_UNFUNCTION_DESCRIPTION_BEGIN
        !insertmacro MUI_DESCRIPTION_TEXT ${secUninstall} $(DESC_secUninstall)
        !insertmacro MUI_DESCRIPTION_TEXT ${secConfig} $(DESC_secConfig)
        !insertmacro MUI_DESCRIPTION_TEXT ${secRegistry} $(DESC_secRegistry)
    !insertmacro MUI_UNFUNCTION_DESCRIPTION_END
