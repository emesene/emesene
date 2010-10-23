# -*- coding: utf-8 -*-

'''This module contains classes to represent the conversation tab.'''

import PyKDE4.kdeui     as KdeGui
from PyKDE4.kdecore import i18n
import PyQt4.QtGui      as QtGui
import PyQt4.QtCore     as QtCore
from PyQt4.QtCore   import Qt

import gui
import gui.kde4ui.widgets as Widgets

import xml
import sys
reload(sys)


class Conversation (gui.base.Conversation, QtGui.QWidget):
    '''This widget represents the contents of a chat tab in the conversations
    page'''
    def __init__(self, session, conv_id, members=None, parent=None):
        '''Constructor'''
        gui.base.Conversation.__init__(self, session, conv_id, members)
        QtGui.QWidget.__init__(self, parent)
        
        self._session = session
        self._conv_id = conv_id
        self._members = members
        self._chat_text = QtCore.QString("<i>New Chat</i><br>")
        
        # emesene's
        self.tab_index = 0
        self.input = self
        self.output = self
        
        # a widget dic to avoid proliferation of instance variables:
        self._widget_dict = {}
        # an action dict to avoi proliferation of instance variables:
        self._action_dict = {}
        
        self._setup_ui()
        
    def __del__(self):
        print "conversation adieeeeeeeuuuu ;______;"
        
        
    def _setup_ui(self):
        '''Instantiates the widgets, and sets the layout'''
        widget_dict = self._widget_dict
        action_dict = self._action_dict
        
        # Actions
        action_dict['add_smiley']   = KdeGui.KAction(
               KdeGui.KIcon("preferences-desktop-font"),  "Add Smiley", self)
        action_dict['send_nudge']   = KdeGui.KAction(
               KdeGui.KIcon("preferences-desktop-font"),  "Send Nudge", self)
        action_dict['change_font']  = KdeGui.KAction(
               KdeGui.KIcon("preferences-desktop-font"),  "Change Font", self)
        action_dict['change_color'] = KdeGui.KAction(
               KdeGui.KIcon("preferences-desktop-fonts"), "Change Color", self)
                    
                    
        label = QtGui.QLabel(str(self._conv_id))
        # TOP LEFT
        top_left_widget = QtGui.QWidget()
        widget_dict['chat_view'] = KdeGui.KTextBrowser(None, True)
        top_left_lay = QtGui.QHBoxLayout()
        top_left_lay.addWidget(widget_dict['chat_view'])
        top_left_widget.setLayout(top_left_lay)
        
        widget_dict['chat_view'].setText(self._chat_text)
        

        # BOTTOM LEFT
        bottom_left_widget = QtGui.QWidget()
        widget_dict['toolbar'] = KdeGui.KToolBar(self)
        widget_dict['smiley_chooser'] = Widgets.SmileyPopupChooser()
        widget_dict['chat_edit'] = Widgets.ChatTextEdit()
        widget_dict['send_btn'] = KdeGui.KPushButton("Send")
        
        text_edit_lay = QtGui.QHBoxLayout()
        text_edit_lay.addWidget(widget_dict['chat_edit'])
        text_edit_lay.addWidget(widget_dict['send_btn'])
        
        bottom_left_lay = QtGui.QVBoxLayout()
        bottom_left_lay.addWidget(widget_dict['toolbar'])
        bottom_left_lay.addLayout(text_edit_lay)
        bottom_left_widget.setLayout(bottom_left_lay)
        
        toolbar = widget_dict['toolbar']
        toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)
        toolbar.addAction(action_dict['add_smiley'])
        toolbar.addAction(action_dict['send_nudge'])
        toolbar.addSeparator()
        toolbar.addAction(action_dict['change_font'])
        toolbar.addAction(action_dict['change_color'])
        
        widget_dict['chat_edit'].set_smiley_dict(gui.theme.EMOTES)
        
        
        widget_dict['smiley_chooser'].emoticon_selected.connect(
                            self._on_smiley_selected)
        widget_dict['chat_edit'].return_pressed.connect(
                            self._on_send_message)
        widget_dict['send_btn'].clicked.connect(
                            self._on_send_message)
        action_dict['add_smiley'].triggered.connect(
                            self._on_show_smiley_chooser)
        action_dict['change_font'].triggered.connect(
                            widget_dict['chat_edit'].show_font_style_chooser)
        action_dict['change_color'].triggered.connect(
                            widget_dict['chat_edit'].show_font_color_chooser)

        
        # LEFT (TOP & BOTTOM)
        left_widget = QtGui.QSplitter(Qt.Vertical)
        left_widget.addWidget(top_left_widget)
        left_widget.addWidget(bottom_left_widget)

        left_lay = QtGui.QVBoxLayout()
        left_lay.addWidget(label)
        left_lay.addWidget(left_widget)

        left_widget.setCollapsible (0, False)
        left_widget.setCollapsible (1, False)
        _, splitter_pos = left_widget.getRange(1)
        left_widget.moveSplitter(splitter_pos, 1)

        # RIGHT
        widget_dict['his_display_pic'] = Widgets.DisplayPic(
                                    self._session, first_pic=gui.theme.user)
        widget_dict['my_display_pic'] = Widgets.DisplayPic(
                                    self._session, first_pic=gui.theme.user)
        
        right_lay = QtGui.QVBoxLayout()
        right_lay.addWidget(widget_dict['his_display_pic'])
        right_lay.addStretch()
        right_lay.addWidget(widget_dict['my_display_pic'])
        
        widget_dict['my_display_pic'].set_display_pic_of_account()
        if self._members:
            his_email = self._members[0]
            widget_dict['his_display_pic'].set_display_pic_of_account(
                                                                his_email)

        # LEFT & RIGHT
        lay = QtGui.QHBoxLayout()
        lay.addLayout(left_lay)
        lay.addLayout(right_lay)
        
        self.setLayout(lay)

        sys.setdefaultencoding("utf8")
        
        
    # emesene's
    def receive_message(self, formatter, contact, message, cedict, first):
        '''This method is called from the core (e3 or base class or whatever
        when a new message arrives. It shows the new message'''
        print formatter,
        print contact,
        print message.type,
        print message.account
        print cedict,
        print first
        
        self._append_to_chat(
            xml.sax.saxutils.escape(message.body) + '<br>')
            
    # emesene's
    def send_message(self, formatter, my_account,
                text, cedict, cstyle, first):
        self._append_to_chat(
            '<b>ME:</b>' + xml.sax.saxutils.escape(text) + '<br/>')
    
    
    def update_single_information(self, nick, message, account): # emesene's
        '''This method is called from the core (e3 or base class or whatever
        to update the contacts infos'''
        print nick,
        print message,
        print account
        
        
    def show(self):
        '''Shows the widget'''
        QtGui.QWidget.show(self)
    
    
    def _on_show_smiley_chooser(self):
        '''Slot called when the user clicks the smiley button.
        Show the smiley chooser panel'''
        self._widget_dict['smiley_chooser'].show()


    def _on_smiley_selected(self, shortcut):
        '''Slot called when the user selects a smiley in the smiley 
        chooser panel. Inserts the smiley in the chat edit'''
        # handles cursor position
        self._widget_dict['chat_edit'].insert_text_after_cursor(shortcut)
        
    
    def _on_send_message(self):
        message_string = str(self._widget_dict['chat_edit'].toPlainText())
        if len(message_string) == 0:
            return
        self._widget_dict['chat_edit'].clear()
        gui.base.Conversation._on_send_message(self, message_string)
        
        
    def _append_to_chat(self, html_string):
        '''Method that appends an html string to the chat view'''
        vert_scroll_bar = self._widget_dict['chat_view'].verticalScrollBar()
        if vert_scroll_bar.value() == vert_scroll_bar.maximum():
            at_bottom = True
        else:
            at_bottom = False

        self._chat_text.append(html_string)
        self._widget_dict['chat_view'].setText(self._chat_text)

        if at_bottom:
            vert_scroll_bar.setValue(vert_scroll_bar.maximum())


#    def onMessageReceived(self, messageview, formatting):
#        """ Called for incoming and outgoing messages
#            message: a MessageView of the message"""
#            
#        messageReceived = messageview.to_stringview().parse_default_smileys()
#        tempStr = QString("<br>")
#        if formatting is not None:
#            tempStr.append("<font face=\"%s\" color=\"#%s\">" % (
#                                    formatting.font, formatting.color ))
#
#
#        tempStr.append(messageReceived.to_HTML_string())
#
#        if formatting is not None:
#            tempStr.append("</font>")
#        tempStr.append("<br>")
#
#        self.appendToChat(tempStr)
#
#
#    def onUserJoined(self, nickname):
#        self.appendToChat("<i>%s has joined the chat </i>"%(unicode(nickname)))
#        self.statusBar.insertItem("%s has joined the chat" % (nickname), 0)
#
#
#    def onNudge(self):
#        pass
#
#    def onUserTyping(self, contact):
#        if self.statusBar.hasItem(1):
#            self.statusBar.removeItem(1)
#        self.statusBar.insertItem("%s is typing a message" % (contact), 1)
#        self.statusBar.setItemAlignment(1, Qt.AlignLeft)

   

        
        
        
