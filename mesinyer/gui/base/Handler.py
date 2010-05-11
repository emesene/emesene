import time
import webbrowser
import gtk

import e3.base
import gui
import extension

import logging
log = logging.getLogger('gui.base.Handler')

class MenuHandler(object):
    '''this handler contains all the handlers needed to handle all the
    menu items
    '''

    def __init__(self, session, dialog, contact_list, avatar_manager, on_disconnect=None,
            on_quit=None):
        '''constructor'''
        self.file_handler = FileHandler(session, on_disconnect, on_quit)
        self.actions_handler = ActionsHandler(session, dialog, contact_list, avatar_manager)
        self.options_handler = OptionsHandler(session, contact_list)
        self.help_handler = HelpHandler(dialog)

class FileHandler(object):
    '''this handler contains all the handlers needed to handle the file
    menu items
    '''

    def __init__(self, session, on_disconnect=None, on_quit=None):
        '''constructor'''
        self.session = session
        self.on_disconnect = on_disconnect
        self.on_quit = on_quit

    def on_status_selected(self, stat):
        '''called when a status is selected on the status menu'''
        self.session.set_status(stat)

    def on_disconnect_selected(self):
        '''called when a status is selected on the status menu'''
        if self.on_disconnect:
            self.on_disconnect()

    def on_quit_selected(self):
        '''called when a status is selected on the status menu'''
        if self.on_quit:
            self.on_quit()

class ActionsHandler(object):
    '''this handler contains all the handlers needed to handle the actions
    menu items
    '''

    def __init__(self, session, dialog, contact_list, avatar_manager):
        '''constructor'''
        self.contact_handler = ContactHandler(session, dialog, contact_list)
        self.group_handler = GroupHandler(session, dialog, contact_list)
        self.my_account_handler = MyAccountHandler(session, dialog, avatar_manager)

class OptionsHandler(object):
    '''this handler contains all the handlers needed to handle the options
    menu items
    '''

    def __init__(self, session, contact_list):
        '''constructor'''
        self.session = session
        self.contact_list = contact_list

    def on_order_by_group_toggled(self, active):
        '''called when the order by group radio button is toggled'''
        if active:
            self.contact_list.order_by_group = active

    def on_order_by_status_toggled(self, active):
        '''called when the order by status radio button is toggled'''
        if active:
            self.contact_list.order_by_status = active

    def on_show_offline_toggled(self, active):
        '''called when the show offline item is toggled'''
        self.contact_list.show_offline = active

    def on_group_offline_toggled(self, active):
        '''called when the show offline item is toggled'''
        self.contact_list.group_offline = active

    def on_show_empty_groups_toggled(self, active):
        '''called when the show empty groups item is toggled'''
        self.contact_list.show_empty_groups = active

    def on_show_blocked_toggled(self, active):
        '''called when the show blocked item is toggled'''
        self.contact_list.show_blocked = active

    def on_preferences_selected(self):
        '''called when the preference button is selected'''
        Preferences = extension.get_default('preferences')
        Preferences(self.session).show()

    def on_plugins_selected(self):
        '''called when the plugins button is selected'''
        Plugins = extension.get_default('plugin window')
        Plugins(self.session).show_all()


class HelpHandler(object):
    '''this handler contains all the handlers needed to handle the help
    menu items
    '''

    def __init__(self, dialog):
        '''constructor'''
        self.dialog = dialog

    def on_about_selected(self):
        '''called when the about item is selected'''
        self.dialog.about_dialog('emesene', '2.0', 'marianoguerra',
            'A simple yet powerful MSN & Gtalk client', 'GPL v3',
            'http://www.emesene.org', ['marianoguerra', 'boyska', 'C10uD','Cando'], '',
            gui.theme.logo)

    def on_website_selected(self):
        '''called when the website item is selected'''
        webbrowser.open("http://www.emesene.org")

    def on_debug_selected(self):
        '''called when the preference button is selected'''
        DebugWindow = extension.get_default('debug window')
        DebugWindow().show()


class ContactHandler(object):
    '''this handler contains all the handlers needed to handle the contact
    menu items
    '''

    def __init__(self, session, dialog, contact_list):
        '''constructor'''
        self.session = session
        self.dialog = dialog
        self.contact_list = contact_list

    def on_add_contact_selected(self):
        '''called when add contact is selected'''
        def add_cb(response, account, groups):
            '''callback to the add_dialog method, add the user and add him
            to the defined groups'''

            if response == gui.stock.ADD:
                self.session.add_contact(account)
                # TODO: this doesn't work
                if groups:
                    for group in groups:
                        self.session.add_to_group(account, group)

        self.dialog.add_contact(self.session.groups.values(), None, add_cb)

    def on_remove_contact_selected(self):
        '''called when remove contact is selected'''
        def remove_cb(response, account):
            '''callback for DialogManager.yes_no, asking to confirm the
            user remove'''

            if response == gui.stock.YES:
                self.session.remove_contact(account)

        contact = self.contact_list.get_contact_selected()

        if contact:
            self.dialog.yes_no(
                "Are you shure you want to delete %s?" % \
                (contact.account, ), remove_cb, contact.account)
        else:
            self.dialog.error('No contact selected')

    def on_block_contact_selected(self):
        '''called when block contact is selected'''
        contact = self.contact_list.get_contact_selected()

        if contact:
            self.session.block(contact.account)
        else:
            self.dialog.error('No contact selected')

    def on_unblock_contact_selected(self):
        '''called when unblock contact is selected'''
        contact = self.contact_list.get_contact_selected()

        if contact:
            self.session.unblock(contact.account)
        else:
            self.dialog.error('No contact selected')

    def on_set_alias_contact_selected(self):
        '''called when set alias contact is selected'''
        def set_alias_cb(response, account, old_alias, new_alias):
            '''callback for the set_alias method,
            the parameters and the values are described on that method'''

            if response == gui.stock.ACCEPT:
                if old_alias == new_alias:
                    log.debug('old alias and new alias are the same')
                    return

                self.session.set_alias(account, new_alias)
            elif response == gui.stock.CLEAR:
                self.session.set_alias(account, '')

        contact = self.contact_list.get_contact_selected()

        if contact:
            self.dialog.set_contact_alias(contact.account, contact.alias,
                 set_alias_cb)
        else:
            self.dialog.error('No contact selected')

    def on_view_information_selected(self):
        '''called when view information is selected'''
        contact = self.contact_list.get_contact_selected()

        if contact:
            self.dialog.contact_information_dialog(self.session,
                contact.account)
        else:
            self.dialog.error('No contact selected')

class GroupHandler(object):
    '''this handler contains all the handlers needed to handle the group
    menu items
    '''

    def __init__(self, session, dialog, contact_list):
        '''constructor'''
        self.session = session
        self.dialog = dialog
        self.contact_list = contact_list

    def on_add_group_selected(self):
        '''called when add group is selected'''
        def add_group_cb(response, group_name):
            '''callback for the add_group method'''

            if response == gui.stock.ACCEPT:
                if group_name:
                    self.session.add_group(group_name)

        self.dialog.add_group(add_group_cb)

    def on_remove_group_selected(self):
        '''called when remove group is selected'''
        def remove_group_cb(response, gid):
            '''callback for the yes_no method, asking for
            confirmation un group delete'''

            if response == gui.stock.YES:
                self.session.remove_group(gid)

        group = self.contact_list.get_group_selected()

        if group:
            self.dialog.yes_no(
                "Are you shure you want to delete the %s group?" % \
                (group.name, ), remove_group_cb, group.identifier)
        else:
            self.dialog.error('No group selected')

    def on_rename_group_selected(self):
        '''called when rename group is selected'''
        def rename_group_cb(response, group, new_name):
            '''callback called by rename_group'''

            if response == gui.stock.ACCEPT:
                if group.name == new_name:
                    log.debug("old and new name are the same")
                elif new_name:
                    self.session.rename_group(group.identifier, new_name)
                else:
                    log.debug("new name not valid")

        group = self.contact_list.get_group_selected()

        if group:
            self.dialog.rename_group(group, rename_group_cb)
        else:
            self.dialog.error('No group selected')

class MyAccountHandler(object):
    '''this handler contains all the handlers needed to handle the my account
    menu items
    '''

    def __init__(self, session, dialog, avatar_manager):
        '''constructor'''
        self.session = session
        self.dialog = dialog
        self.avatar_manager = avatar_manager

        self.old_nick = self.session.contacts.me.nick
        self.old_pm = self.session.contacts.me.message

    def set_nick_cb(self, old_nick=None, new_nick=None):
        '''callback for the set_nick method'''
        if old_nick == new_nick:
            log.debug('old nick and new nick are the same')
            return
        elif new_nick == '':
            log.debug('empty new nick')
            return
        self.session.set_nick(new_nick)

    def set_message_cb(self, old_pm=None, new_pm=None):
        '''callback for the set_message method'''
        if old_pm == new_pm:
            log.debug('old and new personal messages are the same')
            return

        self.session.set_message(new_pm)

    def save_profile(self, widget, data=None):
        '''save the new profile'''
        new_nick = self.nick.get_text()
        new_pm = self.pm.get_text()

        self.set_nick_cb(self.old_nick, new_nick)
        self.set_message_cb(self.old_pm, new_pm)

    def change_profile(self):
        self.windows = gtk.Window()
        self.windows.set_border_width(5)
        self.windows.set_title('Change profile')
        self.windows.set_position(gtk.WIN_POS_CENTER)
        self.windows.set_resizable(False)

        self.hbox = gtk.HBox(spacing=5)
        self.vbox = gtk.VBox()

        self.frame = gtk.Frame('Picture')

        self.avatar = gtk.Image()
        self.avatar.set_size_request(96, 96)
        self.frame.add(self.avatar)
        pixbuf = gtk.gdk.pixbuf_new_from_file(self.session.config.last_avatar)
        self.avatar.set_from_pixbuf(pixbuf)
        self.avatarEventBox = gtk.EventBox()
        self.avatarEventBox.add(self.frame)

        self.hbox.pack_start(self.avatarEventBox)
        self.hbox.pack_start(self.vbox)

        self.nick_label = gtk.Label('Nick:')
        self.nick_label.set_alignment(0.0,0.5)

        self.nick = gtk.Entry()
        self.nick.set_text(self.session.contacts.me.nick)

        self.pm_label = gtk.Label('PM:')
        self.pm_label.set_alignment(0.0,0.5)

        self.pm = gtk.Entry()
        self.pm.set_text(self.session.contacts.me.message)

        self.savebutt = gtk.Button('Save')

        self.savebutt.connect('clicked', self.save_profile)
        self.avatarEventBox.connect("button-press-event", self.on_set_picture_selected)

        self.vbox0 = gtk.VBox()

        self.vbox0.pack_start(self.nick_label)
        self.vbox0.pack_start(self.nick)
        self.vbox0.pack_start(self.pm_label)
        self.vbox0.pack_start(self.pm)

        self.vbox.pack_start(self.vbox0)
        self.vbox.pack_start(self.savebutt)

        self.windows.add(self.hbox)
        self.windows.show_all()

    def on_set_picture_selected(self, widget, data=None):
        '''called when set picture is selected'''
        def set_picture_cb(response, filename):
            '''callback for the avatar chooser'''
            if _av_chooser is not None:
                _av_chooser.stop_and_clear()
            if response == gui.stock.ACCEPT:
                self.avatar_manager.set_as_avatar(filename)

        # Directory for user's avatars
        path_dir = self.avatar_manager.get_avatars_dir()

        # Directory for contact's cached avatars
        cached_avatar_dir = self.avatar_manager.get_cached_avatars_dir()

        # Directories for System Avatars
        faces_paths = self.avatar_manager.get_system_avatars_dirs()

        self.avatar_path = self.session.config.last_avatar

        _av_chooser = extension.get_default('avatar chooser')(set_picture_cb,
                                                self.avatar_path, path_dir,
                                                cached_avatar_dir, faces_paths,
                                                self.avatar_manager)
        _av_chooser.show()

class ConversationToolbarHandler(object):
    '''this handler contains all the methods to handle a conversation toolbar
    '''

    def __init__(self, session, dialog, theme, conversation):
        '''constructor'''
        self.session = session
        self.dialog = dialog
        self.conversation = conversation
        self.theme = theme

    def on_font_selected(self):
        '''called when the Font button is selected'''
        self.dialog.select_font(self.conversation.cstyle,
            self.conversation.on_font_selected)

    def on_color_selected(self):
        '''called when the Color button is selected'''
        self.dialog.select_color(self.conversation.cstyle.color,
            self.conversation.on_color_selected)

    def on_style_selected(self):
        '''called when the Style button is selected'''
        self.dialog.select_style(self.conversation.cstyle,
            self.conversation.on_style_selected)

    def on_invite_selected(self):
        '''called when the Invite button is selected'''
        self.dialog.invite_dialog(self.session,
            self.conversation.on_invite)

    def on_clean_selected(self):
        '''called when the Clean button is selected'''
        self.conversation.on_clean()

    def on_emotes_selected(self):
        '''called when the emotes button is selected'''
        self.dialog.select_emote(self.theme, self.conversation.on_emote)

    def on_notify_atention_selected(self):
        '''called when the nudge button is selected'''
        self.conversation.on_notify_attention()

    def on_invite_file_trasnfer_selected(self):
        '''called when the client requestes to a remote user to
        start a file transfer'''
        raise NotImplementedError

class TrayIconHandler(FileHandler):
    """
    this handler contains all the methods to handle a tray icon
    """

    def __init__(self, session, theme, on_disconnect=None, on_quit=None):
        """
        constructor

        session -- a e3.Session implementation
        theme -- a gui.Theme object
        """
        FileHandler.__init__(self, session, on_disconnect, on_quit)
        self.theme = theme

class FileTransferHandler(object):
    ''' this handler handles a file transfer object '''
    def __init__(self, session, transfer):
        ''' session - e3.session implementation
            transfer - e3.transfer
        '''
        self.session = session
        self.transfer = transfer

    def open(self):
        ''' use desktop's open to open the file, once state is finished '''
        raise NotImplementedError

    def opendir(self):
        ''' open the directory that contains the file, once the transfer is finished '''
        raise NotImplementedError

    def accept(self):
        ''' accepts a file transfer '''
        self.transfer.time_start = time.time()
        self.transfer.state = e3.base.FileTransfer.TRANSFERRING
        self.session.accept_filetransfer(self.transfer)

    def reject(self):
        ''' cancels a file transfer '''
        self.transfer.state = e3.base.FileTransfer.FAILED
        self.session.reject_filetransfer(self.transfer)

    def cancel(self):
        ''' cancels a file transfer '''
        self.transfer.state = e3.base.FileTransfer.FAILED
        self.session.cancel_filetransfer(self.transfer)
