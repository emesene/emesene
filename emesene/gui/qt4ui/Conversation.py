# -*- coding: utf-8 -*-

'''This module contains classes to represent the conversation tab.'''

import xml

import PyQt4.QtGui      as QtGui
import PyQt4.QtCore     as QtCore
from PyQt4.QtCore   import Qt

import e3
import extension
import gui
import gui.qt4ui.widgets as Widgets




class Conversation (gui.base.Conversation, QtGui.QWidget):
    '''This widget represents the contents of a chat tab in the conversations
    page'''
    # pylint: disable=W0612
    NAME = 'MainPage'
    DESCRIPTION = 'The widget used to to display a single conversation'
    AUTHOR = 'Gabriele Whisky Visconti'
    WEBSITE = ''
    # pylint: enable=W0612
    
    def __init__(self, session, conv_id, members=None, parent=None):
        '''Constructor'''
        gui.base.Conversation.__init__(self, session, conv_id, members)
        QtGui.QWidget.__init__(self, parent)
        
        self._session = session
        self._conv_id = conv_id
        self._members = members
        
        # a widget dic to avoid proliferation of instance variables:
        self._widget_dict = {}
        # an action dict to avoid proliferation of instance variables:
        self._action_dict = {}
        
        self._setup_ui()
        
        # emesene's
        self.tab_index = 0
        self.input = self._widget_dict['chat_input']
        self.output = self._widget_dict['chat_output']
        
        #FIXME: move this to base class
        self._load_style()
        self._widget_dict['chat_input'].e3_style = self.cstyle
        
        
    def __del__(self):
        print "conversation adieeeeeeeuuuu ;______;"
        
        
    def _setup_ui(self):
        '''Instantiates the widgets, and sets the layout'''
        widget_dict = self._widget_dict
        action_dict = self._action_dict
        
        # Classes
        conv_output_cls     = extension.get_default('conversation output')
        smiley_chooser_cls  = extension.get_default('smiley chooser')
        avatar_cls          = extension.get_default('avatar')
        info_panel_cls      = extension.get_default('info panel')
        
        # Actions
        icon_path = gui.theme.emote_to_path(':)')[6:]
        action_dict['add_smiley']   = QtGui.QAction(
                            QtGui.QIcon(icon_path), "Add Smiley", self)
        icon_path = gui.theme.emote_to_path(':S')[6:]
        action_dict['send_nudge']   = QtGui.QAction(
                            QtGui.QIcon(icon_path),"Send Nudge", self)
        action_dict['change_font']  = QtGui.QAction(
                            QtGui.QIcon(""),  "Change Font", self)
        action_dict['change_color'] = QtGui.QAction(
                            QtGui.QIcon(""), "Change Color", self) 
    
        
        # TOP LEFT
        widget_dict['chat_output'] = conv_output_cls()
        top_left_lay = QtGui.QHBoxLayout()
        top_left_lay.addWidget(widget_dict['chat_output'])
        
        
        # BOTTOM LEFT
        widget_dict['toolbar'] = QtGui.QToolBar(self)
        widget_dict['smiley_chooser'] = smiley_chooser_cls()
        widget_dict['chat_input'] = Widgets.ChatInput()
        widget_dict['send_btn'] = QtGui.QPushButton("Send")
        
        text_edit_lay = QtGui.QHBoxLayout()
        text_edit_lay.addWidget(widget_dict['chat_input'])
        text_edit_lay.addWidget(widget_dict['send_btn'])
        
        bottom_left_lay = QtGui.QVBoxLayout()
        bottom_left_lay.addWidget(widget_dict['toolbar'])
        bottom_left_lay.addLayout(text_edit_lay)
        
        toolbar = widget_dict['toolbar']
        toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)
        toolbar.addAction(action_dict['add_smiley'])
        toolbar.addAction(action_dict['send_nudge'])
        toolbar.addSeparator()
        toolbar.addAction(action_dict['change_font'])
        toolbar.addAction(action_dict['change_color'])
        
        widget_dict['chat_input'].set_smiley_dict(gui.theme.EMOTES)

        widget_dict['smiley_chooser'].emoticon_selected.connect(
                            self._on_smiley_selected)
        widget_dict['chat_input'].return_pressed.connect(
                            self._on_send_btn_clicked)
        widget_dict['chat_input'].style_changed.connect(
                            self._on_new_style_selected)
        widget_dict['send_btn'].clicked.connect(
                            self._on_send_btn_clicked)
                            
        action_dict['add_smiley'].triggered.connect(
                            self._on_show_smiley_chooser)
        action_dict['send_nudge'].triggered.connect(
                            self.on_notify_attention)
        action_dict['change_font'].triggered.connect(
                            widget_dict['chat_input'].show_font_chooser)
        action_dict['change_color'].triggered.connect(
                            widget_dict['chat_input'].show_color_chooser)
        
        # LEFT (TOP & BOTTOM)
        left_widget = QtGui.QSplitter(Qt.Vertical)
        splitter_up = QtGui.QWidget()
        splitter_down = QtGui.QWidget()
        splitter_up.setLayout(top_left_lay)
        splitter_down.setLayout(bottom_left_lay)
        left_widget.addWidget(splitter_up)
        left_widget.addWidget(splitter_down)

        left_widget.setCollapsible (0, False)
        left_widget.setCollapsible (1, False)
        _, splitter_pos = left_widget.getRange(1)
        left_widget.moveSplitter(splitter_pos, 1)

        # RIGHT
        widget_dict['his_display_pic'] = avatar_cls(self._session)
        widget_dict['my_display_pic'] = avatar_cls(self._session)
        
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
        widget_dict['info_panel'] = info_panel_cls()
        
        lay_no_info = QtGui.QHBoxLayout()
        lay_no_info.addWidget(left_widget)
        lay_no_info.addLayout(right_lay)
        lay = QtGui.QVBoxLayout()
        lay.addWidget(widget_dict['info_panel'])
        lay.addLayout(lay_no_info)
        
        
        self.setLayout(lay)
        
        
    
    # emesene's
    # TODO: put this (and maybe the following) in the base 
    # class as abstract methods
    def on_close(self):
        '''Method called when this chat widget is about to be closed'''
        pass
        
    # emesene's
    
    
    
    def update_single_information(self, nick, message, account): # emesene's
        '''This method is called from the core (e3 or base class or whatever
        to update the contacts infos'''
        # account is a string containing the email
        # does this have to update the picture too?
        status = self._session.contacts.get(account).status
        self._widget_dict['info_panel'].update(status, nick, message, account)
        
        
    def show(self):
        '''Shows the widget'''
        QtGui.QWidget.show(self)
    
    def _on_new_style_selected(self):
        '''Slot called when the user clicks ok in the color chooser or the 
        font chooser'''
        self.cstyle = self._widget_dict['chat_input'].e3_style
   
    def _on_show_smiley_chooser(self):
        '''Slot called when the user clicks the smiley button.
        Show the smiley chooser panel'''
        self._widget_dict['smiley_chooser'].show()


    def _on_smiley_selected(self, shortcut):
        '''Slot called when the user selects a smiley in the smiley 
        chooser panel. Inserts the smiley in the chat edit'''
        # handles cursor position
        self._widget_dict['chat_input'].insert_text_after_cursor(shortcut)
        
    
    def _on_send_btn_clicked(self):
        '''Slot called when the user clicks the send button or presses Enter in
        the chat line editor. Sends the message'''
        message_string = unicode(self._widget_dict['chat_input'].toPlainText())
        if len(message_string) == 0:
            return
        self._widget_dict['chat_input'].clear()
        gui.base.Conversation._on_send_message(self, message_string)
        
    

   


        
        
        
        
        
        
