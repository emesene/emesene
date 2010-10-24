# -*- coding: utf-8 -*-

'''This module contains classes to represent the conversation page.'''

import PyQt4.QtGui      as QtGui

import gui
import gui.qt4ui.Conversation   as Conversation


import sys
reload(sys)

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
        
        # to prevent top level window's destruction:
        self.qt_parent = parent
        
    def __del__(self):
        print "conversation manager adieeeeeeeuuuu ;______;"
        
        
    def add_new_conversation(self, session, conv_id, members):
        '''Creates a new chat tab and returns it'''
        conversation = Conversation.Conversation(session, conv_id, 
                                                 members, self)
        conversation.tab_index = self.addTab(conversation, str(conv_id))
        return conversation
        
    def get_parent(self): # emesene's
        '''Return a reference to the top level window containing this page'''
        return QtGui.QTabWidget.parent(self).parent()
                
    def set_current_page(self, tab_index): # emesene's
        '''Show the chat tab at the given index'''
        QtGui.QTabWidget.setCurrentIndex(self, tab_index)
        
    def set_message_waiting(self, conversation, is_waiting): # emesene's
        '''Not Sure what to do here....'''
        print conversation,
        print is_waiting
                

#    def addChatWidget(self, chatWidget):
#        self.lay.addWidget(chatWidget)
#        chatWidget.setStatusBar(self.sBar)
#
#    def setMenu(self, menuBar):
#        self.setMenuBar(menuBar)
#
#    def setTitle(self, title):
#        self.setPlainCaption(title)









