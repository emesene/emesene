# -*- coding: utf-8 -*-
#
# Copyright (C) 2007  Ali Sabil <ali.sabil@gmail.com>
# Copyright (C) 2007  Ole André Vadla Ravnås <oleavr@gmail.com>
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

"""Client event interfaces

The interfaces defined in this module allow receiving core notification events
from the client.

    @sort: ClientEventInterface
    @group Enums: ClientState, ClientErrorType
    @group Error Enums: NetworkError, AuthenticationError, ProtocolError,
        AddressBookError, OfflineMessagesBoxError"""

from papyon.event import BaseEventInterface

import papyon.gnet
import papyon.service.AddressBook.constants
import papyon.service.OfflineIM.constants
import papyon.msnp

__all__ = [ "ClientState", "ClientErrorType",
        "NetworkError", "AuthenticationError", "ProtocolError",
        "AddressBookError", "OfflineMessagesBoxError",
        "ClientEventInterface" ]

class ClientState(object):
    "L{Client<papyon.Client>} states"
    CLOSED = 0
    CONNECTING = 1
    CONNECTED = 2
    AUTHENTICATING = 3
    AUTHENTICATED = 4
    SYNCHRONIZING = 5
    SYNCHRONIZED = 6
    OPEN = 7

class ClientErrorType(object):
    """L{Client<papyon.Client>} error types
        @see: L{ClientEventInterface.on_client_error}"""

    NETWORK = 0
    "Network related errors"
    AUTHENTICATION = 1
    "Authentication related errors"
    PROTOCOL = 2
    "Protocol related errors"
    ADDRESSBOOK = 3
    "Address book related errors"
    OFFLINE_MESSAGES = 4
    "Offline IM related errors"

NetworkError = papyon.gnet.IoError
"Network related errors"

class AuthenticationError(object):
    "Authentication related errors"
    UNKNOWN = 0
    INVALID_USERNAME = 1
    INVALID_PASSWORD = 2
    INVALID_USERNAME_OR_PASSWORD = 3

class ProtocolError(object):
    "Protocol related errors"
    UNKNOWN = 0
    OTHER_CLIENT = 1
    SERVER_DOWN = 2

AddressBookError = papyon.service.AddressBook.constants.AddressBookError
OfflineMessagesBoxError = papyon.service.OfflineIM.constants.OfflineMessagesBoxError


class ClientEventInterface(BaseEventInterface):
    """Interface allowing the user to get notified about the
    L{Client<papyon.Client>} events"""

    def __init__(self, client):
        """Initializer
            @param client: the client we want to be notified for its events
            @type client: L{Client<papyon.Client>}"""
        BaseEventInterface.__init__(self, client)

    def on_client_state_changed(self, state):
        """Called when the state of the L{Client<papyon.Client>} changes.
            @param state: the new state of the client
            @type state: L{ClientState}"""
        pass

    def on_client_error(self, type, error):
        """Called when an error occurs in the L{Client<papyon.Client>}.

            @param type: the error type
            @type type: L{ClientErrorType}

            @param error: the error code
            @type error: L{NetworkError} or L{AuthenticationError} or
                L{ProtocolError} or L{AddressBookError} or
                L{OfflineMessagesBoxError}"""
        pass

