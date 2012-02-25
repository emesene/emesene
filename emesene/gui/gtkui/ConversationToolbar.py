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

import gtk

import gui
import utils

class ConversationToolbar(gtk.Toolbar):
    """
    A class that represents the toolbar on the conversation window
    """
    NAME = 'Conversation Toolbar'
    DESCRIPTION = 'The toolbar for a conversation'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, handler):
        """
        constructor

        handler -- an instance of e3common.Handler.ConversationToolbarHandler
        """
        gtk.Toolbar.__init__(self)
        self.set_style(gtk.TOOLBAR_ICONS)
        self.set_tooltips(True)

        self.handler = handler

        self.draw()

    def set_sensitive(self, is_sensitive, force_sensitive_block_button=False):
        self.ublock.set_sensitive(force_sensitive_block_button or is_sensitive)
        self.font.set_sensitive(is_sensitive)
        self.nudge.set_sensitive(is_sensitive)
        self.clean.set_sensitive(is_sensitive)
        self.color.set_sensitive(is_sensitive)
        self.emotes.set_sensitive(is_sensitive)
        self.invite.set_sensitive(is_sensitive)
        self.toggle_avatar.set_sensitive(is_sensitive)
        self.invite_av_call.set_sensitive(is_sensitive)
        self.invite_video_call.set_sensitive(is_sensitive)
        self.invite_audio_call.set_sensitive(is_sensitive)
        self.invite_file_transfer.set_sensitive(is_sensitive)


    def draw(self):
        '''draw the toolbar'''
        toolbar_small = self.handler.session.config.get_or_set('b_toolbar_small', False)

        if toolbar_small:
            size = gtk.ICON_SIZE_MENU
        else:
            size = gtk.ICON_SIZE_LARGE_TOOLBAR

        whsize = gtk.icon_size_lookup(size)

        self.settings = self.get_settings()
        self.settings.set_long_property('gtk-toolbar-icon-size', size, \
            'ConversationToolbar.py:37')

        # check if we have theme-specific toolbar-icons

        image_theme = gui.theme.image_theme
        if image_theme.has_custom_toolbar_icons():
            theme_tool_font = utils.gtk_ico_image_load(image_theme.tool_font, size)
            theme_tool_font_color = utils.gtk_ico_image_load(image_theme.tool_font_color, size)
            theme_tool_emotes = utils.gtk_ico_image_load(image_theme.tool_emotes, size)
            theme_tool_nudge = utils.gtk_ico_image_load(image_theme.tool_nudge, size)
            theme_tool_invite = utils.gtk_ico_image_load(image_theme.tool_invite, size)
            theme_tool_clean = utils.gtk_ico_image_load(image_theme.tool_clean, size)
            theme_tool_file_transfer = utils.gtk_ico_image_load(image_theme.tool_file_transfer, size)
            theme_tool_ublock = utils.gtk_ico_image_load(image_theme.tool_ublock, size)
            theme_tool_toggle_avatar = gtk.STOCK_GO_FORWARD
        else:
            theme_tool_font = gtk.STOCK_SELECT_FONT
            theme_tool_font_color = gtk.STOCK_SELECT_COLOR

            emote_theme = gui.theme.emote_theme

            theme_tool_emotes = utils.gtk_ico_image_load(emote_theme.emote_to_path(':D', True), size)
            theme_tool_nudge = utils.gtk_ico_image_load(emote_theme.emote_to_path(':S', True), size)
            theme_tool_invite = gtk.STOCK_ADD
            theme_tool_clean = gtk.STOCK_CLEAR
            theme_tool_file_transfer = gtk.STOCK_GO_UP
            theme_tool_ublock = gtk.STOCK_STOP
            theme_tool_toggle_avatar = gtk.STOCK_GO_FORWARD

        theme_tool_call = utils.gtk_ico_image_load(image_theme.call, size)
        theme_tool_video = utils.gtk_ico_image_load(image_theme.video, size)
        theme_tool_av = utils.gtk_ico_image_load(image_theme.av, size)

        self.font = gtk.ToolButton(theme_tool_font)
        self.font.set_label(_('Select font'))
        self.font.set_tooltip_text(_('Select font'))
        self.font.connect('clicked',
            lambda *args: self.handler.on_font_selected())

        self.color = gtk.ToolButton(theme_tool_font_color)
        self.color.set_label(_('Select font color'))
        self.color.set_tooltip_text(_('Select font color'))
        self.color.connect('clicked',
            lambda *args: self.handler.on_color_selected())

        self.emotes = gtk.ToolButton(theme_tool_emotes)
        self.emotes.set_label(_('Send an emoticon'))
        self.emotes.set_tooltip_text(_('Send an emoticon'))
        self.emotes.connect('clicked',
            lambda *args: self.handler.on_emotes_selected())

        self.nudge = gtk.ToolButton(theme_tool_nudge)
        self.nudge.set_label(_('Request attention'))
        self.nudge.set_tooltip_text(_('Request attention'))
        self.nudge.connect('clicked',
            lambda *args: self.handler.on_notify_attention_selected())

        self.invite = gtk.ToolButton(theme_tool_invite)
        self.invite.set_label(_('Invite a buddy'))
        self.invite.set_tooltip_text(_('Invite a buddy'))
        self.invite.connect('clicked',
            lambda *args: self.handler.on_invite_selected())

        self.clean = gtk.ToolButton(theme_tool_clean)
        self.clean.set_label(_('Clean the conversation'))
        self.clean.set_tooltip_text(_('Clean the conversation'))
        self.clean.connect('clicked',
            lambda *args: self.handler.on_clean_selected())

        self.invite_file_transfer = gtk.ToolButton(theme_tool_file_transfer)
        self.invite_file_transfer.set_label(_('Send a file'))
        self.invite_file_transfer.set_tooltip_text(_('Send a file'))
        self.invite_file_transfer.connect('clicked',
            lambda *args: self.handler.on_invite_file_transfer_selected())

        self.ublock = gtk.ToolButton(theme_tool_ublock)
        self.ublock.set_label(_('Block/Unblock contact'))
        self.ublock.set_tooltip_text(_('Block/Unblock contact'))
        self.ublock.connect('clicked',
            lambda *args: self.handler.on_ublock_selected())

        self.toggle_avatar = gtk.ToolButton(theme_tool_toggle_avatar)
        self.toggle_avatar.set_label(_('Hide/Show avatar'))
        if self.handler.session.config.b_show_info:
            self.toggle_avatar.set_tooltip_text(_('Hide avatar'))
        else:
            self.toggle_avatar.set_tooltip_text(_('Show avatar'))
        self.toggle_avatar.connect('clicked',
            lambda *args: self.handler.on_toggle_avatar_selected())

        self.invite_video_call = gtk.ToolButton(theme_tool_video)
        self.invite_video_call.set_label(_('Video Call'))
        self.invite_video_call.set_tooltip_text(_('Video Call'))
        self.invite_video_call.connect('clicked',
            lambda *args: self.handler.on_invite_video_call_selected())

        self.invite_audio_call = gtk.ToolButton(theme_tool_call)
        self.invite_audio_call.set_label(_('Voice Call'))
        self.invite_audio_call.set_tooltip_text(_('Voice Call'))
        self.invite_audio_call.connect('clicked',
            lambda *args: self.handler.on_invite_voice_call_selected())

        self.invite_av_call = gtk.ToolButton(theme_tool_av)
        self.invite_av_call.set_label(_('Audio/Video Call'))
        self.invite_av_call.set_tooltip_text(_('Audio/Video Call'))
        self.invite_av_call.connect('clicked',
            lambda *args: self.handler.on_invite_av_call_selected())

        self.add(self.font)
        self.add(self.color)
        self.add(gtk.SeparatorToolItem())

        self.add(self.emotes)
        self.add(self.nudge)
        self.add(gtk.SeparatorToolItem())

        self.add(self.invite)
        if self.handler.session_filetransfer_supported():
            self.add(self.invite_file_transfer)
        self.add(gtk.SeparatorToolItem())

        if self.handler.session_call_supported():
            self.add(self.invite_video_call)
            self.add(self.invite_audio_call)
            self.add(self.invite_av_call)
            self.add(gtk.SeparatorToolItem())

        self.add(self.clean)
        self.add(self.ublock)
        self.add(gtk.SeparatorToolItem())
        self.add(self.toggle_avatar)

