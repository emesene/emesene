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

from papyon.errors import ClientError, ClientErrorType

__all__ = ['SpacesError']

class SpacesError(ClientError):
    "Spaces related errors"

    UNKNOWN = 0
    "Generic errors"

    def __init__(self, code, fault="", details=""):
        ClientError.__init__(self, ClientErrorType.SPACES, code)
        self._fault = fault
        self._details = details

    @staticmethod
    def from_fault(fault):
        return SpacesError(SpacesError.UNKNOWN, fault.faultcode,
                fault.faultstring)

    def __str__(self):
        return "Spaces Error (%s): %s" % (self._fault, self._details)
