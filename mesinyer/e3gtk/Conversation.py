import gtk
import gobject

import gui
import utils
import e3common
import extension

class Conversation(gtk.VBox, gui.Conversation):
    '''a widget that contains all the components inside'''
    NAME = 'Conversation'
    DESCRIPTION = 'The widget that displays a conversation'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, session, cid, tab_label, members=None):
        '''constructor'''
        gtk.VBox.__init__(self)
        gui.Conversation.__init__(self, session, cid, members)
        self.set_border_width(1)

        self.tab_label = tab_label

        self._header_visible = session.config.b_show_header
        self._image_visible = session.config.b_show_info
        self._toolbar_visible = session.config.b_show_toolbar

        self.panel = gtk.VPaned()

        Header = extension.get_default('conversation header')
        OutputText = extension.get_default('conversation output')
        InputText = extension.get_default('conversation input')
        ContactInfo = extension.get_default('conversation info')
        ConversationToolbar = extension.get_default(
            'conversation toolbar')

        dialog = extension.get_default('dialog')
        self.header = Header()
        toolbar_handler = e3common.ConversationToolbarHandler(self.session,
            dialog, gui.theme, self)
        self.toolbar = ConversationToolbar(toolbar_handler)
        self.output = OutputText(self.session.config)
        self.input = InputText(self.session.config, self._on_send_message)
        self.info = ContactInfo()

        input_box = gtk.VBox()
        input_box.pack_start(self.toolbar, False)
        input_box.pack_start(self.input, True, True)

        self.panel.pack1(self.output, True, True)
        self.panel.pack2(input_box, True, True)

        self.hbox = gtk.HBox()
        if self.session.config.get_or_set('b_avatar_on_left', False):
            self.hbox.pack_start(self.info, False)
            self.hbox.pack_start(self.panel, True, True)
        else:
            self.hbox.pack_start(self.panel, True, True)
            self.hbox.pack_start(self.info, False)

        self.pack_start(self.header, False)
        self.pack_start(self.hbox, True, True)

        if len(self.members) == 0:
            self.header.information = ('connecting', 'creating conversation')

        self.header.set_image(gui.theme.user)
        self.info.first = utils.safe_gtk_image_load(gui.theme.logo)
        self.info.last = utils.safe_gtk_image_load(gui.theme.logo)

        self._load_style()

        self.session.config.subscribe(self._on_show_toolbar_changed,
            'b_show_toolbar')
        self.session.config.subscribe(self._on_show_header_changed,
            'b_show_header')
        self.session.config.subscribe(self._on_show_info_changed,
            'b_show_info')

        self.tab_index=-1 # used to select an existing conversation

    def _on_show_toolbar_changed(self, value):
        '''callback called when config.b_show_toolbar changes'''
        if value:
            self.toolbar.show()
        else:
            self.toolbar.hide()

    def _on_show_header_changed(self, value):
        '''callback called when config.b_show_header changes'''
        if value:
            self.header.show()
        else:
            self.header.hide()

    def _on_show_info_changed(self, value):
        '''callback called when config.b_show_info changes'''
        if value:
            self.info.show()
        else:
            self.info.hide()

    def on_close(self):
        '''called when the conversation is closed'''
        self.session.config.unsubscribe(self._on_show_toolbar_changed,
            'b_show_toolbar')

    def show(self):
        '''override the show method'''
        gtk.VBox.show(self)

        if self.session.config.b_show_header:
            self.header.show_all()

        self.info.show_all()
        if not self.session.config.b_show_info:
            self.info.hide()

        self.hbox.show()
        self.panel.show_all()

        self.input.grab_focus()

        if not self.session.config.b_show_toolbar:
            self.toolbar.hide()

    def update_panel_position(self):
        """update the panel position to be on the 80% of the height
        """
        position = self.panel.get_position()
        if position:
            self.panel.set_position(int(position * 0.8))

    def update_message_waiting(self, is_waiting):
        """
        update the information on the conversation to inform if a message
        is waiting

        is_waiting -- boolean value that indicates if a message is waiting
        """
        self.update_tab()

    def update_single_information(self, nick, message, account):
        """
        update the information for a conversation with a single user

        nick -- the nick of the other account (escaped)
        message -- the message of the other account (escaped)
        account -- the account
        """
        self.header.information = (message, account)
        self.update_tab()

    def show_tab_menu(self):
        '''callback called when the user press a button over a widget
        chek if it's the right button and display the menu'''
        pass

    def update_tab(self):
        '''update the values of the tab'''
        self.tab_label.set_image(self.icon)
        self.tab_label.set_text(self.text)

    def update_group_information(self):
        """
        update the information for a conversation with multiple users
        """
        self.header.set_image(gui.theme.users)
        text = 'Group chat'

        self.header.information = \
            (text, '%d members' % (len(self.members) + 1,))

        self.update_tab()

    def set_image_visible(self, is_visible):
        """
        set the visibility of the widget that displays the images of the members

        is_visible -- boolean that says if the widget should be shown or hidden
        """
        if is_visible:
            self.info.show()
        else:
            self.info.hide()

    def set_header_visible(self, is_visible):
        '''
        hide or show the widget according to is_visible

        is_visible -- boolean that says if the widget should be shown or hidden
        '''
        if is_visible:
            self.header.show()
        else:
            self.header.hide()

    def set_toolbar_visible(self, is_visible):
        '''
        hide or show the widget according to is_visible

        is_visible -- boolean that says if the widget should be shown or hidden
        '''
        if is_visible:
            self.toolbar.show()
        else:
            self.toolbar.hide()

    def on_emote(self, emote):
        '''called when an emoticon is selected'''
        self.input.append(gobject.markup_escape_text(emote))
        self.input.grab_focus()
