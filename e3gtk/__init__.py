import Login
import dialog
import Header
import Window
import TextBox
import Signals
import UserPanel
import TabWidget
import MainWindow
import ContactList
import ContactInfo
import Conversation
import WebKitTextBox
import ConversationManager

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

    dummy_components.categories['gtk conversation window'] = ConversationManager.ConversationManager
    dummy_components.categories['gtk conversation'] = Conversation.Conversation
    dummy_components.categories['gtk conversation header'] = Header.Header
    dummy_components.categories['gtk conversation info'] = ContactInfo.ContactInfo
    dummy_components.categories['gtk conversation tab'] = TabWidget.TabWidget
    dummy_components.categories['gtk conversation input'] = TextBox.InputText

    if not WebKitTextBox.ERROR:
        dummy_components.categories['gtk conversation output'] = WebKitTextBox.OutputText
    else:
        dummy_components.categories['gtk conversation output'] = TextBox.OutputText

