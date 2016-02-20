# -*- coding: utf-8 -*-
#
# Copyright (C) 2006  Ali Sabil <ali.sabil@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

from papyon.gnet.io import AbstractClient
from papyon.gnet.constants import IoStatus

import gobject

__all__ = ['AbstractProxy']

class AbstractProxy(AbstractClient):
    def __init__(self, client, proxy_infos):
        self._client = client
        self._proxy = proxy_infos
        self._client.connect("sent", self._on_client_sent)
        self._client.connect("received", self._on_client_received)
        self._client.connect("notify::status", self._on_client_status)
        AbstractClient.__init__(self, client.host, client.port)

    def _on_client_status(self, client, param):
        status = client.get_property("status")
        if status == IoStatus.OPEN:
            self._status = IoStatus.OPEN
        elif status == IoStatus.CLOSED:
            self._status = IoStatus.CLOSED

    def _on_client_sent(self, client, data, length):
        self.emit("sent", data, length)

    def _on_client_received(self, client, data, length):
        self.emit("received", data, length)
gobject.type_register(AbstractProxy)
