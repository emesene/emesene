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

from e3.base.Event import Event

#XXX: only activate on gtk3
import gobject
if not hasattr(gobject, '_introspection_module'):
    raise ImportError

import gi
from gi.repository import Gio
import logging
log = logging.getLogger("emesene.e3.common.NetworkManagerHelper")
import extension

class GioNetworkChecker():
    ''' this class does lazy checks for network availability and 
    disconnects emesene if the network goes down '''
    def __init__(self):
        self.__session = None
        self.alert_watcher = None

    #Public methods
    def set_new_session(self, session):
        self.__session = session

        if self.alert_watcher is None:
            self.alert_watcher = Gio.NetworkMonitor.get_default()
            self.alert_watcher.connect("network-changed", self._on_network_changed)

    def stop(self):
        pass

    #Callback functions
    def _on_network_changed(self, monitor, avariable):
        if not avariable:
            # 1 means reconnect
            self.__session.add_event(Event.EVENT_DISCONNECTED, 'Network error', 1)

extension.category_register('network checker', GioNetworkChecker)
extension.set_default('network checker', GioNetworkChecker)
