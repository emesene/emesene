import gtk

import gui
import utils
import dialog
import e3common
import dummy_components

class Conversation(gtk.VBox, gui.Conversation):
    '''a widget that contains all the components inside'''

    def __init__(self, session, cid, tab_label, members=None):
        '''constructor'''
        gtk.VBox.__init__(self)
        gui.Conversation.__init__(self, session, cid, members)
        self.set_border_width(1)

        self.tab_label = tab_label

        self._header_visible = True
        self._image_visible = True
        self._toolbar_visible = True

        self.panel = gtk.VPaned()

        Header = dummy_components.get_default('gtk conversation header')
        OutputText = dummy_components.get_default('gtk conversation output')
        InputText = dummy_components.get_default('gtk conversation input')
        ContactInfo = dummy_components.get_default('gtk conversation info')
        ConversationToolbar = dummy_components.get_default(
            'gtk conversation toolbar')


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
        self.hbox.pack_start(self.panel, True, True)
        self.hbox.pack_start(self.info, False)

        self.pack_start(self.header, False)
        self.pack_start(self.hbox, True, True)

        self._panel_show_id = self.panel.connect('map-event',
            self._on_panel_show)

        if len(self.members) == 0:
            self.header.information = ('connecting', 'creating conversation', 
                '')

        self.header.set_image(gui.theme.user)
        self.info.first = utils.safe_gtk_image_load(gui.theme.logo)
        self.info.last = utils.safe_gtk_image_load(gui.theme.logo)

        self._load_style()

    def show(self):
        '''override the show method'''
        gtk.VBox.show(self)

        if self.session.config.b_show_header is None:
            self.session.config.b_show_header = True

        if self.session.config.b_show_info is None:
            self.session.config.b_show_info = True

        if self.session.config.b_show_header:
            self.header.show_all()

        if self.session.config.b_show_info:
            self.info.show_all()

        self.hbox.show()
        self.panel.show_all()

    def update_message_waiting(self, is_waiting):
        """
        update the information on the conversation to inform if a message is waiting
        
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
        self.header.information = (nick, message, account)
        self.update_tab()

    def _on_panel_show(self, widget, event):
        '''callback called when the panel is shown, resize the panel'''
        position = self.panel.get_position()
        self.panel.set_position(position + int(position * 0.6))
        self.panel.disconnect(self._panel_show_id)
        del self._panel_show_id

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
            (text, '%d members' % (len(self.members) + 1,), '')

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

