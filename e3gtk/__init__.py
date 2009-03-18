import Login
import dialog
import Header
import Window
import TextBox
import Signals
import MainMenu
import UserPanel
import TabWidget
import GroupMenu
import StatusMenu
import MainWindow
import ContactMenu
import AccountMenu
import ContactList
import ContactInfo
import Conversation
import WebKitTextBox
import ConversationManager
import ConversationToolbar

import dummy_components

from protocol.Worker import EVENTS

Signals.Signals.set_events(EVENTS)

def setup():
    """
    define all the components for a gtk environment
    """
    dummy_components.categories['gtk dialog'] = dialog
    dummy_components.categories['gtk login window'] = Login.Login
    dummy_components.categories['gtk window frame'] = Window.Window
    dummy_components.categories['gtk main window'] = MainWindow.MainWindow
    dummy_components.categories['gtk contact list'] = ContactList.ContactList
    dummy_components.categories['gtk user panel'] = UserPanel.UserPanel

    dummy_components.categories['gtk main menu'] = MainMenu.MainMenu
    dummy_components.categories['gtk menu file'] = MainMenu.FileMenu
    dummy_components.categories['gtk menu actions'] = MainMenu.ActionsMenu
    dummy_components.categories['gtk menu options'] = MainMenu.OptionsMenu
    dummy_components.categories['gtk menu contact'] = ContactMenu.ContactMenu
    dummy_components.categories['gtk menu group'] = GroupMenu.GroupMenu
    dummy_components.categories['gtk menu account'] = AccountMenu.AccountMenu
    dummy_components.categories['gtk menu help'] = MainMenu.HelpMenu
    dummy_components.categories['gtk menu status'] = StatusMenu.StatusMenu

    dummy_components.categories['gtk conversation window'] = \
        ConversationManager.ConversationManager
    dummy_components.categories['gtk conversation'] = Conversation.Conversation
    dummy_components.categories['gtk conversation header'] = Header.Header
    dummy_components.categories['gtk conversation info'] = ContactInfo.ContactInfo
    dummy_components.categories['gtk conversation tab'] = TabWidget.TabWidget
    dummy_components.categories['gtk conversation input'] = TextBox.InputText
    dummy_components.categories['gtk conversation toolbar'] = \
        ConversationToolbar.ConversationToolbar 

    if not WebKitTextBox.ERROR:
        dummy_components.categories['gtk conversation output'] = WebKitTextBox.OutputText
    else:
        dummy_components.categories['gtk conversation output'] = TextBox.OutputText

