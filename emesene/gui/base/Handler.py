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

import os
import re
import time
import urllib

import e3.base
import gui
import extension
import Desktop
import Info

import logging
log = logging.getLogger('gui.base.Handler')

#TODO: Remove this someday in future because we still need it
#      for pre-2.12.4-dev versions searching for updates
EMESENE_VERSION = Info.EMESENE_VERSION
EMESENE_LAST_STABLE = Info.EMESENE_LAST_STABLE

class MenuHandler(object):
    '''this handler contains all the handlers needed to handle all the
    menu items
    '''

    def __init__(self, session, contact_list):
        '''constructor'''
        self.file_handler = FileHandler(session)
        self.actions_handler = ActionsHandler(session, contact_list)
        self.options_handler = OptionsHandler(session, contact_list)
        self.help_handler = HelpHandler()

class FileHandler(object):
    '''this handler contains all the handlers needed to handle the file
    menu items
    '''

    def __init__(self, session, on_quit=None):
        '''constructor'''
        self.session = session
        self.on_quit = on_quit

    def on_status_selected(self, stat):
        '''called when a status is selected on the status menu'''
        self.session.set_status(stat)

    def on_disconnect_selected(self):
        '''called when a status is selected on the status menu'''
        self.session.close()

    def on_quit_selected(self):
        '''called when a status is selected on the status menu'''
        if self.on_quit:
            self.on_quit()
        else:
            self.session.close(True)

    def on_disconnect_endpoint_selected(self, ep_id):
        self.session.disconnect_endpoint(ep_id)

class ActionsHandler(object):
    '''this handler contains all the handlers needed to handle the actions
    menu items
    '''

    def __init__(self, session, contact_list):
        '''constructor'''
        self.contact_handler = ContactHandler(session, contact_list)
        self.group_handler = GroupHandler(session, contact_list)
        self.my_account_handler = MyAccountHandler(session)

class OptionsHandler(object):
    '''this handler contains all the handlers needed to handle the options
    menu items
    '''

    def __init__(self, session, contact_list):
        '''constructor'''
        self.session = session
        self.contact_list = contact_list
        self.preferences = None

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

    def on_order_by_name_toggled(self, active):
        '''called when the sort by name item is toggled'''
        self.contact_list.order_by_name = active

    def on_preferences_selected(self):
        '''called when the preference button is selected'''
        self.preferences = extension.get_and_instantiate('preferences',
                                                         self.session)

        if self.session is not self.preferences.session:
            extension.delete_instance('preferences')
            self.preferences = extension.get_and_instantiate('preferences',
                                                             self.session)

        self.preferences.show()
        self.preferences.present()

class HelpHandler(object):
    '''this handler contains all the handlers needed to handle the help
    menu items
    '''

    def __init__(self):
        '''constructor'''
        self.dialog = extension.get_default('dialog')
        self.debug_window = None

    def on_about_selected(self):
        '''called when the about item is selected'''
        self.dialog.about_dialog('emesene', Info.EMESENE_VERSION, Info.EMESENE_AUTHORS,
            _('A simple yet powerful instant messaging client'), Info.EMESENE_LICENSE,
            Info.EMESENE_WEBSITE, Info.EMESENE_CONTRIBUTORS, _('translator-credits'),
            gui.theme.image_theme.logo)

    def on_website_selected(self):
        '''called when the website item is selected'''
        Desktop.open(Info.EMESENE_WEBSITE)

    def on_debug_selected(self):
        '''called when the preference button is selected'''
        def debug_close_cb():
            self.debug_window = None
        if not self.debug_window:
            DebugWindow = extension.get_default('debug window')
            self.debug_window = DebugWindow(debug_close_cb)
            self.debug_window.show()

    def notify_update(self, ver):
        self.dialog.information(_("New version available: %(ver)s\nVisit the "
                    "<a href=\"%(web)s\">emesene website</a> for the "
                    "latest informations about it.") % {"ver" : ver,
                    "web" : Info.EMESENE_WEBSITE})

    def on_check_update_selected(self):
        ''' checks if a new stable version of emesene is available '''
        f = urllib.urlopen("https://github.com/emesene/emesene/raw/master/emesene/Info.py")
        s = f.read()
        f.close()
        s = re.findall(r'EMESENE_LAST_STABLE = "(([^"\\]+|\\.)*)"', s)
        try:
            loc_ver = Info.EMESENE_VERSION.split(".")
            rem_ver = s[0][0].split(".") # [("version","version")]
            if len(rem_ver[2]) > 2:
                return # no RCs, BETAs or DEVELs
            if len(loc_ver[2]) > 2:
                self.dialog.information(_("You're running a development version of emesene.\n"
                                          "You might want to use the latest stable version (%s)\n"
                                          "unless you know what you're doing") % (s[0][0]))
                return
            if int(loc_ver[0]) == int(rem_ver[0]):
                if int(loc_ver[1]) < int(rem_ver[1]):
                    self.notify_update(s[0][0])
                    return
                elif int(loc_ver[1]) == int(rem_ver[1]):
                    if int(loc_ver[2]) < int(rem_ver[2]):
                        self.notify_update(s[0][0])
                        return
        except IndexError:
            pass # Silently fail

        self.dialog.information(_("No update available"))

class ContactHandler(object):
    '''this handler contains all the handlers needed to handle the contact
    menu items
    '''

    def __init__(self, session, contact_list):
        '''constructor'''
        self.session = session
        self.dialog = extension.get_default('dialog')
        self.contact_list = contact_list

    def get_contact_groups(self):
        contact = self.contact_list.get_contact_selected()
        if contact is not None:
            return contact.groups
        else:
            return []

    def get_all_groups(self):
        return self.session.groups

    def is_by_group_view(self):
        return self.contact_list.order_by_group

    def on_add_contact_selected(self):
        '''called when add contact is selected'''
        def add_cb(response, account=None, group=None):
            '''callback to the add_dialog method, add the user and add him
            to the defined group'''
            if response == gui.stock.ADD:
                if group:
                    for group_to_find,group_obj in self.session.groups.iteritems():
                        if(group_obj.name == group):
                            self.session.add_to_group(account, group_obj.identifier)
                else:
                    self.session.add_contact(account)

        group = self.contact_list.get_contact_selected_group()
        self.dialog.add_contact(self.session.groups.values(),
                                (group.name if group else None), add_cb)

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
                _("Are you sure you want to delete %s?") % \
                (contact.account, ), remove_cb, contact.account)
        else:
            self.dialog.error(_('No contact selected'))

    def on_block_contact_selected(self):
        '''called when block contact is selected'''
        def on_block_contact_accept(accept, account):
            if accept == gui.stock.YES:
                self.session.block(account)

        contact = self.contact_list.get_contact_selected()

        if contact:
            self.dialog.yes_no(_("Are you sure you want to block this contact?"),
                          on_block_contact_accept, contact.account)
        else:
            self.dialog.error(_('No contact selected'))

    def on_unblock_contact_selected(self):
        '''called when unblock contact is selected'''
        contact = self.contact_list.get_contact_selected()

        if contact:
            self.session.unblock(contact.account)
        else:
            self.dialog.error(_('No contact selected'))

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
            self.dialog.set_contact_alias(contact.account,
                    contact.alias if contact.alias != '' else contact.display_name, set_alias_cb)
        else:
            self.dialog.error(_('No contact selected'))

    def on_view_information_selected(self):
        '''called when view information is selected'''
        contact = self.contact_list.get_contact_selected()

        if contact:
            self.dialog.contact_information_dialog(self.session,
                contact.account)
        else:
            self.dialog.error(_('No contact selected'))

    def on_copy_to_group_selected(self, group):
        contact = self.contact_list.get_contact_selected()

        if contact:
            self.session.add_to_group(contact.account, group.identifier)
        else:
            self.dialog.error(_('No contact selected'))

    def on_move_to_group_selected(self, group_dst):
        contact = self.contact_list.get_contact_selected()
        group_src = self.contact_list.get_contact_selected_group()

        if contact and group_src and group_dst:
            self.session.move_to_group(contact.account,
                                    group_src.identifier, group_dst.identifier)
        else:
            self.dialog.error(_('No contact selected'))

    def on_remove_from_group_selected(self, group):
        contact = self.contact_list.get_contact_selected()

        if contact:
            self.session.remove_from_group(contact.account, group.identifier)
        else:
            self.dialog.error(_('No contact selected'))

class GroupHandler(object):
    '''this handler contains all the handlers needed to handle the group
    menu items
    '''

    def __init__(self, session, contact_list):
        '''constructor'''
        self.session = session
        self.dialog = extension.get_default('dialog')
        self.contact_list = contact_list

    def is_by_group_view(self):
        return self.contact_list.order_by_group

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
                _("Are you sure you want to delete the %s group?") % \
                (group.name, ), remove_group_cb, group.identifier)
        else:
            self.dialog.error(_('No group selected'))

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
            self.dialog.error(_('No group selected'))

    def on_favorite_group_selected(self):
        ''' called when set as favorite is selected '''
        group = self.contact_list.get_group_selected()

        if group:
            # reset old group's weight
            old_fav_group_id = self.session.config.favorite_group_id
            if old_fav_group_id is not None:
                self.session.config.d_weights[old_fav_group_id] = 0
            # increase new group's weight
            self.session.config.favorite_group_id = group.identifier
            self.session.config.d_weights[group.identifier] = 1
            self.contact_list.fill()
        else:
            self.dialog.error(_('No group selected'))

    def on_unset_favorite_group_selected(self):
        ''' called when unset as favorite is selected in a favorite group '''
        group = self.contact_list.get_group_selected()

        if group:
            # reset group weight
            self.session.config.d_weights[group.identifier] = 0
            self.session.config.favorite_group_id = None
            self.contact_list.fill()
        else:
            self.dialog.error(_('No group selected'))

class MyAccountHandler(object):
    '''this handler contains all the handlers needed to handle the my account
    menu items
    '''

    def __init__(self, session):
        '''constructor'''
        self.session = session

    def change_profile(self):
        '''show a dialog to edit the user account information'''
        last_avatar = self.session.config.last_avatar
        nick = self.session.contacts.me.nick
        message = self.session.contacts.me.message

        dialog = extension.get_default('dialog')
        dialog.edit_profile(self, nick, message, last_avatar)

    def save_profile(self, nick, pm):
        '''save the new profile'''
        self.session.set_nick(nick)
        self.session.set_message(pm)

    def on_set_picture_selected(self, widget, data=None):
        '''called when set picture is selected'''
        _av_chooser = extension.get_and_instantiate('avatar chooser', self.session)
        _av_chooser.show()

class ConversationToolbarHandler(object):
    '''this handler contains all the methods to handle a conversation toolbar
    '''

    def __init__(self, session, theme, conversation):
        '''constructor'''
        self.session = session
        self.dialog = extension.get_default('dialog')
        self.conversation = conversation
        self.theme = theme

    def session_service_supported(self, service):
        '''check if current session supports the service '''
        return self.session.session_has_service(service)

    def on_font_selected(self):
        '''called when the Font button is selected'''
        self.dialog.select_font(self.conversation.cstyle,
            self.conversation.on_font_selected)

    def on_color_selected(self):
        '''called when the Color button is selected'''
        self.dialog.select_color(self.conversation.cstyle.color,
            self.conversation.on_color_selected)

    def on_invite_selected(self):
        '''called when the Invite button is selected'''
        l_buddy_exclude = list(self.conversation.members)
        self.dialog.invite_dialog(self.session,
                                  self.conversation.on_invite, l_buddy_exclude)

    def on_clean_selected(self):
        '''called when the Clean button is selected'''
        self.conversation.on_clean()

    def on_emotes_selected(self):
        '''called when the emotes button is selected'''
        self.dialog.select_emote(self.session, \
                                 self.theme, self.conversation.on_emote)

    def on_notify_attention_selected(self):
        '''called when the nudge button is selected'''
        self.conversation.on_notify_attention()

    def on_invite_file_transfer_selected(self):
        '''called when the client requestes to a remote user to
        start a file transfer'''
        def open_file_cb(response, filepath):
            if response is not gui.stock.CANCEL and \
                response is not gui.stock.CLOSE:

                if filepath is None:
                    extension.get_default('dialog').error(
                                                _("No file selected"))
                else:
                    filename = os.path.basename(filepath)
                    self.conversation.on_filetransfer_invite(filename,
                                                             filepath)

        self.dialog.choose_file(os.path.expanduser("~"), open_file_cb)

    def on_ublock_selected(self):
        '''called when block/unblock button is selected'''
        self.conversation.on_block_user()

    def on_toggle_avatar_selected(self):
        '''hide or show the avatar bar'''
        self.conversation.on_toggle_avatar()

    def on_invite_video_call_selected(self):
        '''called when the user is requesting a video-only call'''
        self.conversation.on_video_call()

    def on_invite_voice_call_selected(self):
        '''called when the user is requesting an audio-only call'''
        self.conversation.on_voice_call()

    def on_invite_av_call_selected(self):
        '''called when the user is requesting an audio-video call'''
        self.conversation.on_av_call()

class OutputViewHandler(object):
    '''this handler contains all the methods to handle output view
    '''

    def __init__(self, conversation):
        '''constructor'''
        self.conversation = conversation

    def on_clean_selected(self):
        '''called when the Clear menu item is selected'''
        self.conversation.on_clean()

    def add_emoticon_selected(self, uri):
        '''called when an emoticon is being stolen'''
        self.conversation.steal_emoticon(uri)

class TrayIconHandler(FileHandler):
    """
    this handler contains all the methods to handle a tray icon
    """

    def __init__(self, session, theme, on_quit=None):
        """
        constructor

        session -- a e3.Session implementation
        theme -- a gui.Theme object
        """
        FileHandler.__init__(self, session, on_quit)
        self.theme = theme

    def on_hide_show_mainwindow(self, main_window=None):
        if main_window is not None:
            if main_window.get_visible():
                main_window.hide()
            else:
                main_window.present()

    def on_preferences_selected(self):
        '''called when the preference button is selected'''
        prefs = extension.get_and_instantiate('preferences', self.session)
        prefs.show()
        prefs.present()

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
        Desktop.open(self.transfer.completepath)

    def opendir(self):
        ''' open the directory that contains the file, once the transfer is finished '''
        Desktop.open(os.path.dirname(self.transfer.completepath))

    def accept(self):
        ''' accepts a file transfer '''
        self.transfer.time_start = time.time()
        self.transfer.state = e3.base.FileTransfer.TRANSFERRING
        self.session.accept_filetransfer(self.transfer)

    def accepted(self):
        ''' when a file transfer is accepted by the other party'''
        self.transfer.time_start = time.time()
        self.transfer.state = e3.base.FileTransfer.TRANSFERRING

    def reject(self):
        ''' rejects a file transfer '''
        self.transfer.state = e3.base.FileTransfer.FAILED
        self.session.reject_filetransfer(self.transfer)

    def cancel(self):
        ''' cancels a file transfer '''
        self.transfer.state = e3.base.FileTransfer.FAILED
        self.session.cancel_filetransfer(self.transfer)

class CallHandler(object):
    ''' this handler handles a file transfer object '''
    def __init__(self, session, call):
        ''' session - e3.session implementation
            transfer - e3.call
        '''
        self.session = session
        self.call = call

    def accept(self):
        ''' accepts a call '''
        if self.call.state != e3.base.Call.ESTABLISHED:
            self.call.state = e3.base.Call.ESTABLISHED
            self.session.accept_call(self.call)

    def accepted(self):
        ''' when a call is accepted by the other party'''
        self.call.state = e3.base.Call.ESTABLISHED

    def reject(self):
        ''' rejects a call '''
        self.call.state = e3.base.Call.FAILED
        self.session.reject_call(self.call)

    def cancel(self):
        ''' cancels a call '''
        self.call.state = e3.base.Call.FAILED
        self.session.cancel_call(self.call)
