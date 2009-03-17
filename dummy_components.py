# a dummy implementation of extensions until we decide some details
# on the extension framework

import Login
import Header
import TextBox
import UserPanel
import TabWidget
import MainWindow
import ContactList
import ContactInfo
import Conversation
import WebKitTextBox
import ConversationManager

categories = {}

categories['gtk login window'] = Login.Login
categories['gtk main window'] = MainWindow.MainWindow
categories['gtk contact list'] = ContactList.ContactList
categories['gtk user panel'] = UserPanel.UserPanel

categories['gtk conversation window'] = ConversationManager.ConversationManager
categories['gtk conversation'] = Conversation.Conversation
categories['gtk conversation header'] = Header.Header
categories['gtk conversation info'] = ContactInfo.ContactInfo
categories['gtk conversation tab'] = TabWidget.TabWidget
categories['gtk conversation input'] = TextBox.InputText

if not WebKitTextBox.ERROR:
    categories['gtk conversation output'] = WebKitTextBox.OutputText
else:
    categories['gtk conversation output'] = TextBox.OutputText

def get_default(category_name):
    """
    return the default extension for the category name
    category_name -- the name of the category
    """
    return categories[category_name]

