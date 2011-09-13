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

from papyon.sip.message import SIPResponse, SIPRequest

class SIPExtension(object):

    def __init__(self, client, core):
        self._client = client
        self._core = core

    def extend(self, message):
        if type(message) is SIPResponse:
            self.extend_response(message)
        elif type(message) is SIPRequest:
            self.extend_request(message)

    def extend_response(self, reponse):
        pass

    def extend_request(self, request):
        pass
