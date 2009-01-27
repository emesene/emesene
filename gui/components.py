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
import gui
import gui.stock as stock
import protocol.status

# set this with your implementation!
Menu = None

def build_main_menu(handler=None, config=None):
    '''build the main menu'''
    root = Menu.MenuItem()

    if handler:
        file_handler = handler.file_handler
        actions_handler = handler.actions_handler
        options_handler = handler.options_handler
        help_handler = handler.help_handler
    else:
        file_handler = None
        actions_handler = None
        options_handler = None
        help_handler = None

    file = _build_file_menu(file_handler)
    actions = _build_actions_menu(actions_handler)
    options = _build_options_menu(options_handler, config)
    help = _build_help_menu(help_handler)

    root.add_child(file)
    root.add_child(actions)
    root.add_child(options)
    root.add_child(help)

    main_menu = root
    return root

def _build_file_menu(file_handler=None):
    '''build the  menu'''
    file_mi = Menu.MenuItem('_File', None, Menu.Accel('f', False, True))


    disconnect = Menu.MenuItem('_Disconnect',
        Menu.Image(stock.DISCONNECT, Menu.Image.TYPE_STOCK))
    quit_mi = Menu.MenuItem('_Quit',
        Menu.Image(stock.QUIT, Menu.Image.TYPE_STOCK))

    if file_handler:
        on_status_selected = file_handler.on_status_selected
        disconnect.selected.suscribe(file_handler.on_disconnect_selected)
        quit_mi.selected.suscribe(file_handler.on_quit_selected)
    else:
        on_status_selected = None

    status = build_status_menu(on_status_selected)

    file_mi.add_child(status)
    file_mi.add_child(Menu.MenuItem('-'))
    file_mi.add_child(disconnect)
    file_mi.add_child(quit_mi)

    return file_mi

def _build_actions_menu(actions_handler=None):
    '''build the  menu'''
    actions_mi = Menu.MenuItem('_Actions', None,
        Menu.Accel('a', False, True))

    if actions_handler:
        contact_handler = actions_handler.contact_handler
        group_handler = actions_handler.group_handler
        my_account_handler = actions_handler.my_account_handler
    else:
        contact_handler = None
        group_handler = None
        my_account_handler = None

    contact = _build_contact_menu(contact_handler)
    group = _build_group_menu(group_handler)
    my_account = _build_my_account_menu(my_account_handler)

    actions_mi.add_child(contact)
    actions_mi.add_child(group)
    actions_mi.add_child(my_account)

    return actions_mi

def _build_options_menu(options_menu=None, config=None):
    '''build the  menu'''
    options_mi = Menu.MenuItem('_Options', None,
        Menu.Accel('o', False, True))

    order_option = Menu.OptionGroup()
    order_by_status = Menu.MenuOption('Order by status')
    order_by_group = Menu.MenuOption('Order by group')

    order_option.add_child(order_by_status)
    order_option.add_child(order_by_group)

    show_offline = Menu.MenuOption('Show _offline contacts')
    show_empty_groups = Menu.MenuOption('Show _empty groups')
    show_blocked = Menu.MenuOption('Show _blocked contacts')

    preferences = Menu.MenuItem('_Preferences',
        Menu.Image(stock.PREFERENCES, Menu.Image.TYPE_STOCK))
    plugins = Menu.MenuItem('Plug_ins',
        Menu.Image(stock.CONNECT, Menu.Image.TYPE_STOCK))

    if options_menu:
        order_by_group.toggled.suscribe(
            options_menu.on_order_by_group_toggled)
        order_by_status.toggled.suscribe(
            options_menu.on_order_by_status_toggled)
        show_offline.toggled.suscribe(options_menu.on_show_offline_toggled)
        show_empty_groups.toggled.suscribe(
            options_menu.on_show_empty_groups_toggled)
        show_blocked.toggled.suscribe(options_menu.on_show_blocked_toggled)

    options_mi.add_child(order_option)
    options_mi.add_child(Menu.MenuItem('-'))
    options_mi.add_child(show_offline)
    options_mi.add_child(show_empty_groups)
    options_mi.add_child(show_blocked)
    options_mi.add_child(Menu.MenuItem('-'))
    options_mi.add_child(preferences)
    options_mi.add_child(plugins)

    if config is None:
        return options_mi

    if config.b_order_by_group is None:
        config.b_order_by_group = True

    if config.b_show_nick is None:
        config.b_show_nick = True

    if config.b_show_empty_groups is None:
        config.b_show_empty_groups = False

    if config.b_show_offline is None:
        config.b_show_offline = False

    if config.b_show_blocked is None:
        config.b_show_blocked = False

    order_by_status.active = not config.b_order_by_group
    order_by_group.active = config.b_order_by_group

    show_offline.active = config.b_show_offline
    show_empty_groups.active = config.b_show_empty_groups
    show_blocked.active = config.b_show_blocked
     

    return options_mi

def _build_help_menu(help_handler=None):
    '''build the  menu'''
    help_mi = Menu.MenuItem('_Help', None, Menu.Accel('h', False, True))

    site = Menu.MenuItem('_Website', Menu.Image(gui.theme.connect))
    about = Menu.MenuItem('_About',
        Menu.Image(stock.ABOUT, Menu.Image.TYPE_STOCK))

    if help_handler:
        site.selected.suscribe(help_handler.on_website_selected)
        about.selected.suscribe(help_handler.on_about_selected)

    help_mi.add_child(site)
    help_mi.add_child(Menu.MenuItem('-'))
    help_mi.add_child(about)

    return help_mi

def build_status_menu(on_status_change=None):
    '''build the  menu'''

    status = Menu.MenuItem('_Status')

    for stat in protocol.status.ORDERED:
        temp_item = Menu.MenuItem(protocol.status.STATUS[stat],
            Menu.Image(gui.theme.status_icons[stat]))

        if on_status_change:
            temp_item.selected.suscribe(on_status_change, stat)

        status.add_child(temp_item)

    return status

def _build_contact_menu(contact_handler=None):
    '''build the  menu'''
    contact_mi = Menu.MenuItem('_Contact')

    add_contact_mi = Menu.MenuItem('_Add',
        Menu.Image(stock.ADD, Menu.Image.TYPE_STOCK))
    remove_contact_mi = Menu.MenuItem('_Remove',
        Menu.Image(stock.REMOVE, Menu.Image.TYPE_STOCK))
    block_contact_mi = Menu.MenuItem('_Block',
        Menu.Image(stock.STOP, Menu.Image.TYPE_STOCK))
    unblock_contact_mi = Menu.MenuItem('_Unblock',
        Menu.Image(stock.APPLY, Menu.Image.TYPE_STOCK))
    set_alias_contact_mi = Menu.MenuItem('_Set alias',
        Menu.Image(stock.EDIT, Menu.Image.TYPE_STOCK))

    if contact_handler:
        add_contact_mi.selected.suscribe(
            contact_handler.on_add_contact_selected)
        remove_contact_mi.selected.suscribe(
            contact_handler.on_remove_contact_selected)
        block_contact_mi.selected.suscribe(
            contact_handler.on_block_contact_selected)
        unblock_contact_mi.selected.suscribe(
            contact_handler.on_unblock_contact_selected)
        set_alias_contact_mi.selected.suscribe(
            contact_handler.on_set_alias_contact_selected)

    contact_mi.add_child(add_contact_mi)
    contact_mi.add_child(remove_contact_mi)
    contact_mi.add_child(block_contact_mi)
    contact_mi.add_child(unblock_contact_mi)
    contact_mi.add_child(set_alias_contact_mi)

    return contact_mi

def _build_group_menu(group_handler=None):
    '''build the  menu'''
    group_mi = Menu.MenuItem('_Group')

    add_group_mi = Menu.MenuItem('_Add',
        Menu.Image(stock.ADD, Menu.Image.TYPE_STOCK))
    remove_group_mi = Menu.MenuItem('_Remove',
        Menu.Image(stock.REMOVE, Menu.Image.TYPE_STOCK))
    rename_group_mi = Menu.MenuItem('Re_name',
        Menu.Image(stock.EDIT, Menu.Image.TYPE_STOCK))

    if group_handler:
        add_group_mi.selected.suscribe(
            group_handler.on_add_group_selected)
        remove_group_mi.selected.suscribe(
            group_handler.on_remove_group_selected)
        rename_group_mi.selected.suscribe(
            group_handler.on_rename_group_selected)

    group_mi.add_child(add_group_mi)
    group_mi.add_child(remove_group_mi)
    group_mi.add_child(rename_group_mi)

    return group_mi

def _build_my_account_menu(my_account_handler=None):
    '''build the  menu'''
    my_account_mi = Menu.MenuItem('_My account')

    set_nick_contact_mi = Menu.MenuItem('Set _nick',
        Menu.Image(stock.EDIT, Menu.Image.TYPE_STOCK))
    set_message_contact_mi = Menu.MenuItem('Set _message',
        Menu.Image(stock.EDIT, Menu.Image.TYPE_STOCK))
    set_picture_contact_mi = Menu.MenuItem('Set _picture',
        Menu.Image(stock.EDIT, Menu.Image.TYPE_STOCK))

    if my_account_handler:
        set_nick_contact_mi.selected.suscribe(
            my_account_handler.on_set_nick_selected)
        set_message_contact_mi.selected.suscribe(
            my_account_handler.on_set_message_selected)
        set_picture_contact_mi.selected.suscribe(
            my_account_handler.on_set_picture_selected)

    my_account_mi.add_child(set_nick_contact_mi)
    my_account_mi.add_child(set_message_contact_mi)
    my_account_mi.add_child(set_picture_contact_mi)

    return my_account_mi

def build_conversation_toolbar(config):
    '''build the  menu'''
    toolbar = Menu.MenuItem()

    font_mi = Menu.MenuItem('Font',
        Menu.Image(stock.SELECT_FONT, Menu.Image.TYPE_STOCK))
    color_mi = Menu.MenuItem('Color',
        Menu.Image(stock.SELECT_COLOR, Menu.Image.TYPE_STOCK))
    style_mi = Menu.MenuItem('Style',
        Menu.Image(stock.BOLD, Menu.Image.TYPE_STOCK))

    emotes_mi = Menu.MenuItem('Emoticons',
        Menu.Image(gui.theme.emote_to_path(':)', True)))
    nudge_mi = Menu.MenuItem('Nudge',
        Menu.Image(gui.theme.emote_to_path(':S', True)))

    invite_mi = Menu.MenuItem('Invite',
        Menu.Image(stock.ADD, Menu.Image.TYPE_STOCK))
    clean_mi = Menu.MenuItem('Clean',
        Menu.Image(stock.CLEAR, Menu.Image.TYPE_STOCK))

    toolbar.add_child(font_mi)
    toolbar.add_child(color_mi)
    toolbar.add_child(style_mi)
    toolbar.add_child(Menu.MenuItem('-'))
    toolbar.add_child(emotes_mi)
    toolbar.add_child(nudge_mi)
    toolbar.add_child(Menu.MenuItem('-'))
    toolbar.add_child(invite_mi)
    toolbar.add_child(clean_mi)

    return toolbar

def _build_conversation_menu():
    '''build the  menu'''
    pass

