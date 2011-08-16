# -*- coding: utf-8 -*-

'''This module contains classes to represent the conversation tab.'''

import logging

import PyQt4.QtGui      as QtGui
import PyQt4.QtCore     as QtCore
from PyQt4.QtCore   import Qt

from gui.qt4ui.Utils import tr

import extension
import gui
import gui.qt4ui.widgets as Widgets
from   gui.qt4ui     import Utils


log = logging.getLogger('qt4ui.Conversation')

class Conversation (gui.base.Conversation, QtGui.QWidget):
    '''This widget represents the contents of a chat tab in the conversations
    page'''
    # pylint: disable=W0612
    NAME = 'MainPage'
    DESCRIPTION = 'The widget used to to display a single conversation'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''
    # pylint: enable=W0612
    
    def __init__(self, session, conv_id, members=None, parent=None):
        '''Constructor'''
        gui.base.Conversation.__init__(self, session, conv_id, None, members)
        QtGui.QWidget.__init__(self, parent)
        
        self._session = session
        self._conv_id = conv_id
        self._members = members
        self._on_typing_timer = QtCore.QTimer()
        
        # a widget dic to avoid proliferation of instance variables:
        self._widget_d = {}
        # an action dict to avoid proliferation of instance variables:
        self._action_dict = {}
        
        self._setup_ui()
        
        # emesene's
        self.tab_index = 0
        self.input = self._widget_d['chat_input']
        self.output = self._widget_d['chat_output']
        
        #FIXME: move this to base class
        self._load_style()
        self._widget_d['chat_input'].e3_style = self.cstyle
        
        # not a particularly nice lambda....
        # FIXME: This will have to be changed when groups will be
        #        implemented
        self._on_typing_timer.setSingleShot(True)
        self._on_typing_timer.timeout.connect(
            lambda *args: self._widget_d['info_panel'].set_icon(
                gui.theme.image_theme.status_icons[
                    self._session.contacts.get(
                        self._members[0]).status]))

        self.subscribe_signals()

#        self.session.signals.contact_attr_changed.subscribe(
#            self.on_contact_attr_changed_succeed)
#        self.session.signals.filetransfer_invitation.subscribe(
#                self.on_filetransfer_invitation)
#        self.session.signals.filetransfer_accepted.subscribe(
#                self.on_filetransfer_accepted)
#        self.session.signals.filetransfer_progress.subscribe(
#                self.on_filetransfer_progress)
#        self.session.signals.filetransfer_completed.subscribe(
#                self.on_filetransfer_completed)
        
        
    def __del__(self):
        log.debug('conversation adieeeeeeeuuuu ;______;')
        
        
    def _setup_ui(self):
        '''Instantiates the widgets, and sets the layout'''
        widget_d = self._widget_d
        action_dict = self._action_dict
        
        # Classes
        conv_output_cls     = extension.get_default('conversation output')
        smiley_chooser_cls  = extension.get_default('smiley chooser')
        avatar_cls          = extension.get_default('avatar')
        info_panel_cls      = extension.get_default('info panel')
        
        # Actions
        icon_path = gui.theme.emote_theme.emote_to_path(':)')[6:]
        action_dict['add_smiley']   = QtGui.QAction(
                            QtGui.QIcon(icon_path), tr('Add Smiley'), self)
        icon_path = gui.theme.emote_theme.emote_to_path(':S')[6:]
        action_dict['send_nudge']   = QtGui.QAction(
                            QtGui.QIcon(icon_path), tr('Send Nudge'), self)
        action_dict['change_font']  = QtGui.QAction(
                            QtGui.QIcon(""),  tr('Change Font'), self)
        action_dict['change_color'] = QtGui.QAction(
                            QtGui.QIcon(""), tr('Change Color'), self) 
    
        
        # TOP LEFT
        widget_d['chat_output'] = conv_output_cls()
        top_left_lay = QtGui.QHBoxLayout()
        top_left_lay.addWidget(widget_d['chat_output'])
        
        
        # BOTTOM LEFT
        widget_d['toolbar'] = QtGui.QToolBar(self)
        widget_d['smiley_chooser'] = smiley_chooser_cls()
        widget_d['chat_input'] = Widgets.ChatInput()
        
        text_edit_lay = QtGui.QHBoxLayout()
        text_edit_lay.addWidget(widget_d['chat_input'])
        
        bottom_left_lay = QtGui.QVBoxLayout()
        bottom_left_lay.addWidget(widget_d['toolbar'])
        bottom_left_lay.addLayout(text_edit_lay)
        
        toolbar = widget_d['toolbar']
        toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)
        toolbar.addAction(action_dict['add_smiley'])
        toolbar.addAction(action_dict['send_nudge'])
        toolbar.addSeparator()
        toolbar.addAction(action_dict['change_font'])
        toolbar.addAction(action_dict['change_color'])
        
        widget_d['chat_input'].set_smiley_dict(gui.theme.emote_theme.emotes)

        widget_d['smiley_chooser'].emoticon_selected.connect(
                            self._on_smiley_selected)
        widget_d['chat_input'].return_pressed.connect(
                            self._on_send_btn_clicked)
        widget_d['chat_input'].style_changed.connect(
                            self._on_new_style_selected)
                            
        action_dict['add_smiley'].triggered.connect(
                            self._on_show_smiley_chooser)
        action_dict['send_nudge'].triggered.connect(
                            self.on_notify_attention)
        action_dict['change_font'].triggered.connect(
                            widget_d['chat_input'].show_font_chooser)
        action_dict['change_color'].triggered.connect(
                            widget_d['chat_input'].show_color_chooser)
        
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
        widget_d['his_display_pic'] = avatar_cls(self._session)
        widget_d['my_display_pic'] = avatar_cls(self._session)
        
        right_lay = QtGui.QVBoxLayout()
        right_lay.addWidget(widget_d['his_display_pic'])
        right_lay.addStretch()
        right_lay.addWidget(widget_d['my_display_pic'])
        
        widget_d['my_display_pic'].set_display_pic_of_account()
        if self._members:
            his_email = self._members[0]
            widget_d['his_display_pic'].set_display_pic_of_account(
                                                                his_email)

        # LEFT & RIGHT
        widget_d['info_panel'] = info_panel_cls()
        
        lay_no_info = QtGui.QHBoxLayout()
        lay_no_info.addWidget(left_widget)
        lay_no_info.addLayout(right_lay)
        lay = QtGui.QVBoxLayout()
        lay.addWidget(widget_d['info_panel'])
        lay.addLayout(lay_no_info)
        
        
        self.setLayout(lay)
        
        
    
    # emesene's
    
    def input_grab_focus(self):
        '''sets the focus on the input widget'''
        self._widget_d['chat_input'].setFocus(Qt.OtherFocusReason)

    # TODO: put this (and maybe the following) in the base 
    # class as abstract methods
    def on_close(self):
        '''Method called when this chat widget is about to be closed'''
        self.unsubscribe_signals()
        pass
        
    # emesene's

    def iconify(self):
        '''override the iconify method'''
        pass
    
    def _on_avatarsize_changed(self, value):
        '''callback called when config.i_conv_avatar_size changes'''
        pass

    def _on_show_toolbar_changed(self, value):
        '''callback called when config.b_show_toolbar changes'''
        self.set_toolbar_visible(value)

    def _on_show_header_changed(self, value):
        '''callback called when config.b_show_header changes'''
        self.set_header_visible(value)

    def _on_show_info_changed(self, value):
        '''callback called when config.b_show_info changes'''
        self.set_image_visible(value)

    def _on_show_avatar_onleft(self,value):
        '''callback called when config.b_avatar_on_left changes'''
        pass

    def _on_icon_size_change(self, value):
        '''callback called when config.b_toolbar_small changes'''
        pass

    def on_picture_change_succeed(self, account, path):
        '''callback called when the picture of an account is changed'''
        pass

    def update_message_waiting(self, is_waiting):
        """
        update the information on the conversation to inform if a message is waiting

        is_waiting -- boolean value that indicates if a message is waiting
        """
        pass

    def update_single_information(self, nick, message, account): # emesene's
        '''This method is called from the core (e3 or base class or whatever
        to update the contacts infos'''
        # account is a string containing the email
        # does this have to update the picture too?
        log.debug('UPSingInfo Start')
        status = self._session.contacts.get(account).status
        log.debug('UpSingInfo: [%s], [%s], [%s], [%s]' % (status, nick, message, account))
        self._widget_d['info_panel'].set_all(status, Utils.unescape(nick), Utils.unescape(message), account)
        log.debug('UPSingInfo Stop')
        
    def show(self, other_started=False):
        '''Shows the widget'''
        QtGui.QWidget.show(self)
    
    def _on_new_style_selected(self):
        '''Slot called when the user clicks ok in the color chooser or the 
        font chooser'''
        self.cstyle = self._widget_d['chat_input'].e3_style
   
    def _on_show_smiley_chooser(self):
        '''Slot called when the user clicks the smiley button.
        Show the smiley chooser panel'''
        self._widget_d['smiley_chooser'].show()


    def _on_smiley_selected(self, shortcut):
        '''Slot called when the user selects a smiley in the smiley 
        chooser panel. Inserts the smiley in the chat edit'''
        # handles cursor position
        self._widget_d['chat_input'].insert_text_after_cursor(shortcut)
        
    
    def _on_send_btn_clicked(self):
        '''Slot called when the user clicks the send button or presses Enter in
        the chat line editor. Sends the message'''
        message_string = unicode(self._widget_d['chat_input'].toPlainText())
        if len(message_string) == 0:
            return
        self._widget_d['chat_input'].clear()
        gui.base.Conversation._on_send_message(self, message_string)
        
        
    # TODO: use self.icon extensively
    # TODO: could we handle this directly in UserInfoPanel (but I think that
    #       this wouldn't make self.icon usable :/)
    def on_contact_attr_changed_succeed(self, account, what, old,
            do_notify=True):
        ''' called when contacts change their attributes'''
        if account in self._members:
            if what  == 'status':
                # FIXME: self.icon doesn't beahave correctly at the 
                # moment. That's probably because 'set message
                # waiting' stuff is still not implemented (in fact
                # self.icon returns that icon.)
                #self._widget_d['info_panel'].set_icon(self.icon)
                status = self._session.contacts.get(account).status
                icon =  gui.theme.image_theme.status_icons[status]
                self._widget_d['info_panel'].set_icon(icon)
            elif what == 'nick':
                self._widget_d['info_panel'].set_nick(self.text)
            elif what == 'message':
                message = self._session.contacts.get(account).message
                self._widget_d['info_panel'].set_message(message)
                
    def on_user_typing(self, account):
        '''method called when a someone is typing'''
        # TODO: this should update the tabs' icon, not this one.
        # updating the tab icon should be done here, not in the Conversation
        # page class. 
        self._widget_d['info_panel'].set_icon(gui.theme.image_theme.typing)
        self._on_typing_timer.start(3000)

    def update_group_information(self):
        """
        update the information for a conversation with multiple users
        """
        pass


    def set_sensitive(self, is_sensitive):
        """
        used to make the conversation insensitive while the conversation
        is still open while the user is disconnected and to set it back to
        sensitive when the user is reconnected
        """
        pass

    def set_image_visible(self, is_visible):
        """
        set the visibility of the widget that displays the images of the members

        is_visible -- boolean that says if the widget should be shown or hidden
        """
        pass

    def set_header_visible(self, is_visible):
        '''
        hide or show the widget according to is_visible

        is_visible -- boolean that says if the widget should be shown or hidden
        '''
        if is_visible:
            self._widget_d['info_panel'].show()
        else:
            self._widget_d['info_panel'].hide()

    def set_toolbar_visible(self, is_visible):
        '''
        hide or show the widget according to is_visible

        is_visible -- boolean that says if the widget should be shown or hidden
        '''
        if is_visible:
            self._widget_d['toolbar'].show()
        else:
            self._widget_d['toolbar'].hide()

    def on_toggle_avatar(self):
        '''hide or show the avatar bar'''
        pass
        
    def on_filetransfer_invitation(self, transfer, conv_id):
        ''' called when a new file transfer is issued '''
        if self._conv_id != conv_id:
            return
            
        self.transferw = extension.get_and_instantiate('filetransfer widget', 
                                                       self._session, transfer)
        self.transferw.show()

    def on_filetransfer_accepted(self, transfer):
        ''' called when the file transfer is accepted '''
        pass

    def on_filetransfer_progress(self, transfer):
        ''' called every chunk received '''
        self.transferw.update()

    def on_filetransfer_rejected(self, transfer):
        ''' called when a file transfer is rejected '''
        pass
        
    def on_filetransfer_completed(self, transfer):
        ''' called when a file transfer is completed '''
        pass

    def on_filetransfer_canceled(self, transfer):
        ''' called when a file transfer is canceled '''
        pass

    def on_call_invitation(self, call, cid, westart=False):
        '''called when a new call is issued both from us or other party'''
        pass

    def on_video_call(self):
        '''called when the user is requesting a video-only call'''
        pass

    def on_voice_call(self):
        '''called when the user is requesting an audio-only call'''
        pass

    def on_av_call(self):
        '''called when the user is requesting an audio-video call'''
        pass
   


        
        
        
        
        
        
