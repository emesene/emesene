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

import gui
from gui.gtkui import check_gtk3

if check_gtk3():
    try:
        from gi.repository import AppIndicator3 as appindicator
    except ImportError:
        from gi.repository import AppIndicator as appindicator
    appindicator.STATUS_ACTIVE = appindicator.IndicatorStatus.ACTIVE
    appindicator.CATEGORY_APPLICATION_STATUS = appindicator.IndicatorCategory.APPLICATION_STATUS
    appindicator.new_with_path = appindicator.Indicator.new_with_path
else:
    import appindicator
    appindicator.new_with_path = appindicator.Indicator

import logging
log = logging.getLogger('gui.common.Indicator')

import TrayIcon

# This line will except with too old version of appindicator
# so you'll get your nice gtk trayicon
# This is fixed since Ubuntu Maverick (10.10)
# https://bugs.launchpad.net/indicator-application/+bug/607831
try:
    func = getattr(appindicator.Indicator, "set_icon_theme_path")
except AttributeError:
    raise ImportError

import uuid

class Indicator(gui.BaseTray):
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
        self.indicator = appindicator.new_with_path(
            app_name_hax,
            self._get_icon_name(self.handler.theme.image_theme.logo_panel),
            appindicator.CATEGORY_APPLICATION_STATUS,
            self._get_icon_directory(self.handler.theme.image_theme.logo_panel))

        if hasattr(self.indicator.props, 'title'):
            self.indicator.set_property('title', 'emesene')

        self.main_window = main_window

        self.menu = None
        self.set_login()
        self.indicator.set_status(appindicator.STATUS_ACTIVE)

    def set_login(self):
        """
        method called to set the state to the login window
        """
        icon_path = self.handler.theme.image_theme.logo_panel
        self.indicator.set_icon_theme_path(self._get_icon_directory(icon_path))
        self.indicator.set_icon(self._get_icon_name(icon_path))

        self.menu = TrayIcon.LoginMenu(self.handler, self.main_window)
        self.menu.show_all()
        self.indicator.set_menu(self.menu)

    def set_main(self, session):
        """
        method called to set the state to the main window
        """
        gui.BaseTray.set_main(self, session)
        if self.menu:
            self.menu.unsubscribe()
        self.menu = TrayIcon.MainMenu(self.handler, self.main_window)
        self.menu.show_all()
        self.indicator.set_menu(self.menu)
        self._on_status_change_succeed(self.handler.session.account.status)

    def _on_status_change_succeed(self, stat):
        """
        change the icon in the tray according to user's state
        """
        icon_path = self.handler.theme.image_theme.status_icons_panel[stat]
        self.indicator.set_icon_theme_path(self._get_icon_directory(icon_path))
        #the appindicator takes a 'name' of an icon and NOT a filename.
        #that means that we have to strip the file extension
        self.indicator.set_icon(self._get_icon_name(icon_path))

    def _get_icon_directory(self, icon_path):
        """
        get the directory of the current icon
        """
        return os.path.dirname(os.path.join(os.getcwd(), icon_path))

    def _get_icon_name(self, icon_path):
        """
        get the name of the current panel icon
        """
        name = os.path.basename(os.path.join(os.getcwd(), icon_path))
        name = os.path.splitext(name)
        return name[0]

    def hide(self):
        self.unsubscribe()
        self.indicator.set_status(appindicator.STATUS_PASSIVE)

    def unsubscribe(self):
        self.disconnect_signals()
        if self.menu:
            self.menu.unsubscribe()
