# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Johann Prieur <johann.prieur@gmail.com>
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

from papyon.errors import ClientError, ClientErrorType

__all__ = ["OfflineMessagesBoxState", "OfflineMessagesBoxError"]

class OfflineMessagesBoxState(object):
    """Offline messages box synchronization state.

    The box is said to be synchronized when it
    owns the references to all the new messages on the server."""

    NOT_SYNCHRONIZED = 0
    """The box is not synchronized yet"""
    SYNCHRONIZING = 1
    """The box is being synchronized"""
    SYNCHRONIZED = 2
    """The box is already synchronized"""

class OfflineMessagesBoxError(ClientError):
    "Offline IM related errors"
    UNKNOWN = 0
    AUTHENTICATION_FAILED = 1
    SYSTEM_UNAVAILABLE = 2
    SENDER_THROTTLE_LIMIT_EXCEEDED = 3

    def __init__(self, code, fault="", details=""):
        ClientError.__init__(self, ClientErrorType.OFFLINE_MESSAGES, code)
        self._fault = fault
        self._details = details

    @staticmethod
    def from_fault(fault):
        error_code = OfflineMessagesBoxError.UNKNOWN
        faultcode = fault.faultcode
        faultstring = fault.faultstring
        if faultcode.endswith("AuthenticationFailed"):
            error_code = OfflineMessagesBoxError.AUTHENTICATION_FAILED
        elif faultcode.endswith("SystemUnavailable"):
            error_code = OfflineMessagesBoxError.SYSTEM_UNAVAILABLE
        elif faultcode.endswith("SenderThrottleLimitExceeded"):
            error_code = OfflineMessagesBoxError.SENDER_THROTTLE_LIMIT_EXCEEDED
        return OfflineMessagesBoxError(error_code, faultcode, faultstring)

    def __str__(self):
        return "Offline Message Error (%s): %s" % (self._fault, self._details)
