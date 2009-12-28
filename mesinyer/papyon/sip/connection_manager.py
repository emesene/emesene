# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2009 Collabora Ltd.
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from papyon.msnp.constants import *
from papyon.sip.connection import *
from papyon.sip.transport import *

import gobject

class SIPConnectionManager(gobject.GObject):

    __gsignals__ = {
        'invite-received': (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            ([object]))
    }

    server = "vp.sip.messenger.msn.com"
    port = 443

    def __init__(self, client, protocol):
        gobject.GObject.__init__(self)
        self._client = client
        self._protocol = protocol
        self._protocol.connect("buddy-notification-received",
                self.on_notification_received)
        self._connections = {}
        self._disconnecting = []

        self.create_connection(True, "NS")

    def create_connection(self, tunneled, host=None):
        if tunneled:
            transport = SIPTunneledTransport(self._protocol)
            connection = SIPTunneledConnection(self._client, transport)
        else:
            transport = SIPTransport(host, self.port)
            connection = SIPConnection(self._client, transport)
        connection.connect("invite-received", self.on_invite_received)
        connection.connect("disconnecting", self.on_connection_disconnecting)
        connection.connect("disconnected", self.on_connection_disconnected)
        self._connections[host] = connection
        return connection

    def remove_connection(self, connection):
        host = None
        for k, v in self._connections.iteritems():
            if v == connection:
                host = k
        if host is not None:
            del self._connections[host]

    def get_connection(self, tunneled, host=None):
        if tunneled:
            host = "NS"
        connection = self._connections.get(host, None)
        if connection is None:
            connection = self.create_connection(tunneled, host)
        return connection

    def create_call(self, peer):
        tunneled = (self._client.profile.client_id.supports_tunneled_sip and
                    peer.client_capabilities.supports_tunneled_sip)
        connection = self.get_connection(tunneled, self.server)
        call = connection.create_call(peer=peer)
        return call

    def on_notification_received(self, protocol, type, notification):
        if type is not UserNotificationTypes.SIP_INVITE:
            return
        args = notification.payload.split()
        if len(args) == 3 and args[0] == "INVITE":
            # Register to the server so we can take the call
            connection = self.get_connection(False, args[1])
            connection.register()

    def on_invite_received(self, connection, call):
        self.emit("invite-received", call)

    def on_connection_disconnecting(self, connection):
        self.remove_connection(connection)
        if connection not in self._disconnecting:
            self._disconnecting.append(connection)

    def on_connection_disconnected(self, connection):
        if connection in self._disconnecting:
            self._disconnecting.remove(connection)
        else:
            self.remove_connection(connection)
