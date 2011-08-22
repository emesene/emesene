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
import appindicator

import logging
log = logging.getLogger('gui.common.Indicator')

import TrayIcon
import gui

# This line will except with too old version of appindicator
# so you'll get your nice gtk trayicon
# This is fixed since Ubuntu Maverick (10.10)
# https://bugs.launchpad.net/indicator-application/+bug/607831
try:
    func = getattr(appindicator.Indicator, "set_icon_theme_path")
except AttributeError:
    raise ImportError

import uuid

class Indicator(appindicator.Indicator, gui.BaseTray):
    """
    A widget that implements the tray icon of emesene for gtk
    """
    NAME = 'Indicator'
    DESCRIPTION = _('The Ayatana Indicator applet extension')
    AUTHOR = 'Riccardo (C10ud), Stefano(Cando)'
    WEBSITE = 'www.emesene.org'

    def __init__(self, handler, main_window=None):
        """
        constructor

        handler -- a e3common.Handler.TrayIconHandler object
        """
        gui.BaseTray.__init__(self, handler)
        app_name_hax = "emesene-%s" % uuid.uuid1()
        appindicator.Indicator.__init__(
            self, app_name_hax, "logo",
            appindicator.CATEGORY_APPLICATION_STATUS,
            os.path.join(os.getcwd(), handler.theme.image_theme.panel_path))

        self.main_window = main_window

        gui.BaseTray.set_visible(self, True)
        self.menu = None
        self.set_login()
        self.set_status(appindicator.STATUS_ACTIVE)

    def set_login(self):
        """
        method called to set the state to the login window
        """
        icon_name = self.handler.theme.image_theme.logo.split("/")[-1]
        icon_name = icon_name[:icon_name.rfind(".")]
        self.set_icon(icon_name)
        self.menu = TrayIcon.LoginMenu(self.handler, self.main_window)
        self.menu.show_all()
        self.set_menu(self.menu)

    def set_main(self, session):
        """
        method called to set the state to the main window
        """
        gui.BaseTray.set_main(self, session)
        self.menu = TrayIcon.MainMenu(self.handler, self.main_window)
        self.menu.show_all()
        self.set_menu(self.menu)
        self._on_status_change_succeed(self.handler.session.account.status)

    def _on_status_change_succeed(self, stat):
        """
        change the icon in the tray according to user's state
        """
        path = os.path.join(os.getcwd(),
                            self.handler.theme.image_theme.panel_path)
        self.set_icon_theme_path(path)
        #the appindicator takes a 'name' of an icon and NOT a filename.
        #that means that we have to strip the file extension
        icon_name = self.handler.theme.image_theme.status_icons_panel[stat].split("/")[-1]
        icon_name = icon_name[:icon_name.rfind(".")]
        self.set_icon(icon_name)
