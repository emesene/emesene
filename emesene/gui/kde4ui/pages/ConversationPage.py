# -*- coding: utf-8 -*-

'''This module contains classes to represent the conversation page.'''

import PyKDE4.kdeui     as KdeGui
from PyKDE4.kdecore import i18n
import PyQt4.QtGui      as QtGui
import PyQt4.QtCore     as QtCore
from PyQt4.QtCore   import Qt

import gui
import gui.kde4ui.Conversation   as Conversation
import gui.kde4ui.widgets as Widgets


import sys
reload(sys)

class ConversationPage (gui.base.ConversationManager, KdeGui.KTabWidget):
    '''The Conversation Page'''
    # pylint: disable=W0612
    NAME = 'MainPage'
    DESCRIPTION = 'The widget used to to display the conversation screen'
    AUTHOR = 'Gabriele Whisky Visconti'
    WEBSITE = ''
    # pylint: enable=W0612
    
    def __init__(self, session, parent):
        # TODO: understand what have to be passed as "on_last_close"
        gui.base.ConversationManager.__init__(self, session, on_last_close=None)
        KdeGui.KTabWidget.__init__(self, parent)
        
        # to prevent top level window's destruction:
        self.qt_parent = parent
        
    def __del__(self):
        print "conversation manager adieeeeeeeuuuu ;______;"
        
        
    def add_new_conversation(self, session, cid, members):
        conversation = Conversation.Conversation(session, cid, members, self)
        self._saveeee_meee = conversation
        conversation.tab_index = self.addTab(conversation, str(cid))
        return conversation
        
    def get_parent(self): # emesene's
        return KdeGui.KTabWidget.parent(self).parent()
                
    def set_current_page(self, tab_index): # emesene's
        KdeGui.KTabWidget.setCurrentIndex(self, tab_index)
        
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









