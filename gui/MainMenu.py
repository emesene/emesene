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
import protocol.base.stock as stock
import protocol.base.status as status

class MainMenu(Menu.Menu):
    '''a class that has all the fields of of the main menu'''

    def __init__(self, dialog, contacts, groups, contact_list):
        '''class contructor'''
        Menu.Menu.__init__(self)
        
        self.dialog = dialog
        self.contacts = contacts
        self.groups = groups
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
            self.append(self._build_view(logged_in))
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
                if stat != status.OFFLINE:
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

    def _build_view(self, logged_in):
        '''build and return the view menu'''
        self.view_menu = Menu.Menu(_('_View'))

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

        self.view_menu.append(self.order_option)
        self.view_menu.append(Menu.Item('-'))
        self.view_menu.append(self.show_by_nick_option)
        self.view_menu.append(self.show_offline_option)
        self.view_menu.append(self.show_empty_groups_option)

        return self.view_menu
        
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
        self.prefs_item = Menu.Item(_('_Preferences'), Menu.Item.TYPE_STOCK, 
            stock.PREFERENCES, Menu.Accel('P'))
        self.prefs_item.signal_connect('selected', self._on_preferences_selected)

        if logged_in:
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
        self.contacts.set_status(stat)

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
        self.groups.add_dialog()

    def _on_remove_group_selected(self, item):
        '''called when remove_group is selected'''
        group = self.contact_list.get_group_selected()

        def _yes_no_cb(response):
            '''callback from the confirmation dialog'''
            if response == stock.YES:
                self.groups.remove(group.name)

        if group:
            self.dialog.yes_no(
                _('Are you sure you want to remove group %s?') % \
                (group.name,), _yes_no_cb)
        else:
            self.dialog.error(_('No group selected'))

    def _on_rename_group_selected(self, item):
        '''called when rename_group is selected'''
        group = self.contact_list.get_group_selected()
        
        if group:
            self.groups.rename_dialog(group.name)
        else:
            self.dialog.error(_('No group selected'))

    def _on_add_contact_selected(self, item):
        '''called when add is selected'''
        self.contacts.add_dialog()

    def _on_remove_selected(self, item):
        '''called when remove is selected'''
        contact = self.contact_list.get_contact_selected()

        def _yes_no_cb(response):
            '''callback from the confirmation dialog'''
            if response == stock.YES:
                self.contacts.remove(contact.account)

        if contact:
            self.dialog.yes_no(
                _('Are you sure you want to remove contact %s?') % \
                (contact.account,), _yes_no_cb)
        else:
            self.dialog.error(_('No contact selected'))

    def _on_block_selected(self, item):
        '''called when block is selected'''
        contact = self.contact_list.get_contact_selected()
        
        if contact:
            self.contacts.block(contact.account)
        else:
            self.dialog.error(_('No contact selected'))

    def _on_unblock_selected(self, item):
        '''called when unblock is selected'''
        contact = self.contact_list.get_contact_selected()
        
        if contact:
            self.contacts.unblock(contact.account)
        else:
            self.dialog.error(_('No contact selected'))

    def _on_move_selected(self, item):
        '''called when move is selected'''
        pass

    def _on_set_alias_selected(self, item):
        '''called when set_alias is selected'''
        contact = self.contact_list.get_contact_selected()
        
        if contact:
            self.contacts.set_alias_dialog(contact.account)
        else:
            self.dialog.error(_('No contact selected'))

    def _on_set_nick_selected(self, item):
        '''called when set nick is selected'''
        self.contacts.set_nick_dialog()

    def _on_set_message_selected(self, item):
        '''called when set message is selected'''
        self.contacts.set_message_dialog(\
            self.contacts.me.message)

    def _on_set_picture_selected(self, item):
        '''called when set picture is selected'''
        self.contacts.set_picture_dialog()

