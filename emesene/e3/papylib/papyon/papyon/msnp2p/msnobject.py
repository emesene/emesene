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
from papyon.msnp2p.errors import SLPParseError
from papyon.msnp2p.SLP import *
from papyon.msnp2p.transport import *
from papyon.msnp2p.session import P2PSession
from papyon.event import EventsDispatcher
from papyon.util.decorator import rw_property

import gobject
import random

__all__ = ['MSNObjectSession']

class MSNObjectSession(P2PSession):
    def __init__(self, session_manager, peer, peer_guid, application_id,
            message=None, context=None):
        P2PSession.__init__(self, session_manager, peer, peer_guid,
                EufGuid.MSN_OBJECT, application_id, message)

        self._context = None
        if message is not None:
            try:
                self._application_id = message.body.application_id
                self._context = message.body.context.strip('\x00')
            except AttributeError:
                raise SLPParseError("Incoming INVITE without context")
        if context is not None:
            self._context = context

    @property
    def context(self):
        return self._context

    def accept(self, data_file):
        self._accept()
        self._send_data("\x00" * 4)
        self._send_data(data_file)

    def reject(self):
        self._decline(603)

    def invite(self):
        self._invite(self._context)
        return False

    def cancel(self):
        self._close()
