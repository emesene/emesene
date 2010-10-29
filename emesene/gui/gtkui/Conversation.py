import gtk
import gobject

import e3
import gui
import utils
import extension

class Conversation(gtk.VBox, gui.Conversation):
    '''a widget that contains all the components inside'''
    NAME = 'Conversation'
    DESCRIPTION = 'The widget that displays a conversation'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, session, cid, update_win, tab_label, members=None):
        '''constructor'''
        gtk.VBox.__init__(self)
        gui.Conversation.__init__(self, session, cid, update_win, members)
        self.set_border_width(2)

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
        TransfersBar = extension.get_default('filetransfer pool')
        dialog = extension.get_default('dialog')
        Avatar = extension.get_default('avatar')

        avatar_size = self.session.config.get_or_set('i_conv_avatar_size', 64)

        self.avatar = Avatar(cellDimention=avatar_size)
        self.his_avatar = Avatar(cellDimention=avatar_size)

        self.header = Header(session, members)
        toolbar_handler = gui.base.ConversationToolbarHandler(self.session,
            dialog, gui.theme, self)
        self.toolbar = ConversationToolbar(toolbar_handler)
        self.output = OutputText(self.session.config)
        self.output.set_size_request(-1, 30)
        self.input = InputText(self.session.config, self._on_send_message,
                self.cycle_history)
        self.output.set_size_request(-1, 25)
        self.input.set_size_request(-1, 25)
        self.info = ContactInfo()
        self.transfers_bar = TransfersBar(self.session)

        frame_input = gtk.Frame()
        frame_input.set_shadow_type(gtk.SHADOW_IN)

        input_box = gtk.VBox()
        input_box.pack_start(self.toolbar, False)
        input_box.pack_start(self.input, True, True)

        frame_input.add(input_box)

        self.panel.pack1(self.output, True, False)
        self.panel.pack2(frame_input, False, False)

        self.panel_signal_id = self.panel.connect_after('expose-event',
                self.update_panel_position)

        self.hbox = gtk.HBox()
        if self.session.config.get_or_set('b_avatar_on_left', False):
            self.hbox.pack_start(self.info, False)
            self.hbox.pack_start(self.panel, True, True)
        else:
            self.hbox.pack_start(self.panel, True, True)
            self.hbox.pack_start(self.info, False)

        self.pack_start(self.header, False)
        self.pack_start(self.hbox, True, True)
        self.pack_start(self.transfers_bar, False)

        if len(self.members) == 0:
            self.header.information = ('connecting', 'creating conversation')

        last_avatar = self.session.config.last_avatar
        if self.session.config_dir.file_readable(last_avatar):
            my_picture = last_avatar
        else:
            my_picture = gui.theme.user

        his_picture = gui.theme.user
        if members:
            account = members[0]
            contact = self.session.contacts.get(account)

            if contact and contact.picture:
                his_picture = contact.picture

        self.info.first = self.his_avatar
        self.his_avatar.set_from_file(his_picture)

        self.info.last = self.avatar
        self.avatar.set_from_file(my_picture)

        self._load_style()

        self.session.config.subscribe(self._on_show_toolbar_changed,
            'b_show_toolbar')
        self.session.config.subscribe(self._on_show_header_changed,
            'b_show_header')
        self.session.config.subscribe(self._on_show_info_changed,
            'b_show_info')
        self.session.signals.picture_change_succeed.subscribe(
            self.on_picture_change_succeed)
        self.session.signals.contact_attr_changed.subscribe(
            self.on_contact_attr_changed_succeed)

        self.session.signals.filetransfer_invitation.subscribe(
                self.on_filetransfer_invitation)
        self.session.signals.filetransfer_accepted.subscribe(
                self.on_filetransfer_accepted)
        self.session.signals.filetransfer_progress.subscribe(
                self.on_filetransfer_progress)

        self.tab_index = -1 # used to select an existing conversation
        self.index = 0 # used for the rotate picture function
        self.rotate_started = False

        if self.group_chat:
            self.rotate_started = True #to prevents more than one timeout_add
            gobject.timeout_add_seconds(5, self.rotate_picture)

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
        #stop the avatars animation...if any..
        self.avatar.stop()
        self.his_avatar.stop()

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

    def update_panel_position(self, *args):
        """update the panel position to be on the 80% of the height
        """
        height = self.panel.get_allocation().height
        if height > 0:
            self.panel.set_position(int(height * 0.8))
            self.panel.disconnect(self.panel_signal_id)
            del self.panel_signal_id

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

        self.update_window(self.text, self.icon, self.tab_index)

    def update_group_information(self):
        """
        update the information for a conversation with multiple users
        """
        if not self.rotate_started:
            self.rotate_started = True
            gobject.timeout_add_seconds(5, self.rotate_picture)

        #TODO add plus support for nick to the tab label!
        members_nick = []
        i = 0
        for account in self.members:
            i += 1
            contact = self.session.contacts.get(account)

            if contact is None or contact.nick is None:
                nick = account
            elif len(contact.nick) > 20 and i != len(self.members):
                nick = contact.nick[:20] + '...'
            else:
                nick = contact.nick

            members_nick.append(nick)

        self.header.information = \
            ('%d members' % (len(self.members) + 1, ),
                    ", ".join(members_nick))
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

    def rotate_picture(self):
        '''change the account picture in a multichat
           conversation every 5 seconds'''
        def increment():
            if self.index < len(self.members) - 1 :
                self.index += 1
            else:
                self.index = 0

        contact = self.session.contacts.get(self.members[self.index])
        if contact is None:
            increment()
            return True

        path = contact.picture

        if path != '':
            self.his_avatar.set_from_file(path)

        increment()
        return True

    def _on_user_typing(self, cid, account, *args):
        """
        inform that the other user has started typing
        """
        pass

    def on_emote(self, emote):
        '''called when an emoticon is selected'''
        self.input.append(gobject.markup_escape_text(emote))
        self.input.grab_focus()

    def on_picture_change_succeed(self, account, path):
        '''callback called when the picture of an account is changed'''
        # our account?
        if account == self.session.account.account:
            self.avatar.set_from_file(path)
        elif account in self.members:
            self.his_avatar.set_from_file(path)

    def on_contact_attr_changed_succeed(self, account, what, old):
        self.update_tab()

    def on_filetransfer_invitation(self, transfer):
        self.transfers_bar.add(transfer)

    def on_filetransfer_accepted(self, transfer):
        pass

    def on_filetransfer_progress(self, transfer):
        self.transfers_bar.update(transfer)

    def on_filetransfer_rejected(self, transfer):
        self.transfers_bar.update(transfer)

