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

from papyon.msnp.constants import *
from papyon.sip.call import SIPCall
from papyon.sip.core import SIPCore

import gobject
import logging
import uuid

logger = logging.getLogger('papyon.sip.call_manager')

class SIPCallManager(gobject.GObject):

    __gsignals__ = {
        'incoming-call': (
            gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            (object,))
    }

    def __init__(self, client):
        gobject.GObject.__init__(self)
        self._client = client
        self._core = SIPCore(self._client)
        self._core.connect("invite-received", self._on_invite_received)
        self._core.connect("invite-answered", self._on_invite_answered)
        self._core.connect("cancel-received", self._on_cancel_received)

        self._calls = {} # Call-ID => call, handle_id

    ### Public API -----------------------------------------------------------

    def create_call(self, peer):
        #FIXME check if busy
        id = self._generate_id()
        call = SIPCall(self._client, self._core, id, peer=peer)
        self._add_call(call)
        return call

    def close(self):
        for call, handle_id in self._calls.values():
            call.end()
            self._remove_call(call)

    ### Protected API --------------------------------------------------------

    def find_call(self, message):
        return self._calls.get(message.call_id, (None, None))[0]

    ### Private API ----------------------------------------------------------

    def _add_call(self, call):
        handle = call.connect("ended", self._remove_call)
        self._calls[call.id] = (call, handle)

    def _remove_call(self, call):
        call, handle = self._calls.pop(call.id)
        call.disconnect(handle)

    def _on_invite_received(self, core, invite):
        #FIXME check if busy
        id = invite.call_id
        if id in self._calls:
            logger.warning("Call with same id (%s) already exists" % id)
            return

        call = SIPCall(self._client, core, id, invite=invite)
        if not call.handle_invite_request(invite):
            logger.warning("Call ended before we could signal it (%s)" % id)
            return

        self._add_call(call)
        self.emit("incoming-call", call)

    def _on_invite_answered(self, core, response):
        call_id = response.call_id
        call, handle = self._calls.get(call_id, (None, None))
        if not call:
            logger.warning("No call matches with INVITE answer (%s)" % call_id)
            return
        call.handle_invite_response(response)

    def _on_cancel_received(self, core, request):
        call_id = request.call_id
        if not call_id in self._calls:
            logger.warning("No call matches with CANCEL request (%s)" % call_id)
            return
        call, handle = self._calls.get(call_id)
        call.handle_cancel_request(request)

    def _generate_id(self):
        id = None
        while True:
            id = uuid.uuid4().get_hex()
            if id not in self._calls: break
        return id
