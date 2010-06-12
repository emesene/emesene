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
        self.handler = handler

        self.font = gtk.ToolButton(gtk.STOCK_SELECT_FONT)
        self.font.connect('clicked',
            lambda *args: self.handler.on_font_selected())
        self.color = gtk.ToolButton(gtk.STOCK_SELECT_COLOR)
        self.color.connect('clicked',
            lambda *args: self.handler.on_color_selected())

        self.emotes = gtk.ToolButton(
            utils.safe_gtk_image_load(gui.theme.emote_to_path(':D', True)), 'Emotes')
        self.emotes.connect('clicked',
            lambda *args: self.handler.on_emotes_selected())
        self.nudge = gtk.ToolButton(
            utils.safe_gtk_image_load(gui.theme.emote_to_path(':S', True)), 'Nudge')
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


