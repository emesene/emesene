import os
import gtk
import time
import appindicator

import gui
import utils
import extension
from e3 import status

import logging
log = logging.getLogger('gui.gtkui.Indicator')

import TrayIcon

HASMESSAGINGMENU = True
try:
    import MessagingMenu
except ImportError:
    HASMESSAGINGMENU = False
    log.exception(_('Could not import python-indicate: please install via your package manager.'))

# This line will except with too old version of appindicator
# so you'll get your nice gtk trayicon
# This is fixed since Ubuntu Maverick (10.10)       
# https://bugs.launchpad.net/indicator-application/+bug/607831
try:
    func = getattr(appindicator.Indicator, "set_icon_theme_path")
except AttributeError:
    raise ImportError

class Indicator(appindicator.Indicator):
    """
    A widget that implements the tray icon of emesene for gtk
    """

    def __init__(self, handler, main_window=None):
        """
        constructor

        handler -- a e3common.Handler.TrayIconHandler object
        """
        NAME = 'Indicator'
        DESCRIPTION = 'The Ayatana Indicator applet extension'
        AUTHOR = 'Riccardo (C10ud), Stefano(Cando)'
        WEBSITE = 'www.emesene.org'
        appindicator.Indicator.__init__(self, "emesene", "logo", \
            appindicator.CATEGORY_APPLICATION_STATUS, \
            os.path.join(os.getcwd(), handler.theme.panel_path))

        self.handler = handler

        self.main_window = main_window
        self.conversations = None

        self.menu = None
        self.set_login()
        self.set_status(appindicator.STATUS_ACTIVE)

        self.messaging_menu = None
        if HASMESSAGINGMENU:
            self.messaging_menu = MessagingMenu.MessagingMenu(handler, main_window)

    def set_visible(self, arg):
        """ dummy, indicators remove themselves automagically """
        if self.messaging_menu:
            self.messaging_menu.set_visible(arg)

    def set_login(self):
        """
        method called to set the state to the login window
        """
        icon_name = self.handler.theme.logo.split("/")[-1]
        icon_name = icon_name[:icon_name.rfind(".")]
        self.set_icon(icon_name)
        self.menu = TrayIcon.LoginMenu(self.handler)
        self.menu.hide_show_mainwindow.connect('activate', self._on_activate)
        self.menu.show_all()
        self.set_menu(self.menu)

    def set_main(self, session):
        """
        method called to set the state to the main window
        """
        self.handler.session = session
        self.handler.session.signals.status_change_succeed.subscribe(self._on_change_status)
        self.menu = TrayIcon.MainMenu(self.handler, self.main_window)
        self.menu.hide_show_mainwindow.connect('activate', self._on_activate)
        self.menu.show_all()
        self.set_menu(self.menu)

        if self.messaging_menu:
            self.messaging_menu.set_main(session)

    def set_conversations(self, convs):
        """
        Sets the conversations manager
        """
        self.conversations = convs

        if self.messaging_menu:
            self.messaging_menu.set_conversations(convs)

    def set_contacts(self, contacts):
        """
        sets the contacts
        """

    def _on_change_status(self,stat):
        """
        change the icon in the tray according to user's state
        """
        path = os.path.join(os.getcwd(), self.handler.theme.panel_path)
        self.set_icon_theme_path(path)
        #the appindicator takes a 'name' of an icon and NOT a filename. 
        #that means that we have to strip the file extension
        icon_name = self.handler.theme.status_icons_panel[stat].split("/")[-1]
        icon_name = icon_name[:icon_name.rfind(".")]
        self.set_icon(icon_name)        
        
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

