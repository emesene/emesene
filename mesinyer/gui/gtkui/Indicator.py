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
        self.menu.hide_show_mainwindow.connect('activate', self._on_activate)
        self.menu.show_all()
        self.set_menu(self.menu)

    def set_main(self, session):
        """
        method called to set the state to the main window
        """
        self.handler.session = session
        self.handler.session.signals.status_change_succeed.subscribe(self._on_change_status)
        self.menu = MainMenu(self.handler)
        self.menu.hide_show_mainwindow.connect('activate', self._on_activate)
        self.menu.show_all()
        self.set_menu(self.menu)

    def _on_change_status(self,stat):
        """
        change the icon in the tray according to user's state
        """
        if stat not in status.ALL or stat == -1:
            return
        self.set_icon(self.handler.theme.status_icons[stat].split("/")[-1])
        
    def _on_activate(self, trayicon):
	"""
        callback called when the menu entry 'hide/show emesene'
        is clicked
        """

        if(self.main_window != None):
            if(self.main_window.get_property("visible")):
                self.main_window.hide()
            else:
                self.main_window.show()

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
        self.hide_show_mainwindow = gtk.MenuItem('Hide/Show emesene')
        self.quit = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        self.quit.connect('activate',
            lambda *args: self.handler.on_quit_selected())
            
        self.append(self.hide_show_mainwindow)
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
        
        self.hide_show_mainwindow = gtk.MenuItem('Hide/Show emesene')

        self.disconnect = gtk.ImageMenuItem(gtk.STOCK_DISCONNECT)
        self.disconnect.connect('activate',
            lambda *args: self.handler.on_disconnect_selected())
        self.quit = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        self.quit.connect('activate',
            lambda *args: self.handler.on_quit_selected())

        self.append(self.status)
        self.append(self.hide_show_mainwindow)
        self.append(self.disconnect)
        self.append(gtk.SeparatorMenuItem())
        self.append(self.quit)
