import os
import gtk
import appindicator

import extension
from e3 import status

class Indicator(appindicator.Indicator):
    """
    A widget that implements the tray icon of emesene for gtk
    """

    def __init__(self, handler, main_window=None):
        """
        constructor

        handler -- a e3common.Handler.TrayIconHandler object
        """
        appindicator.Indicator.__init__(self, "emesene", "logo", \
            appindicator.CATEGORY_APPLICATION_STATUS, \
            os.path.join(os.getcwd(), handler.theme.theme_path))

        self.handler = handler

        self.main_window = main_window
        self.conversations = None

        self.set_login()
        self.set_status(appindicator.STATUS_ACTIVE)

    def set_visible(self, arg):
        """ dummy, indicators remove themselves automagically """
        return

    def set_login(self):
        """
        method called to set the state to the login window
        """
        self.menu = LoginMenu(self.handler)
        self.menu.show_all()
        self.set_menu(self.menu)

    def set_main(self, session):
        """
        method called to set the state to the main window
        """
        self.handler.session = session
        self.handler.session.signals.status_change_succeed.subscribe(self._on_change_status)
        self.menu = MainMenu(self.handler)
        self.menu.show_all()
        self.set_menu(self.menu)

    def set_conversations(self, convs):
        """
        Sets the conversations manager
        """
        self.conversations = convs

    def _on_change_status(self,stat):
        """
        change the icon in the tray according to user's state
        """
        if stat not in status.ALL or stat == -1:
            return
        self.set_icon(self.handler.theme.status_icons[stat].split("/")[-1])

class LoginMenu(gtk.Menu):
    """
    a widget that represents the menu displayed on the trayicon on the
    login window
    """

    def __init__(self, handler):
        """
        constructor

        handler -- a e3common.Handler.TrayIconHandler object
        """
        gtk.Menu.__init__(self)
        self.handler = handler
        self.quit = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        self.quit.connect('activate',
            lambda *args: self.handler.on_quit_selected())

        self.append(self.quit)

class MainMenu(gtk.Menu):
    """
    a widget that represents the menu displayed on the trayicon on the
    main window
    """

    def __init__(self, handler):
        """
        constructor

        handler -- a e3common.Handler.TrayIconHandler object
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
