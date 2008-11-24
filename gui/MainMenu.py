# -*- coding: utf-8 -*-

#   This file is part of emesene.
#
#    Emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
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
'''a module that define an abstract MainMenu'''
import gettext

_ = gettext.gettext

import gui
import Menu
import protocol.stock as stock
import protocol.status as status

class MainMenu(Menu.Menu):
    '''a class that has all the fields of of the main menu'''

    def __init__(self, dialog, account, contact_list):
        '''class contructor'''
        Menu.Menu.__init__(self)
        
        self.dialog = dialog
        self.account = account
        self.contact_list = contact_list

        self.signal_add('quit-selected', 0)
        self.signal_add('disconnect-selected', 0)
        self.signal_add('preferences-selected', 0)
        self.signal_add('plugins-selected', 0)
        self.signal_add('about-selected', 0)

        self._build(True)

    def _build(self, logged_in):
        '''clean and build the root menu'''
        for item in self:
            self.remove(item)

        self.append(self._build_file(logged_in))
        
        if logged_in:
            self.append(self._build_actions(logged_in))

        self.append(self._build_options(logged_in))
        self.append(self._build_help(logged_in))

    def _build_file(self, logged_in):
        '''build and return the file menu'''
        self.file_menu = Menu.Menu('_File')

        # file menu
        self.quit_item = Menu.Item(_('_Quit'), Menu.Item.TYPE_STOCK, 
            stock.QUIT, Menu.Accel('Q'))
        self.quit_item.signal_connect('selected', self._on_quit_selected)

        if logged_in:
            self.status_item = Menu.Menu(_('_Status'))
            for stat in status.ORDERED:
                temp_item = Menu.Item(status.STATUS[stat], 
                    Menu.Item.TYPE_IMAGE_PATH, 
                    gui.theme.status_icons[stat])
                temp_item.signal_connect('selected', 
                    self._on_status_selected, stat)
                self.status_item.append(temp_item)
        
            self.disconnect_item = Menu.Item(_('_Disconnect'), 
                Menu.Item.TYPE_STOCK, stock.DISCONNECT)
            self.disconnect_item.signal_connect('selected', 
                self._on_disconnect_selected)

            self.file_menu.append(self.status_item)
            self.file_menu.append(Menu.Item('-'))
            self.file_menu.append(self.disconnect_item)

        self.file_menu.append(self.quit_item)

        return self.file_menu

    def _build_actions(self, logged_in):
        '''build and return the actions menu'''
        self.actions_menu = Menu.Menu(_('_Actions'))
        self.contact_actions_menu = Menu.Menu(_('_Contact'))
        self.group_actions_menu = Menu.Menu('_Group')

        # group actions
        self.add_group_item = Menu.Item(_('_Add'), Menu.Item.TYPE_STOCK, 
            stock.ADD)
        self.add_group_item.signal_connect('selected', 
            self._on_add_group_selected)
        
        self.remove_group_item = Menu.Item(_('_Remove'), Menu.Item.TYPE_STOCK, 
            stock.REMOVE)
        self.remove_group_item.signal_connect('selected', 
            self._on_remove_group_selected)
        
        self.rename_group_item = Menu.Item(_('Re_name'), Menu.Item.TYPE_STOCK, 
            stock.EDIT)
        self.rename_group_item.signal_connect('selected', 
            self._on_rename_group_selected)
        
        # contact actions
        self.add_contact_item = Menu.Item(_('_Add'), Menu.Item.TYPE_STOCK, 
            stock.ADD)
        self.add_contact_item.signal_connect('selected', 
            self._on_add_contact_selected)
        
        self.remove_item = Menu.Item(_('_Remove'), Menu.Item.TYPE_STOCK, 
            stock.REMOVE)
        self.remove_item.signal_connect('selected', self._on_remove_selected)
        
        self.block_item = Menu.Item(_('_Block'), Menu.Item.TYPE_STOCK, 
            stock.STOP)
        self.block_item.signal_connect('selected', self._on_block_selected)
        
        self.unblock_item = Menu.Item(_('_Unblock'), Menu.Item.TYPE_STOCK, 
            stock.APPLY)
        self.unblock_item.signal_connect('selected', self._on_unblock_selected)
        
        self.move_item = Menu.Item(_('_Move'), Menu.Item.TYPE_STOCK, 
            stock.FORWARD)
        self.move_item.signal_connect('selected', self._on_move_selected)
        
        self.set_alias_item = Menu.Item(_('Set _alias'), Menu.Item.TYPE_STOCK, 
            stock.EDIT)
        self.set_alias_item.signal_connect('selected', 
            self._on_set_alias_selected)

        # account actions
        self.set_nick_item = Menu.Item(_('Set _nick'), Menu.Item.TYPE_STOCK, 
            stock.EDIT)
        self.set_nick_item.signal_connect('selected', 
            self._on_set_nick_selected)
        
        self.set_message_item = Menu.Item(_('Set _message'), 
            Menu.Item.TYPE_STOCK, stock.EDIT)
        self.set_message_item.signal_connect('selected', 
            self._on_set_message_selected)
        
        self.set_picture_item = Menu.Item(_('Set _picture'), 
            Menu.Item.TYPE_STOCK, stock.EDIT)
        self.set_picture_item.signal_connect('selected', 
            self._on_set_picture_selected)
        
        self.contact_actions_menu.append(self.add_contact_item)
        self.contact_actions_menu.append(self.remove_item)
        self.contact_actions_menu.append(self.block_item)
        self.contact_actions_menu.append(self.unblock_item)
        self.contact_actions_menu.append(self.set_alias_item)
        self.contact_actions_menu.append(self.move_item)

        self.group_actions_menu.append(self.add_group_item)
        self.group_actions_menu.append(self.remove_group_item)
        self.group_actions_menu.append(self.rename_group_item)

        self.actions_menu.append(self.contact_actions_menu)
        self.actions_menu.append(self.group_actions_menu)
        self.actions_menu.append(self.set_nick_item)
        self.actions_menu.append(self.set_message_item)
        self.actions_menu.append(self.set_picture_item)

        return self.actions_menu
        
    def _build_options(self, logged_in):
        '''build and return the option menu'''
        self.option_menu = Menu.Menu(_('_Options'))

        if self.contact_list.order_by_group:
            index = 1
        else:
            index = 0

        self.order_option = Menu.Option(index)
        self.by_status_option = Menu.Radio(_('Order by _status'))
        self.by_status_option.signal_connect('toggled', 
            self._on_by_status_toggled)
        self.by_group_option = Menu.Radio(_('Order by _group'))
        self.by_group_option.signal_connect('toggled', 
            self._on_by_group_toggled)

        self.order_option.append(self.by_status_option)
        self.order_option.append(self.by_group_option)

        self.show_by_nick_option = Menu.CheckBox(_('Show by _nick'),
            self.contact_list.show_nick)
        self.show_by_nick_option.signal_connect('toggled', 
            self._on_by_nick_toggled)

        self.show_offline_option = Menu.CheckBox(_('Show _offline'),
            self.contact_list.show_offline)
        self.show_offline_option.signal_connect('toggled', 
            self._on_show_offline_toggled)

        self.show_empty_groups_option = Menu.CheckBox(_('Show _empty groups'),
            self.contact_list.show_empty_groups)
        self.show_empty_groups_option.signal_connect('toggled', 
            self._on_empty_groups_toggled)

        self.prefs_item = Menu.Item(_('_Preferences'), Menu.Item.TYPE_STOCK, 
            stock.PREFERENCES, Menu.Accel('P'))
        self.prefs_item.signal_connect('selected', self._on_preferences_selected)

        if logged_in:
            self.option_menu.append(self.order_option)
            self.option_menu.append(Menu.Item('-'))
            self.option_menu.append(self.show_by_nick_option)
            self.option_menu.append(self.show_offline_option)
            self.option_menu.append(self.show_empty_groups_option)
            self.option_menu.append(Menu.Item('-'))

            self.plugins_item = Menu.Item(_('Plug_ins'), Menu.Item.TYPE_STOCK, 
                stock.DISCONNECT)
            self.plugins_item.signal_connect('selected', 
                self._on_plugins_selected)
            self.option_menu.append(self.plugins_item)
        
        self.option_menu.append(self.prefs_item)

        return self.option_menu
        
    def _build_help(self, logged_in):
        '''build and return the help menu'''
        self.help_menu = Menu.Menu(_('_Help'))
        self.about_item = Menu.Item(_('_About'), Menu.Item.TYPE_STOCK, 
            stock.ABOUT)
        self.about_item.signal_connect('selected', self._on_about_selected)

        self.help_menu.append(self.about_item)

        return self.help_menu

    # callbacks

    def _on_quit_selected(self, item):
        '''called when quit is selected'''
        self.signal_emit('quit-selected')

    def _on_disconnect_selected(self, item):
        '''called when disconnect is selected'''
        self.signal_emit('disconnect-selected')

    def _on_status_selected(self, item, stat):
        '''called when a status is selected'''
        self.account.set_status(stat)

    def _on_by_status_toggled(self, option, value):
        '''called when order by status is toggled'''
        if value:
            self.contact_list.order_by_status = value
            self.contact_list.fill()
    
    def _on_by_group_toggled(self, option, value):
        '''called when order by group is toggled'''
        if value:
            self.contact_list.order_by_group = value
            self.contact_list.fill()

    def _on_by_nick_toggled(self, check, value):
        '''called when show by nick is toggled'''
        self.contact_list.show_by_nick = value
    
    def _on_show_offline_toggled(self, check, value):
        '''called when show offline is toggled'''
        self.contact_list.show_offline = value
    
    def _on_empty_groups_toggled(self, check, value):
        '''called when show empty groups is toggled'''
        self.contact_list.show_empty_groups = value
    
    def _on_preferences_selected(self, item):
        '''called when preferences is selected'''
        self.signal_emit('preferences-selected')

    def _on_plugins_selected(self, item):
        '''called when plugins is selected'''
        self.signal_emit('plugins-selected')

    def _on_about_selected(self, item):
        '''called when about is selected'''
        self.signal_emit('about-selected')

    def _on_add_group_selected(self, item):
        '''called when add_group is selected'''
        self.add_group_dialog()

    def _on_remove_group_selected(self, item):
        '''called when remove_group is selected'''
        group = self.contact_list.get_group_selected()

        if group:
            self.remove_group_dialog(group.identifier, group.name)
        else:
            self.dialog.error(_('No group selected'))

    def _on_rename_group_selected(self, item):
        '''called when rename_group is selected'''
        group = self.contact_list.get_group_selected()
        
        if group:
            self.rename_group_dialog(group)
        else:
            self.dialog.error(_('No group selected'))

    def _on_add_contact_selected(self, item):
        '''called when add is selected'''
        self.add_dialog()

    def _on_remove_selected(self, item):
        '''called when remove is selected'''
        contact = self.contact_list.get_contact_selected()

        if contact:
            self.remove_dialog(contact.account)
        else:
            self.dialog.error(_('No contact selected'))

    def _on_block_selected(self, item):
        '''called when block is selected'''
        contact = self.contact_list.get_contact_selected()
        
        if contact:
            self.account.block(contact.account)
        else:
            self.dialog.error(_('No contact selected'))

    def _on_unblock_selected(self, item):
        '''called when unblock is selected'''
        contact = self.contact_list.get_contact_selected()
        
        if contact:
            self.account.unblock(contact.account)
        else:
            self.dialog.error(_('No contact selected'))

    def _on_move_selected(self, item):
        '''called when move is selected'''
        pass

    def _on_set_alias_selected(self, item):
        '''called when set_alias is selected'''
        contact = self.contact_list.get_contact_selected()
        
        if contact:
            self.set_alias_dialog(contact.account)
        else:
            self.dialog.error(_('No contact selected'))

    def _on_set_nick_selected(self, item):
        '''called when set nick is selected'''
        self.set_nick_dialog(self.account.nick)

    def _on_set_message_selected(self, item):
        '''called when set message is selected'''
        self.set_personal_message_dialog(self.account.message)

    def _on_set_picture_selected(self, item):
        '''called when set picture is selected'''
        self.set_picture_dialog()
    
    # dialog

    def set_nick_dialog(self, old_nick):
        '''show a dialog asking to change the nick'''
        self.dialog.set_nick(old_nick, self.set_nick_cb)

    def set_personal_message_dialog(self, old_personal_message):
        '''show a dialog asking to change the personal message'''
        self.dialog.set_message(old_personal_message, 
            self.set_personal_message_cb)

    def set_alias_dialog(self, account, old_alias):
        '''show the alias dialog'''
        self.dialog.set_contact_alias(account, old_alias, self.set_alias_cb)

    def remove_dialog(self, account):
        '''show a confirmation dialog to ask if sure to remove the
        user, it's optional to use, but recomended'''
        self.dialog.yes_no(
            _("Are you sure you want to delete %s?") % (account, ),
            self.remove_cb, account)
    
    def add_dialog(self):
        '''show a dialog to ask for the account, and if the account
        is valid, add the user'''
        self.dialog.add_contact(self.add_cb)

    # callbacks

    def set_nick_cb(self, response, old_nick, new_nick):
        '''callback for the DialogManager.set_nick method'''

        if response == stock.ACCEPT:
            if old_nick == new_nick:
                debug('old nick and new nick are the same')
                return
            elif new_nick == '':
                debug('empty new nick')
                return

            self.account.set_nick(new_nick)

    def set_personal_message_cb(self, response, old_pm, new_pm):
        '''callback for the DialogManager.set_personal_message method'''

        if response == stock.ACCEPT:
            if old_pm == new_pm:
                debug('old and new personal messages are the same')
                return

            self.account.set_personal_message(new_pm)

    def set_alias_cb(self, response, account, old_alias, new_alias):
        '''callback for the DialogManager.set_contact_alias method,
        the parameters and the values are described on that method'''

        if response == stock.ACCEPT:
            if old_alias == new_alias:
                debug('old alias and new alias are the same')
                return

            self.account.set_alias(account, new_alias)
        elif response == stock.CLEAR:
            self.account.set_alias(account, '')

    def remove_cb(self, response, account):
        '''callback for DialogManager.yes_no, asking to confirm the 
        user remove'''

        if response == stock.YES:
            self.account.remove(account)

    def add_cb(self, response, account, groups):
        '''callback to the add_dialog method, add the user and add him 
        to the defined groups'''

        if response == stock.ADD:
            self.account.add(account)
            # TODO: this doesn't work
            if groups:
                for group in groups:
                    self.account.add_to_group(account, group)
    # group dialogs

    def add_group_dialog(self):
        '''show a dialog to add a group'''
        self.dialog.add_group(self.add_group_cb)

    def rename_group_dialog(self, group):
        '''show a dialog showing the actual name of a group
        and asking for the new one'''
        self.dialog.rename_group(group, self.rename_group_cb)

    def remove_group_dialog(self, gid, name):
        '''ask for confirmation on group deletion, it can be used the method
        directly, but it's good to ask :P'''
        self.dialog.yes_no(_(
            _("Are you shure you want to delete the %s group?") % (name, )),
            self.remove_group_cb, gid)

    # callbacks

    def add_group_cb(self, response, group_name):
        '''callback for the DialogManager.add_group method'''

        if response == stock.ACCEPT:
            if group_name:
                self.account.add_group(group_name)

    def rename_group_cb(self, response, group, new_name):
        '''callback called by DialogManager.rename_group'''

        if response == stock.ACCEPT:
            if group.name == new_name:
                debug("old and new name are the same")
            elif new_name:
                self.account.rename_group(group.identifier, new_name)
            else:
                debug("new name not valid")

    def remove_group_cb(self, response, gid):
        '''callback for the DialogManager.yes_no method, asking for
        confirmation un group delete'''

        if response == stock.YES:
            self.account.remove_group(gid)

def debug(msg):
    '''debug method, the module send the debug here, it can be changed
    to use another debugging method'''

    print 'MainMenu.py:', msg
