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
#

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

class OfflineMessagesBoxError(object):
    "Offline IM related errors"
    UNKNOWN = 0
    AUTHENTICATION_FAILED = 1
    SYSTEM_UNAVAILABLE = 2
    SENDER_THROTTLE_LIMIT_EXCEEDED = 3
    

