import webbrowser

import gui
import extension

from debugger import dbg

class MenuHandler(object):
    '''this handler contains all the handlers needed to handle all the
    menu items
    '''

    def __init__(self, session, dialog, contact_list, on_disconnect=None,
            on_quit=None):
        '''constructor'''
        self.file_handler = FileHandler(session, on_disconnect, on_quit)
        self.actions_handler = ActionsHandler(session, dialog, contact_list)
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

    def __init__(self, session, dialog, contact_list):
        '''constructor'''
        self.contact_handler = ContactHandler(session, dialog, contact_list)
        self.group_handler = GroupHandler(session, dialog, contact_list)
        self.my_account_handler = MyAccountHandler(session, dialog)

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
            self.contact_list.fill()

    def on_order_by_status_toggled(self, active):
        '''called when the order by status radio button is toggled'''
        if active:
            self.contact_list.order_by_status = active
            self.contact_list.fill()

    def on_show_offline_toggled(self, active):
        '''called when the show offline item is toggled'''
        self.contact_list.show_offline = active

    def on_show_empty_groups_toggled(self, active):
        '''called when the show empty groups item is toggled'''
        self.contact_list.show_empty_groups = active

    def on_show_blocked_toggled(self, active):
        '''called when the show blocked item is toggled'''
        self.contact_list.show_blocked = active

    def on_preferences_selected(self):
        '''called when the preference button is selected'''
        Preferences = extension.get_default('gtk preferences')
        Preferences(self.session).show()


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
            'http://www.emesene.org', ['marianoguerra'], '',
            gui.theme.logo)

    def on_website_selected(self):
        '''called when the website item is selected'''
        webbrowser.open("http://www.emesene.org")


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
                    dbg('old alias and new alias are the same', 'handler', 1)
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
                    dbg("old and new name are the same", 'handler', 1)
                elif new_name:
                    self.session.rename_group(group.identifier, new_name)
                else:
                    dbg("new name not valid", 'handler', 1)

        group = self.contact_list.get_group_selected()

        if group:
            self.dialog.rename_group(group, rename_group_cb)
        else:
            self.dialog.error('No group selected')

class MyAccountHandler(object):
    '''this handler contains all the handlers needed to handle the my account
    menu items
    '''

    def __init__(self, session, dialog):
        '''constructor'''
        self.session = session
        self.dialog = dialog

    def on_set_nick_selected(self):
        '''called when set nick is selected'''
        def set_nick_cb(response, old_nick, new_nick):
            '''callback for the set_nick method'''

            if response == gui.stock.ACCEPT:
                if old_nick == new_nick:
                    dbg('old nick and new nick are the same', 'handler', 1)
                    return
                elif new_nick == '':
                    dbg('empty new nick', 'handler', 1)
                    return

                self.session.set_nick(new_nick)

        self.dialog.set_nick(self.session.contacts.me.nick, set_nick_cb)

    def on_set_message_selected(self):
        '''called when set message is selected'''
        def set_message_cb(response, old_pm, new_pm):
            '''callback for the set_message method'''

            if response == gui.stock.ACCEPT:
                if old_pm == new_pm:
                    dbg('old and new personal messages are the same',
                        'handler', 1)
                    return

                self.session.set_message(new_pm)

        self.dialog.set_message(self.session.contacts.me.message,
            set_message_cb)

    def on_set_picture_selected(self):
        '''called when set picture is selected'''
        pass

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
        self.conversation.on_notify_atention()

class TrayIconHandler(FileHandler):
    """
    this handler contains all the methods to handle a tray icon
    """

    def __init__(self, session, theme, on_disconnect=None, on_quit=None):
        """
        constructor

        session -- a protocol.Session implementation
        theme -- a gui.Theme object
        """
        FileHandler.__init__(self, session, on_disconnect, on_quit)
        self.theme = theme
