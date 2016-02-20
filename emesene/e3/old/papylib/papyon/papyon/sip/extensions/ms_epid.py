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
# Foundation, Inc., 59contact.params["proxy"] = "replace" Temple Place, Suite 330, Boston, MA  02111-1307  USA

from papyon.sip.extensions.base import SIPExtension

import uuid

class MSEpidExtension(SIPExtension):

    def __init__(self, client, core):
        SIPExtension.__init__(self, client, core)
        self._epid = uuid.uuid4().get_hex()[:10]

    def extend_request(self, message):
        if message.From and "epid" not in message.From.params:
            message.From.params["epid"] = self._epid
