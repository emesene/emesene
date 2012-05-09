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

import gtk
import e3
import gui
from gui.gtkui import check_gtk3
import utils
import sys

import extension

class MainMenu(gtk.MenuBar):
    """
    A widget that represents the main menu of the main window
    """
    NAME = 'Main Menu'
    DESCRIPTION = 'The Main Menu of the main window'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, handlers, session):
        """
        constructor

        handlers is a e3common.Handler.MenuHandler
        """
        gtk.MenuBar.__init__(self)

        self.handlers = handlers

        FileMenu = extension.get_default('menu file')
        ActionsMenu = extension.get_default('menu actions')
        OptionsMenu = extension.get_default('menu options')
        HelpMenu = extension.get_default('menu help')

        self.file = gtk.MenuItem(_('_File'))
        self.file_menu = FileMenu(self.handlers.file_handler, session)
        self.file.set_submenu(self.file_menu)

        self.actions = gtk.MenuItem(_('_Actions'))
        self.actions_menu = ActionsMenu(self.handlers.actions_handler, session)
        self.actions.set_submenu(self.actions_menu)

        self.options = gtk.MenuItem(_('_Options'))
        self.options_menu = OptionsMenu(self.handlers.options_handler, session.config)
        self.options.set_submenu(self.options_menu)

        self.help = gtk.MenuItem(_('_Help'))
        self.help_menu = HelpMenu(self.handlers.help_handler)
        self.help.set_submenu(self.help_menu)

        self.append(self.file)
        self.append(self.actions)
        self.append(self.options)
        self.append(self.help)

    def set_accels(self, accel_group):
        """
        Set accelerators for menu items
        """
        if sys.platform == 'darwin':
            self.file_menu.quit.add_accelerator(
                    'activate', accel_group, gtk.keysyms.Q,
                    gtk.gdk.META_MASK, gtk.ACCEL_VISIBLE)
            self.file_menu.disconnect.add_accelerator(
                    'activate', accel_group, gtk.keysyms.D,
                    gtk.gdk.META_MASK, gtk.ACCEL_VISIBLE)
        else:
            self.file_menu.quit.add_accelerator(
                    'activate', accel_group, gtk.keysyms.Q,
                    gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
            self.file_menu.disconnect.add_accelerator(
                    'activate', accel_group, gtk.keysyms.D,
                    gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)

class FileMenu(gtk.Menu):
    """
    A widget that represents the File popup menu located on the main menu
    """

    def __init__(self, handler, session):
        """
        constructor

        handler -- e3common.Handler.FileHandler
        """
        gtk.Menu.__init__(self)
        self.handler = handler

        if session and session.session_has_service(e3.Session.SERVICE_STATUS):
            StatusMenu = extension.get_default('menu status')
            self.status = gtk.ImageMenuItem(_('Status'))
            self.status.set_image(gtk.image_new_from_stock(gtk.STOCK_CONVERT,
                gtk.ICON_SIZE_MENU))
            self.status_menu = StatusMenu(handler.on_status_selected)
            self.status.set_submenu(self.status_menu)
            self.append(self.status)

        self.disconnect = gtk.ImageMenuItem(gtk.STOCK_DISCONNECT)
        self.disconnect.connect('activate',
            lambda *args: self.handler.on_disconnect_selected())
        self.quit = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        self.quit.connect('activate',
            lambda *args: self.handler.on_quit_selected())

        self.append(self.disconnect)
        self.append(gtk.SeparatorMenuItem())
        self.append(self.quit)

class ActionsMenu(gtk.Menu):
    """
    A widget that represents the Actions popup menu located on the main menu
    """

    def __init__(self, handler, session):
        """
        constructor

        handler -- e3common.Handler.ActionsHandler
        """
        gtk.Menu.__init__(self)
        self.handler = handler

        ContactsMenu = extension.get_default('menu contact')
        AccountMenu = extension.get_default('menu account')

        self.contact = gtk.ImageMenuItem(_('_Contact'))
        self.contact.set_image(utils.safe_gtk_image_load(gui.theme.image_theme.chat))
        self.contact_menu = ContactsMenu(self.handler.contact_handler, session)
        self.contact.set_submenu(self.contact_menu)
        self.account = gtk.ImageMenuItem(_('_Account'))
        self.account.set_image(utils.safe_gtk_image_load(gui.theme.image_theme.chat))

        self.account_menu = AccountMenu(self.handler.my_account_handler)
        self.myaccount = gtk.ImageMenuItem(_('_Profile'))
        self.myaccount.set_image(utils.safe_gtk_image_load(gui.theme.image_theme.chat))
        self.myaccount.set_submenu(self.account_menu)

        self.append(self.contact)

        if session.session_has_service(e3.Session.SERVICE_GROUP_MANAGING):
            GroupsMenu = extension.get_default('menu group')
            self.group = gtk.ImageMenuItem(_('_Group'))
            self.group.set_image(utils.safe_gtk_image_load(gui.theme.image_theme.group_chat))
            self.group_menu = GroupsMenu(self.handler.group_handler)
            self.group.set_submenu(self.group_menu)
            self.append(self.group)

        self.append(self.myaccount)

class OptionsMenu(gtk.Menu):
    """
    A widget that represents the Options popup menu located on the main menu
    """

    def __init__(self, handler, config):
        """
        constructor

        handler -- e3common.Handler.OptionsHandler
        """
        gtk.Menu.__init__(self)
        self.handler = handler

        if not check_gtk3():
            self.by_status = gtk.RadioMenuItem(None, _('Order by _status'))
            self.by_group = gtk.RadioMenuItem(self.by_status, _('Order by _group'))
        else:
            self.by_status = gtk.RadioMenuItem(_('Order by _status'))
            self.by_status.set_use_underline(True)
            self.by_group = gtk.RadioMenuItem.new_with_mnemonic_from_widget(self.by_status, _('Order by _group'))
        self.by_group.set_active(config.b_order_by_group)
        self.by_status.set_active(not config.b_order_by_group)

        self.show_menu = gtk.MenuItem(_('Show...'))
        self.show_submenu = gtk.Menu()

        self.show_offline = gtk.CheckMenuItem(_('Show _offline contacts'))
        self.show_offline.set_active(config.b_show_offline)
        self.group_offline = gtk.CheckMenuItem(_('G_roup offline contacts'))
        self.group_offline.set_active(config.b_group_offline)
        self.show_empty_groups = gtk.CheckMenuItem(_('Show _empty groups'))
        self.show_empty_groups.set_active(config.b_show_empty_groups)
        self.show_blocked = gtk.CheckMenuItem(_('Show _blocked contacts'))
        self.show_blocked.set_active(config.b_show_blocked)
        self.order_by_name = gtk.CheckMenuItem(_('Sort by name'))
        self.order_by_name.set_active(config.b_order_by_name)

        self.preferences = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
        self.preferences.connect('activate',
            lambda *args: self.handler.on_preferences_selected())

        self.by_status.connect('toggled',
            lambda *args: self.handler.on_order_by_status_toggled(
                self.by_status.get_active()))
        self.by_group.connect('toggled',
            lambda *args: self.handler.on_order_by_group_toggled(
                self.by_group.get_active()))
        self.show_empty_groups.connect('toggled',
            lambda *args: self.handler.on_show_empty_groups_toggled(
                self.show_empty_groups.get_active()))
        self.show_offline.connect('toggled',
            lambda *args: self.handler.on_show_offline_toggled(
                self.show_offline.get_active()))
        self.group_offline.connect('toggled',
            lambda *args: self.handler.on_group_offline_toggled(
                self.group_offline.get_active()))
        self.show_blocked.connect('toggled',
            lambda *args: self.handler.on_show_blocked_toggled(
                self.show_blocked.get_active()))
        self.order_by_name.connect('toggled',
            lambda *args: self.handler.on_order_by_name_toggled(
                self.order_by_name.get_active()))

        self.show_menu.set_submenu(self.show_submenu)
        self.show_submenu.append(self.show_offline)

        self.append(self.by_status)
        self.append(self.by_group)
        self.append(gtk.SeparatorMenuItem())
        self.append(self.show_menu)
        self.show_submenu.append(self.show_empty_groups)
        self.show_submenu.append(self.show_blocked)
        self.show_submenu.append(self.order_by_name)
        self.append(self.group_offline)
        self.append(gtk.SeparatorMenuItem())
        self.append(self.preferences)

class HelpMenu(gtk.Menu):
    """
    A widget that represents the Help popup menu located on the main menu
    """

    def __init__(self, handler):
        """
        constructor

        handler -- e3common.Handler.HelpHandler
        """
        gtk.Menu.__init__(self)
        self.handler = handler

        self.website = gtk.ImageMenuItem(_('_Website'))
        self.website.set_image(gtk.image_new_from_stock(gtk.STOCK_HOME,
            gtk.ICON_SIZE_MENU))
        self.website.connect('activate',
            lambda *args: self.handler.on_website_selected())
        self.about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
        self.about.connect('activate',
            lambda *args: self.handler.on_about_selected())

        self.debug = gtk.MenuItem(_('Debug'))
        self.debug.connect('activate',
                lambda *args: self.handler.on_debug_selected())
                
        self.updatecheck = gtk.ImageMenuItem(_('Check for updates'))
        self.updatecheck.set_image(gtk.image_new_from_stock(gtk.STOCK_REFRESH,
            gtk.ICON_SIZE_MENU))
        self.updatecheck.connect('activate', lambda *args: self.handler.on_check_update_selected())

        self.append(self.website)
        self.append(self.about)
        self.append(self.debug)
        self.append(gtk.SeparatorMenuItem())
        self.append(self.updatecheck)
