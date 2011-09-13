# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2010 Collabora Ltd.
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

__all__ = ["ClientErrorType", "ClientError", "ParseError"]

class ClientErrorType(object):
    """L{Client<papyon.Client>} error types
        @see: L{ClientEventInterface.on_client_error}"""

    UNKNOWN = 0
    "Generic errors"
    NETWORK = 1
    "Network related errors"
    AUTHENTICATION = 2
    "Authentication related errors"
    PROTOCOL = 3
    "Protocol related errors"
    ADDRESSBOOK = 4
    "Address book related errors"
    CONTENT_ROAMING = 5
    "Content roaming related errors"
    OFFLINE_MESSAGES = 6
    "Offline IM related errors"
    SPACES = 7
    "Spaces related errors"

class ClientError(Exception):
    def __init__(self, type=0, code=0):
        Exception.__init__(self)
        self._type = type
        self._code = code

    @property
    def type(self):
        return self._type

    def __eq__(self, other):
        #backward compatibility (error was an integer)
        if isinstance(other, int):
            return (self._code == other)
        return (self == other)

    def __int__(self):
        return self._code

    def __str__(self):
        return str(self._code)

class ParseError(ClientError):
    def __init__(self, protocol, message, infos):
        ClientError.__init__(self, ClientErrorType.UNKNOWN, 0)
        self.protocol = protocol
        self.message = message
        self.infos = infos

    def __str__(self):
        ret = "%s Parse Error: %s" % (self.protocol, self.message)
        if self.infos:
            ret += "\r\n" + self.infos
        return ret
