import gtk

import dummy_components

class MainMenu(gtk.MenuBar):
    """
    A widget that represents the main menu of the main window
    """

    def __init__(self, handlers):
        """
        constructor

        handlers is a e3common.Handler.MenuHandler
        """
        gtk.MenuBar.__init__(self)

        self.handlers = handlers

        FileMenu = dummy_components.get_default('gtk menu file')
        ActionsMenu = dummy_components.get_default('gtk menu actions')
        OptionsMenu = dummy_components.get_default('gtk menu options')
        HelpMenu = dummy_components.get_default('gtk menu help')

        self.file = gtk.MenuItem('File')
        self.file_menu = FileMenu(self.handlers.file_handler)
        self.file.set_submenu(self.file_menu)

        self.actions = gtk.MenuItem('Actions')
        self.actions_menu = ActionsMenu(self.handlers.actions_handler)
        self.actions.set_submenu(self.actions_menu)

        self.options = gtk.MenuItem('Options')
        self.options_menu = OptionsMenu(self.handlers.options_handler)
        self.options.set_submenu(self.options_menu)

        self.help = gtk.MenuItem('Help')
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

        StatusMenu = dummy_components.get_default('gtk menu status')
        self.status = gtk.MenuItem('Status')
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

        ContactsMenu = dummy_components.get_default('gtk menu contact')
        GroupsMenu = dummy_components.get_default('gtk menu group')
        AccountMenu = dummy_components.get_default('gtk menu account')

        self.contact = gtk.MenuItem('Contact')
        self.contact_menu = ContactsMenu(self.handler.contact_handler)
        self.contact.set_submenu(self.contact_menu)
        self.group = gtk.MenuItem('Group')
        self.group_menu = GroupsMenu(self.handler.group_handler)
        self.group.set_submenu(self.group_menu)
        self.account = gtk.MenuItem('Account')
        self.account_menu = AccountMenu(self.handler.my_account_handler)
        self.account.set_submenu(self.account_menu)

        self.append(self.contact)
        self.append(self.group)
        self.append(self.account)

class OptionsMenu(gtk.Menu):
    """
    A widget that represents the Options popup menu located on the main menu
    """

    def __init__(self, handler):
        """
        constructor

        handler -- e3common.Handler.OptionsHandler
        """
        gtk.Menu.__init__(self)
        self.handler = handler

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

        self.website = gtk.MenuItem('Website')
        self.website.connect('activate',
            lambda *args: self.handler.on_website_selected())
        self.about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
        self.about.connect('activate',
            lambda *args: self.handler.on_about_selected())

        self.append(self.website)
        self.append(self.about)
