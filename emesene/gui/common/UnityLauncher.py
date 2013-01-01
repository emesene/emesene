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

import logging
log = logging.getLogger("gui.common.UnityLauncher")

import dbus, dbus.service
import gui
from NumerableTrayIcon import NumerableTrayIcon

class UnityDBusController(dbus.service.Object):
    def __init__(self, app_uri):
        dbus.service.Object.__init__(self, dbus.SessionBus(), '/')
        self.properties = {}
        self.app_uri = app_uri
        self._update()

    def set_property(self, property_, value):
        if property_ == "count":
            value = dbus.Int64(value)
        self.properties[property_] = value
        self._update()

    def _update(self):
        self.Update(self.app_uri, self.properties)

    @dbus.service.signal(dbus_interface='com.canonical.Unity.LauncherEntry',
                         signature=("sa{sv}"))
    def Update(self, app_uri, properties):
        pass

    @dbus.service.method(dbus_interface='com.canonical.Unity.LauncherEntry',
                         in_signature="", out_signature="sa{sv}")
    def Query(self):
        return self.app_uri, self.properties

class UnityLauncher(NumerableTrayIcon):
    ''' A widget that implements fancy unity launcher actions '''
    NAME = 'Unity Launcher'
    DESCRIPTION = 'Unity message count and quicklist'
    AUTHOR = 'Sven (Sbte)'
    WEBSITE = 'www.emesene.org'

    def __init__ (self, handler=None):
        '''constructor'''
        NumerableTrayIcon.__init__(self, handler)
        self.launcher = UnityDBusController("application://emesene.desktop")

    def count_changed(self, count):
        show_count = (self.count != 0)
        self.launcher.set_property("count-visible", show_count)
        self.launcher.set_property("urgent", show_count)
        self.launcher.set_property("count", self.count)

    def unsubscribe(self):
        self.disconnect_signals()
