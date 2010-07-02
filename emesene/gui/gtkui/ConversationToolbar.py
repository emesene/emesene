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

        self.font = gtk.ToolButton(gtk.STOCK_SELECT_FONT)
        self.font.connect('clicked',
            lambda *args: self.handler.on_font_selected())
        self.color = gtk.ToolButton(gtk.STOCK_SELECT_COLOR)
        self.color.connect('clicked',
            lambda *args: self.handler.on_color_selected())

        emotes_img = utils.safe_gtk_image_load(
                gui.theme.emote_to_path(':D', True), whsize)
        self.emotes = gtk.ToolButton(emotes_img, 'Emotes')
        self.emotes.connect('clicked',
            lambda *args: self.handler.on_emotes_selected())

        nudge_img = utils.safe_gtk_image_load(
                gui.theme.emote_to_path(':S', True), whsize)
        self.nudge = gtk.ToolButton(nudge_img, 'Nudge')
        self.nudge.connect('clicked',
            lambda *args: self.handler.on_notify_attention_selected())

        self.invite = gtk.ToolButton(gtk.STOCK_ADD)
        self.invite.connect('clicked',
            lambda *args: self.handler.on_invite_selected())
        self.clean = gtk.ToolButton(gtk.STOCK_CLEAR)
        self.clean.connect('clicked',
            lambda *args: self.handler.on_clean_selected())

        self.invite_file_transfer = gtk.ToolButton(gtk.STOCK_GO_UP)
        self.invite_file_transfer.set_label(_('Send File'))
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


