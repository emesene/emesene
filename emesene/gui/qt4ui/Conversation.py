# -*- coding: utf-8 -*-

#    This file is part of emesene.
#
#    emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    emesene is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with emesene; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

'''This module contains classes to represent the conversation tab.'''

import logging

import PyQt4.QtGui as QtGui
import PyQt4.QtCore as QtCore
from PyQt4.QtCore import Qt

from gui.qt4ui.Utils import tr

import extension
import gui
from gui.base import Plus
import gui.qt4ui.widgets as Widgets
log = logging.getLogger('qt4ui.Conversation')


class Conversation (gui.base.Conversation, QtGui.QWidget):
    '''This widget represents the contents of a chat tab in the conversations
    page'''
    NAME = 'MainPage'
    DESCRIPTION = 'The widget used to to display a single conversation'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''

    def __init__(self, session, conv_id, members=None, parent=None):
        '''Constructor'''
        gui.base.Conversation.__init__(self, session, conv_id, None, members)
        QtGui.QWidget.__init__(self, parent)

        self._on_typing_timer = QtCore.QTimer()

        # a widget dic to avoid proliferation of instance variables:
        self._widget_d = {}
        self._setup_ui()

        #update information
        if len(self.members) == 0:
            self.header.information = ('connecting', 'creating conversation')
        else:
            #update adium theme header/footer
            account = self.members[0]
            contact = self.session.contacts.safe_get(account)
            his_picture = contact.picture
            nick = contact.nick
            display_name = contact.display_name
            self.set_sensitive(not contact.blocked, True)
            my_picture = self.session.contacts.me.picture
            self.output.clear(account, nick, display_name,
                              my_picture, his_picture)

        # emesene's
        self.tab_index = 0
        self.conv_manager = None

        self._load_style()
        self.input.e3_style = self.cstyle

        self.typing_timeout = QtCore.QTimer()
        self.typing_timeout.setSingleShot(False)
        self.typing_timeout.timeout.connect(self.update_tab)

        self.subscribe_signals()

    def _setup_ui(self):
        '''Instantiates the widgets, and sets the layout'''
        widget_d = self._widget_d

        # Classes
        conv_output_cls = extension.get_default('conversation output')
        smiley_chooser_cls = extension.get_default('smiley chooser')
        info_panel_cls = extension.get_default('info panel')
        conv_toolbar_cls = extension.get_default('conversation toolbar')
        ContactInfo = extension.get_default('conversation info')

        # TOP LEFT
        self.output = conv_output_cls(self.session.config)
        top_left_lay = QtGui.QHBoxLayout()
        top_left_lay.setContentsMargins(0, 0, 0, 0)
        top_left_lay.addWidget(self.output)

        # BOTTOM LEFT
        self.toolbar_handler = gui.base.ConversationToolbarHandler(self.session,
                                 gui.theme, self)
        self.toolbar = conv_toolbar_cls(self.toolbar_handler, self.session)
        self.toolbar.redraw_ublock_button(self._get_first_contact().blocked)
        self.toolbar.update_toggle_avatar_icon(self.session.config.b_show_info)

        widget_d['smiley_chooser'] = smiley_chooser_cls()
        self.input = Widgets.ChatInput(self._on_send_message,
                               self.cycle_history,
                               self._send_typing_notification)

        self.bottom_left_lay = QtGui.QVBoxLayout()
        self.bottom_left_lay.setContentsMargins(0, 0, 0, 0)
        self.bottom_left_lay.addWidget(self.toolbar)
        self.bottom_left_lay.addWidget(self.input)
        if self.below_conversation:
            self.bottom_left_lay.addWidget(self.below_conversation)

        self.input.set_smiley_dict(gui.theme.emote_theme.emotes)
        widget_d['smiley_chooser'].emoticon_selected.connect(
                            self._on_smiley_selected)
        self.input.style_changed.connect(
                            self._on_new_style_selected)

        BelowConversation = extension.get_default('below conversation')
        if BelowConversation is not None:
            self.below_conversation = BelowConversation(self, self.session)

        # LEFT (TOP & BOTTOM)
        self.left_widget = QtGui.QSplitter(Qt.Vertical)
        splitter_up = QtGui.QWidget()
        splitter_down = QtGui.QWidget()
        splitter_up.setLayout(top_left_lay)
        splitter_down.setLayout(self.bottom_left_lay)
        self.left_widget.addWidget(splitter_up)
        self.left_widget.addWidget(splitter_down)
        self.left_widget.splitterMoved.connect(self.on_input_panel_resize)
        self.left_widget.setCollapsible(0, False)
        self.left_widget.setCollapsible(1, False)
        self.update_panel_position()

        # RIGHT
        self.info = ContactInfo(self.session, self.members)

        # LEFT & RIGHT
        self.header = info_panel_cls(self.session, self.members)

        self.lay_no_info = QtGui.QGridLayout()
        self.lay_no_info.addWidget(self.left_widget, 0, 1)
        self.lay_no_info.addWidget(self.info, 0, 2)
        lay = QtGui.QVBoxLayout()
        lay.setContentsMargins(1, 1, 1, 1)
        lay.addWidget(self.header)
        lay.addLayout(self.lay_no_info)

        self.setLayout(lay)

    def on_font_selected(self, style):
        '''called when a new font is selected'''
        gui.base.Conversation.on_font_selected(self, style)
        self.input.e3_style = style

    def input_grab_focus(self):
        '''sets the focus on the input widget'''
        self.input.setFocus(Qt.OtherFocusReason)

    def on_conversation_info_extension_changed(self, new_extension):
        if type(self.info) != new_extension:
            self.lay_no_info.removeWidget(self.info)
            self.info = None

            if new_extension:
                self.info = new_extension(self.session, self.members)
                if self.session.config.get_or_set('b_avatar_on_left', False):
                    self.lay_no_info.addWidget(self.info, 0, 1)
                    self.lay_no_info.removeWidget(self.left_widget)
                    self.lay_no_info.addWidget(self.left_widget, 0, 2)
                else:
                    self.lay_no_info.removeWidget(self.left_widget)
                    self.lay_no_info.addWidget(self.left_widget, 0, 1)
                    self.lay_no_info.addWidget(self.info, 0, 2)

            if self.session.config.b_show_info:
                self.info.show()

    def on_below_conversation_changed(self, newvalue):
        if type(self.below_conversation) != newvalue:
            #replace the below conversation
            if not self.below_conversation is None:
                self.bottom_left_lay.removeWidget(self.below_conversation)
                self.below_conversation = None

            if newvalue:
                self.below_conversation = newvalue(self, self.session)
                self.bottom_left_lay.addWidget(self.below_conversation)
                self.below_conversation.show()

    def on_close(self):
        '''Method called when this chat widget is about to be closed'''
        self.unsubscribe_signals()
        self.info.destroy()

    def update_panel_position(self):
        """update the panel position to be on the 80% of the height
        """
        min_, max_ = self.left_widget.getRange(1)
        height = max_ - min_
        if height > 0:
            pos = self.session.config.get_or_set("i_input_panel_position",
                    int(height * 0.8))
            self.left_widget.moveSplitter(pos, 1)

        policy = self.left_widget.sizePolicy()
        policy.setHorizontalStretch(80)
        self.left_widget.setSizePolicy(policy)

    def on_input_panel_resize(self, pos, index):
        self.session.config.i_input_panel_position = pos

    def iconify(self):
        '''override the iconify method'''
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
        self.toolbar.update_toggle_avatar_icon(value)

    def _on_show_avatar_onleft(self, value):
        '''callback called when config.b_avatar_on_left changes'''
        if self.session.config.get_or_set('b_avatar_on_left', False):
            self.lay_no_info.addWidget(self.info, 0, 1)
            self.lay_no_info.removeWidget(self.left_widget)
            self.lay_no_info.addWidget(self.left_widget, 0, 2)
        else:
            self.lay_no_info.removeWidget(self.left_widget)
            self.lay_no_info.addWidget(self.left_widget, 0, 1)
            self.lay_no_info.addWidget(self.info, 0, 2)

    def _on_icon_size_change(self, value):
        '''callback called when config.b_toolbar_small changes'''
        pass

    def show(self, other_started=False):
        '''Shows the widget'''
        QtGui.QWidget.show(self)

    def _on_new_style_selected(self):
        '''Slot called when the user clicks ok in the color chooser or the
        font chooser'''
        self.cstyle = self.input.e3_style

    def _on_show_smiley_chooser(self):
        '''Slot called when the user clicks the smiley button.
        Show the smiley chooser panel'''
        self._widget_d['smiley_chooser'].show()

    def _on_smiley_selected(self, shortcut):
        '''Slot called when the user selects a smiley in the smiley
        chooser panel. Inserts the smiley in the chat edit'''
        # handles cursor position
        self.input.insert_text_after_cursor(shortcut)

    def on_user_typing(self, account):
        """
        inform that the other user has started typing
        """
        if account in self.members:
            self.tab_label.set_image(gui.theme.image_theme.typing)
            if self.typing_timeout.isActive():
                self.typing_timeout.stop()
            self.typing_timeout.start(3000)

    def update_tab(self):
        '''update the values of the tab'''
        self.typing_timeout.stop()
        self.conv_manager.setTabText(self.tab_index,
            Plus.msnplus_strip(self.text))
        self.conv_manager.setTabIcon(self.tab_index, QtGui.QIcon(self.icon))

        #FIXME: implement show_avatar_in_taskbar option

    def set_sensitive(self, is_sensitive, force_sensitive_block_button=False):
        """
        used to make the conversation insensitive while the conversation
        is still open while the user is disconnected and to set it back to
        sensitive when the user is reconnected
        """
        self.info.set_sensitive(is_sensitive or force_sensitive_block_button)
        self.toolbar.set_sensitive(is_sensitive, force_sensitive_block_button)
        self.input.setEnabled(is_sensitive)
        self.header.setEnabled(is_sensitive or force_sensitive_block_button)

        # redraws block button to its corresponding icon and tooltip
        contact_unblocked = not force_sensitive_block_button or is_sensitive
        self.toolbar.redraw_ublock_button(contact_unblocked)

    def set_image_visible(self, is_visible):
        """
        set the visibility of the widget that displays the images of the members

        is_visible -- boolean that says if the widget should be shown or hidden
        """
        self.info.setVisible(is_visible)

    def set_header_visible(self, is_visible):
        '''
        hide or show the widget according to is_visible

        is_visible -- boolean that says if the widget should be shown or hidden
        '''
        self.header.setVisible(is_visible)

    def set_toolbar_visible(self, is_visible):
        '''
        hide or show the widget according to is_visible

        is_visible -- boolean that says if the widget should be shown or hidden
        '''
        self.toolbar.setVisible(is_visible)

    def _get_first_contact(self):
        account = self.members[0]
        contact = self.session.contacts.contacts[account]
        return contact

    def on_filetransfer_invitation(self, transfer, conv_id):
        ''' called when a new file transfer is issued '''
        if self.icid != conv_id:
            return

        self.transferw = extension.get_and_instantiate('filetransfer widget',
                                                       self.session, transfer)
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

