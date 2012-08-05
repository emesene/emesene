# -*- coding: utf-8 -*-

'''This module contains the AdiumChatOutput class'''
import base64

from PyQt4      import QtGui
from PyQt4      import QtCore
from PyQt4      import QtWebKit
from PyQt4.QtCore   import Qt

import e3
import gui
from gui.base import Plus
from gui.qt4ui  import Utils
from gui.qt4ui.Utils import tr


class ConversationToolbar (QtGui.QToolBar):
    """
    A class that represents the toolbar on the conversation window
    """
    NAME = 'Conversation Toolbar'
    DESCRIPTION = 'The toolbar for a conversation'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, handler, session):
        """
        constructor

        handler -- an instance of e3common.Handler.ConversationToolbarHandler
        """
        QtGui.QToolBar.__init__(self)

        self.handler = handler
        self.session = session

        # an action dict to avoid proliferation of instance variables:
        self._action_dict = {}
        self.draw()

    def redraw_ublock_button(self, contact_unblocked):
        """
        redraws the block button,
        setting the appropiated stock_id and tooltip
        """
        if contact_unblocked:
            ublock_icon = self.theme_tool_block
            tooltip_text = tr('Block contact')
        else:
            ublock_icon = self.theme_tool_unblock
            tooltip_text = tr('Unblock contact')

        self._action_dict['ublock'].setToolTip(tooltip_text)
        self._action_dict['ublock'].setIcon(ublock_icon)

    def set_sensitive(self, is_sensitive, force_sensitive_block_button=False):
        self._action_dict['ublock'].setEnabled(force_sensitive_block_button or is_sensitive)
        self._action_dict['toggle_avatars'].setEnabled(force_sensitive_block_button or is_sensitive)
        self._action_dict['change_font'].setEnabled(is_sensitive)
        self._action_dict['send_nudge'].setEnabled(is_sensitive)
        self._action_dict['clean'].setEnabled(is_sensitive)
        self._action_dict['change_color'].setEnabled(is_sensitive)
        self._action_dict['add_smiley'].setEnabled(is_sensitive)
        self._action_dict['invite'].setEnabled(is_sensitive)

#        self.invite_av_call.set_sensitive(is_sensitive)
#        self.invite_video_call.set_sensitive(is_sensitive)
#        self.invite_audio_call.set_sensitive(is_sensitive)
#        self.invite_file_transfer.set_sensitive(is_sensitive)

    def update_toggle_avatar_icon(self, show_avatars):
        if show_avatars:
            self._action_dict['toggle_avatars'].setIcon(self.theme_tool_hide_avatar)
            self._action_dict['toggle_avatars'].setToolTip(tr('Hide avatar'))
        else:
            self._action_dict['toggle_avatars'].setIcon(self.theme_tool_show_avatar)
            self._action_dict['toggle_avatars'].setToolTip(tr('Show avatar'))

    def draw(self):
        '''draw the toolbar'''

        action_dict = self._action_dict

        self.setToolButtonStyle(Qt.ToolButtonIconOnly)

        #FIXME: toolbar size
        #toolbar_small = self.handler.session.config.get_or_set('b_toolbar_small', False)
        # check if we have theme-specific toolbar-icons

        image_theme = gui.theme.image_theme
        if image_theme.has_custom_toolbar_icons():
            theme_tool_font = QtGui.QIcon(image_theme.tool_font)
            theme_tool_font_color = QtGui.QIcon(image_theme.tool_font_color)
            theme_tool_emotes = QtGui.QIcon(image_theme.tool_emotes)
            theme_tool_nudge = QtGui.QIcon(image_theme.tool_nudge)
            theme_tool_invite = QtGui.QIcon(image_theme.tool_invite)
            theme_tool_clean = QtGui.QIcon(image_theme.tool_clean)
            theme_tool_file_transfer = QtGui.QIcon(image_theme.tool_file_transfer)
            self.theme_tool_block = QtGui.QIcon(image_theme.tool_block)
            self.theme_tool_unblock = QtGui.QIcon(image_theme.tool_unblock)
        else:
            theme_tool_font = QtGui.QIcon.fromTheme("preferences-desktop-font")
            theme_tool_font_color = QtGui.QIcon.fromTheme("preferences-desktop-theme") #FIXME: no stock icon

            emote_theme = gui.theme.emote_theme

            theme_tool_emotes = QtGui.QIcon(emote_theme.emote_to_path(':D', True))
            theme_tool_nudge = QtGui.QIcon(emote_theme.emote_to_path(':S', True))
            theme_tool_invite = QtGui.QIcon.fromTheme("list-add")
            theme_tool_clean = QtGui.QIcon.fromTheme("edit-clear")
            theme_tool_file_transfer = QtGui.QIcon.fromTheme("go-up")
            self.theme_tool_block = QtGui.QIcon.fromTheme("list-remove")
            self.theme_tool_unblock = QtGui.QIcon.fromTheme("list-add")

        if self.session.config.b_avatar_on_left:
            self.theme_tool_hide_avatar = QtGui.QIcon.fromTheme("go-previous")
            self.theme_tool_show_avatar = QtGui.QIcon.fromTheme("go-next")
        else:
            self.theme_tool_hide_avatar = QtGui.QIcon.fromTheme("go-next")
            self.theme_tool_show_avatar = QtGui.QIcon.fromTheme("go-previous")

#FIXME: add icons
#        theme_tool_call = QtGui.QIcon(image_theme.call)
#        theme_tool_video = QtGui.QIcon(image_theme.video)
#        theme_tool_av = QtGui.QIcon(image_theme.av)

        action_dict['change_font']  = QtGui.QAction(theme_tool_font,  tr('Select font'), self)
        action_dict['change_font'].triggered.connect(self.handler.on_font_selected)

        action_dict['change_color'] = QtGui.QAction(theme_tool_font_color, tr('Select font color'), self)
        action_dict['change_color'].triggered.connect(
                            self.handler.on_color_selected)

        action_dict['add_smiley'] = QtGui.QAction(theme_tool_emotes, tr('Send an emoticon'), self)
        #FIXME: this should use self.handler.on_emotes_selected but that isn't working
        action_dict['add_smiley'].triggered.connect(
                            self.handler.conversation._on_show_smiley_chooser)

        action_dict['send_nudge'] = QtGui.QAction(theme_tool_nudge, tr('Request attention'), self)
        action_dict['send_nudge'].triggered.connect(
                            self.handler.on_notify_attention_selected)

        action_dict['invite'] = QtGui.QAction(theme_tool_invite, tr('Invite a buddy'), self)
        action_dict['invite'].triggered.connect(
                            self.handler.on_invite_selected)

        action_dict['clean'] = QtGui.QAction(theme_tool_clean, tr('Clean the conversation'), self)
        action_dict['clean'].triggered.connect(
                            self.handler.on_clean_selected)

#        self.invite_file_transfer = gtk.ToolButton(theme_tool_file_transfer)
#        self.invite_file_transfer.set_label(_('Send a file'))
#        self.invite_file_transfer.set_tooltip_text(_('Send a file'))
#        self.invite_file_transfer.connect('clicked',
#            lambda *args: self.handler.on_invite_file_transfer_selected())

        action_dict['ublock'] = QtGui.QAction(
                            self.theme_tool_show_avatar, tr('Block/Unblock contact'), self)
        action_dict['ublock'].triggered.connect(
                            self.handler.on_ublock_selected)

        action_dict['toggle_avatars'] = QtGui.QAction(
                            self.theme_tool_block, tr('Hide/Show avatar'), self)
        action_dict['toggle_avatars'].triggered.connect(
                            self.handler.on_toggle_avatar_selected)
        self.update_toggle_avatar_icon(self.session.config.b_show_info)

#        self.invite_video_call = gtk.ToolButton(theme_tool_video)
#        self.invite_video_call.set_label(_('Video Call'))
#        self.invite_video_call.set_tooltip_text(_('Video Call'))
#        self.invite_video_call.connect('clicked',
#            lambda *args: self.handler.on_invite_video_call_selected())

#        self.invite_audio_call = gtk.ToolButton(theme_tool_call)
#        self.invite_audio_call.set_label(_('Voice Call'))
#        self.invite_audio_call.set_tooltip_text(_('Voice Call'))
#        self.invite_audio_call.connect('clicked',
#            lambda *args: self.handler.on_invite_voice_call_selected())

#        self.invite_av_call = gtk.ToolButton(theme_tool_av)
#        self.invite_av_call.set_label(_('Audio/Video Call'))
#        self.invite_av_call.set_tooltip_text(_('Audio/Video Call'))
#        self.invite_av_call.connect('clicked',
#            lambda *args: self.handler.on_invite_av_call_selected())

        self.addAction(action_dict['change_font'])
        self.addAction(action_dict['change_color'])
        self.addSeparator()

        self.addAction(action_dict['add_smiley'])
        self.addAction(action_dict['send_nudge'])

        if self.handler.session_service_supported(e3.Session.SERVICE_CONTACT_INVITE):
            self.addSeparator()
            self.addAction(action_dict['invite'])
#FIXME: implement this actions
#        if self.handler.session_service_supported(e3.Session.SERVICE_FILETRANSFER):
#            self.add(self.invite_file_transfer)
        self.addSeparator()

#        if self.handler.session_service_supported(e3.Session.SERVICE_CALLS):
#            self.add(self.invite_video_call)
#            self.add(self.invite_audio_call)
#            self.add(self.invite_av_call)
#            self.addSeparator()

        self.addAction(action_dict['clean'])
        if self.handler.session_service_supported(e3.Session.SERVICE_CONTACT_BLOCK):
            self.addAction(action_dict['ublock'])

        self.addSeparator()
        self.addAction(action_dict['toggle_avatars'])
