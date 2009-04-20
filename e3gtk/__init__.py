import Login
import Dialog
import Header
import Window
import TextBox
import MainMenu
import TrayIcon
import UserPanel
import TabWidget
import GroupMenu
import StatusMenu
import MainWindow
import AccountMenu
import ContactMenu
import ContactList
import ContactInfo
import Preferences 
import Conversation
import WebKitTextBox
import ConversationManager
import ConversationToolbar

import extension

def setup():
    """
    define all the components for a gtk environment
    """
    extension.category_register('gtk dialog', Dialog.Dialog)
    extension.category_register('gtk preferences', Preferences.Preferences)
    extension.category_register('gtk login window', Login.Login)
    extension.category_register('gtk window frame', Window.Window)
    extension.category_register('gtk main window', MainWindow.MainWindow)
    extension.category_register('gtk contact list', ContactList.ContactList)
    extension.category_register('gtk user panel', UserPanel.UserPanel)
    extension.category_register('gtk tray icon', TrayIcon.TrayIcon)

    extension.category_register('gtk main menu', MainMenu.MainMenu)
    extension.category_register('gtk menu file', MainMenu.FileMenu)
    extension.category_register('gtk menu actions', MainMenu.ActionsMenu)
    extension.category_register('gtk menu options', MainMenu.OptionsMenu)
    extension.category_register('gtk menu contact', ContactMenu.ContactMenu)
    extension.category_register('gtk menu group', GroupMenu.GroupMenu)
    extension.category_register('gtk menu account', AccountMenu.AccountMenu)
    extension.category_register('gtk menu help', MainMenu.HelpMenu)
    extension.category_register('gtk menu status', StatusMenu.StatusMenu)

    extension.category_register('gtk conversation window', \
        ConversationManager.ConversationManager)
    extension.category_register('gtk conversation', Conversation.Conversation)
    extension.category_register('gtk conversation header', Header.Header)
    extension.category_register('gtk conversation info', ContactInfo.ContactInfo)
    extension.category_register('gtk conversation tab', TabWidget.TabWidget)
    extension.category_register('gtk conversation input', TextBox.InputText)
    extension.category_register('gtk conversation toolbar', \
        ConversationToolbar.ConversationToolbar)

    if not WebKitTextBox.ERROR:
        extension.category_register('gtk conversation output', WebKitTextBox.OutputText)
    else:
        extension.category_register('gtk conversation output', TextBox.OutputText)

