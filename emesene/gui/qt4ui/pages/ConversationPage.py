# -*- coding: utf-8 -*-

'''This module contains classes to represent the conversation page.'''

import PyQt4.QtGui      as QtGui

import gui
import gui.qt4ui.Conversation   as Conversation


class ConversationPage (gui.base.ConversationManager, QtGui.QTabWidget):
    '''The Conversation Page'''
    # pylint: disable=W0612
    NAME = 'MainPage'
    DESCRIPTION = 'The widget used to to display the conversation screen'
    AUTHOR = 'Gabriele Whisky Visconti'
    WEBSITE = ''
    # pylint: enable=W0612
    
    def __init__(self, session, on_last_close, parent):
        '''Constructor'''
        gui.base.ConversationManager.__init__(self, session, on_last_close)
        QtGui.QTabWidget.__init__(self, parent)
        
        self.setTabsClosable(True)
        self.setDocumentMode(True)
        
        # to prevent top level window's destruction:
        self.qt_parent = parent
        
        self.tabCloseRequested.connect(self._on_tab_close_request)
        
        
    def __del__(self):
        print "conversation manager adieeeeeeeuuuu ;______;"
        
    def get_parent(self): # emesene's
        '''Return a reference to the top level window containing this page'''
        return QtGui.QTabWidget.parent(self).parent()
                
    def set_current_page(self, tab_index): # emesene's
        '''Show the chat tab at the given index'''
        QtGui.QTabWidget.setCurrentIndex(self, tab_index)
        
    
        
        
    #[START] -------------------- GUI.BASE.CONVERSATIONMANAGER_OVERRIDE
    
    def add_new_conversation(self, session, conv_id, members):
        '''Creates a new chat tab and returns it. This implements base's
        class abstract method.'''
        conversation = Conversation.Conversation(session, conv_id, 
                                                 members)
        account = session.contacts.get(members[0])
        conversation.tab_index = self.addTab(conversation, 
                                             unicode(account.display_name))
        self.setTabIcon(conversation.tab_index, 
                        QtGui.QIcon(gui.theme.status_icons[account.status]))
        return conversation
        
    def remove_conversation(self, conversation):
        '''Removes the chat tab. This implements base's class 
        abstract method.'''
        index = self.indexOf(conversation)
        self.removeTab(index)
    
    def set_message_waiting(self, conversation, is_waiting): # emesene's
        '''Not Sure what to do here....'''
        print conversation,
        print is_waiting
        
        
    def _on_contact_attr_changed(self, account, change_type, old_value,
            do_notify=True):
        '''called when an attribute of a contact changes.
        Overridden to update tabs'''
        gui.base.ConversationManager._on_contact_attr_changed(self, account, 
                                                              change_type, 
                                                              old_value, 
                                                              do_notify)
        for conversation in self.conversations.values():
            if account in conversation.members:
                index = self.indexOf(conversation)
                account = self.session.contacts.get(conversation.members[0])
                icon = QtGui.QIcon(gui.theme.status_icons[account.status])
                self.setTabIcon(index, icon)
                self.setTabText(index, unicode(account.display_name))
                
                
    #[START] -------------------- GUI.BASE.CONVERSATIONMANAGER_OVERRIDE
                

    def _on_tab_close_request(self, index):
        '''Slot executed when the use clicks the close button in a tab'''
        self.on_conversation_close(self.widget(index))


        







