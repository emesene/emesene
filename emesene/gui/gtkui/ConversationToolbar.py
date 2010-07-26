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

        toolbar_small = handler.session.config.get_or_set('b_toolbar_small', False)

        if toolbar_small:
            size = gtk.ICON_SIZE_MENU
        else:
            size = gtk.ICON_SIZE_LARGE_TOOLBAR

        whsize = gtk.icon_size_lookup(size)

        settings = self.get_settings()
        settings.set_long_property('gtk-toolbar-icon-size', size, \
            'ConversationToolbar.py:37')

        self.handler = handler

        # check if we have theme-specific toolbar-icons
        if gui.theme.toolbar_path:
            theme_tool_font = utils.safe_gtk_image_load(gui.theme.tool_font, whsize)
            theme_tool_font_color = utils.safe_gtk_image_load(gui.theme.tool_font_color, whsize)
            theme_tool_emotes = utils.safe_gtk_image_load(gui.theme.tool_emotes, whsize)
            theme_tool_nudge = utils.safe_gtk_image_load(gui.theme.tool_nudge, whsize)
            theme_tool_invite = utils.safe_gtk_image_load(gui.theme.tool_invite, whsize)
            theme_tool_clean = utils.safe_gtk_image_load(gui.theme.tool_clean, whsize)
            theme_tool_file_transfer = utils.safe_gtk_image_load(gui.theme.tool_file_transfer, whsize)
        else:
            theme_tool_font = gtk.STOCK_SELECT_FONT
            theme_tool_font_color = gtk.STOCK_SELECT_COLOR
            theme_tool_emotes = utils.safe_gtk_image_load(gui.theme.emote_to_path(':D', True), whsize)
            theme_tool_nudge = utils.safe_gtk_image_load(gui.theme.emote_to_path(':S', True), whsize)
            theme_tool_invite = gtk.STOCK_ADD
            theme_tool_clean = gtk.STOCK_CLEAR
            theme_tool_file_transfer = gtk.STOCK_GO_UP

        self.font = gtk.ToolButton(theme_tool_font)
        self.font.set_label(_('Select font'))
        self.font.connect('clicked',
            lambda *args: self.handler.on_font_selected())

        self.color = gtk.ToolButton(theme_tool_font_color)
        self.color.set_label(_('Select font color'))
        self.color.connect('clicked',
            lambda *args: self.handler.on_color_selected())

        self.emotes = gtk.ToolButton(theme_tool_emotes)
        self.emotes.set_label(_('Send an emoticon'))
        self.emotes.connect('clicked',
            lambda *args: self.handler.on_emotes_selected())

        self.nudge = gtk.ToolButton(theme_tool_nudge)
        self.nudge.set_label(_('Request attention'))
        self.nudge.connect('clicked',
            lambda *args: self.handler.on_notify_attention_selected())

        self.invite = gtk.ToolButton(theme_tool_invite)
        self.invite.set_label(_('Invite a buddy'))
        self.invite.connect('clicked',
            lambda *args: self.handler.on_invite_selected())

        self.clean = gtk.ToolButton(theme_tool_clean)
        self.clean.set_label(_('Clean the conversation'))
        self.clean.connect('clicked',
            lambda *args: self.handler.on_clean_selected())

        self.invite_file_transfer = gtk.ToolButton(theme_tool_file_transfer)
        self.invite_file_transfer.set_label(_('Send a file'))
        self.invite_file_transfer.connect('clicked',
            lambda *args: self.handler.on_invite_file_transfer_selected())


        self.add(self.font)
        self.add(self.color)
        self.add(gtk.SeparatorToolItem())

        self.add(self.emotes)
        self.add(self.nudge)
        self.add(gtk.SeparatorToolItem())

        self.add(self.invite)
        self.add(self.clean)

        self.add(self.invite_file_transfer)


