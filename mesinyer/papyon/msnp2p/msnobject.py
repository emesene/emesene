# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2007 Ali Sabil <ali.sabil@gmail.com>
# Copyright (C) 2008 Richard Spiers <richard.spiers@gmail.com>
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

from papyon.msnp2p.constants import *
from papyon.msnp2p.SLP import *
from papyon.msnp2p.transport import *
from papyon.msnp2p.exceptions import *
from papyon.msnp2p.session import P2PSession
from papyon.event import EventsDispatcher
from papyon.util.decorator import rw_property

import gobject
import random

__all__ = ['MSNObjectSession']

class MSNObjectSession(P2PSession):
    def __init__(self, session_manager, peer, application_id, message=None):
        P2PSession.__init__(self, session_manager, peer,
                EufGuid.MSN_OBJECT, application_id, message)

        if message is not None:
            self._application_id = message.body.application_id
            try:
                self._context = message.body.context.strip('\x00')
            except AttributeError:
                raise SLPError("Incoming INVITE without context")

    def accept(self, data_file):
        self._respond(200)
        self._send_p2p_data("\x00" * 4)
        self._send_p2p_data(data_file)

    def reject(self):
        self._respond(603)

    def invite(self, context):
        self._invite(context)
        return False
