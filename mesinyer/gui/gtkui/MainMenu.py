import gtk

import gui
import utils

import extension
from debugger import dbg

class MainMenu(gtk.MenuBar):
    """
    A widget that represents the main menu of the main window
    """
    NAME = 'Main Menu'
    DESCRIPTION = 'The Main Menu of the main window'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, handlers, config):
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

        self.file = gtk.MenuItem('_File')
        self.file_menu = FileMenu(self.handlers.file_handler)
        self.file.set_submenu(self.file_menu)

        self.actions = gtk.MenuItem('_Actions')
        self.actions_menu = ActionsMenu(self.handlers.actions_handler)
        self.actions.set_submenu(self.actions_menu)

        self.options = gtk.MenuItem('_Options')
        self.options_menu = OptionsMenu(self.handlers.options_handler, config)
        self.options.set_submenu(self.options_menu)

        self.help = gtk.MenuItem('_Help')
        self.help_menu = HelpMenu(self.handlers.help_handler)
        self.help.set_submenu(self.help_menu)

        self.append(self.file)
        self.append(self.actions)
        self.append(self.options)
        self.append(self.help)


class FileMenu(gtk.Menu):
    """
    A widget that represents the File popup menu located on the main menu
    """

    def __init__(self, handler):
        """
        constructor

        handler -- e3common.Handler.FileHandler
        """
        gtk.Menu.__init__(self)
        self.handler = handler

        StatusMenu = extension.get_default('menu status')
        self.status = gtk.ImageMenuItem('Status')
        self.status.set_image(gtk.image_new_from_stock(gtk.STOCK_CONVERT,
            gtk.ICON_SIZE_MENU))
        self.status_menu = StatusMenu(handler.on_status_selected)
        self.status.set_submenu(self.status_menu)

        self.disconnect = gtk.ImageMenuItem(gtk.STOCK_DISCONNECT)
        self.disconnect.connect('activate',
            lambda *args: self.handler.on_disconnect_selected())
        self.quit = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        self.quit.connect('activate',
            lambda *args: self.handler.on_quit_selected())

        self.append(self.status)
        self.append(self.disconnect)
        self.append(gtk.SeparatorMenuItem())
        self.append(self.quit)

class ActionsMenu(gtk.Menu):
    """
    A widget that represents the Actions popup menu located on the main menu
    """

    def __init__(self, handler):
        """
        constructor

        handler -- e3common.Handler.ActionsHandler
        """
        gtk.Menu.__init__(self)
        self.handler = handler

        ContactsMenu = extension.get_default('menu contact')
        GroupsMenu = extension.get_default('menu group')
        AccountMenu = extension.get_default('menu account')

        self.contact = gtk.ImageMenuItem('_Contact')
        self.contact.set_image(utils.safe_gtk_image_load(gui.theme.chat))
        self.contact_menu = ContactsMenu(self.handler.contact_handler)
        self.contact.set_submenu(self.contact_menu)
        self.group = gtk.ImageMenuItem('_Group')
        self.group.set_image(utils.safe_gtk_image_load(gui.theme.group_chat))
        self.group_menu = GroupsMenu(self.handler.group_handler)
        self.group.set_submenu(self.group_menu)
        self.account = gtk.ImageMenuItem('_Account')
        self.account.set_image(utils.safe_gtk_image_load(gui.theme.chat))
        self.account_menu = AccountMenu(self.handler.my_account_handler)
        self.account.set_submenu(self.account_menu)

        self.append(self.contact)
        self.append(self.group)
        self.append(self.account)

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

        self.by_status = gtk.RadioMenuItem(None, 'Order by _status')
        self.by_group = gtk.RadioMenuItem(self.by_status, 'Order by _group')
        self.by_group.set_active(config.b_order_by_group)
        self.by_status.set_active(not config.b_order_by_group)

        self.show_offline = gtk.CheckMenuItem('Show _offline contacts')
        self.show_offline.set_active(config.b_show_offline)
        self.show_empty_groups = gtk.CheckMenuItem('Show _empty groups')
        self.show_empty_groups.set_active(config.b_show_empty_groups)
        self.show_blocked = gtk.CheckMenuItem('Show _blocked contacts')
        self.show_blocked.set_active(config.b_show_blocked)

        self.preferences = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
        self.preferences.connect('activate',
            lambda *args: self.handler.on_preferences_selected())
        self.plugins = gtk.ImageMenuItem('Plug_ins')
        self.plugins.set_image(gtk.image_new_from_stock(gtk.STOCK_CONNECT,
            gtk.ICON_SIZE_MENU))
        self.plugins.connect('activate',
            lambda *args: self.handler.on_plugins_selected())

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
        self.show_blocked.connect('toggled', 
            lambda *args: self.handler.on_show_blocked_toggled(
                self.show_blocked.get_active()))

        self.append(self.by_status)
        self.append(self.by_group)
        self.append(gtk.SeparatorMenuItem())
        self.append(self.show_offline)
        self.append(self.show_empty_groups)
        self.append(self.show_blocked)
        self.append(gtk.SeparatorMenuItem())
        self.append(self.preferences)
        self.append(self.plugins)

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

        self.website = gtk.ImageMenuItem('_Website')
        self.website.set_image(gtk.image_new_from_stock(gtk.STOCK_HOME,
            gtk.ICON_SIZE_MENU))
        self.website.connect('activate',
            lambda *args: self.handler.on_website_selected())
        self.about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
        self.about.connect('activate',
            lambda *args: self.handler.on_about_selected())

        self.debug = gtk.MenuItem('Debug')
        self.debug.connect('activate',
                lambda *args: self.handler.on_debug_selected())

        self.append(self.website)
        self.append(self.about)
        self.append(self.debug)
