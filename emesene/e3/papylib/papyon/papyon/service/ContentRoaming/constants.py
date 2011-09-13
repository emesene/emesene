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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from papyon.errors import ClientError, ClientErrorType

__all__ = ["ContentRoamingError", "ContentRoamingState"]

class ContentRoamingError(ClientError):
    UNKNOWN = 0

    ITEM_ALREADY_EXISTS = 1
    ITEM_DOES_NOT_EXIST = 2

    def __init__(self, code, fault="", details=""):
        ClientError.__init__(self, ClientErrorType.CONTENT_ROAMING, code)
        self._fault = fault
        self._details = details

    @staticmethod
    def get_detailled_error(fault):
        if fault.detail is not None:
            errorcode = fault.detail.findtext("./stv1:errorcode")
            errorstring = fault.detail.findtext("./stv1:errorstring")
        else:
            errorcode = fault.faultcode
            errorstring = fault.faultstring
        return errorcode, errorstring

    @staticmethod
    def from_fault(fault):
        errorcode, errorstring = ContentRoamingError.get_detailled_error(fault)
        code = ContentRoamingError.UNKNOWN

        if errorcode == "ItemDoesNotExist":
            code = ContentRoamingError.ITEM_ALREADY_EXISTS
        elif errorcode == "ItemDoesNotExist":
            code = ContentRoamingError.ITEM_DOES_NOT_EXIST

        return ContentRoamingError(code, errorcode, errorstring)

    def __str__(self):
        return "Content Roaming Error (%s): %s" % (self._fault, self._details)

class ContentRoamingState(object):
    """Content roaming service synchronization state.

    The service is said to be synchronized when it
    matches the stuff stored on the server."""

    NOT_SYNCHRONIZED = 0
    """The service is not synchronized yet"""
    SYNCHRONIZING = 1
    """The service is being synchronized"""
    SYNCHRONIZED = 2
    """The service is already synchronized"""

