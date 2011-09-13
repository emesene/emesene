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

from papyon.util import Timer

import gobject
import logger

__all__ = ['SIPRegistration']

logger = logging.getLogger('papyon.sip.registration')

class SIPRegistration(gobject.GObject):

    __gsignals__ = {
        'registered': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ([])),
        'unregistered': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ([])),
        'failed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ([]))
    }

    def __init__(self, client, core):
        gobject.GObject.__init__(self)
        self._client = client
        self._core = core
        self._state = "NEW"
        self._sso = client._sso
        self._src = None
        self._request = None
        self._pending_unregister = False
        self._tokens = {}

        self._tag = None
        self._call_id = None
        self._cseq = None

    @property
    def registered(self):
        return (self._state == "REGISTERED")

    def register(self):
        if self._state in ("REGISTERING", "REGISTERED", "CANCELLED"):
            return
        self._state = "REGISTERING"
        self._do_register(None, None)

    def unregister(self):
        if self._state in ("NEW", "UNREGISTERING", "UNREGISTERED", "CANCELLED"):
            return
        elif self._state == "REGISTERING":
            if self._request is None:
                self._state = "CANCELLED"
                self.emit("unregistered")
            else:
                self._pending_unregister = True
            return

        self._state = "UNREGISTERING"
        self._pending_unregister = False
        if self._src is not None:
            gobject.source_remove(self._src)
        self._src = None
        self._do_unregister(None, None)

    def _send_register(self, timeout, auth):
        self._request = self._core.register(self._tag, self._call_id,
                self._cseq, timeout, auth)
        self._tag = self._request.From.tag
        self._call_id = self._request.call_id
        self._cseq = self._request.cseq.number + 1

    @RequireSecurityTokens(LiveService.MESSENGER_SECURE)
    def _do_register(self, callback, errback):
        # Check if state changed while requesting security token
        if self._state != "REGISTERING":
            return
        auth = "msmsgs:RPS_%s" % self._tokens[LiveService.MESSENGER_SECURE]
        auth = base64.b64encode(auth).replace("\n", "")
        self._send_register(900, auth)

    @RequireSecurityTokens(LiveService.MESSENGER_SECURE)
    def _do_unregister(self, callback, errback):
        auth = "%s:%s" % (self._account, self._tokens[LiveService.MESSENGER_SECURE])
        auth = base64.encodestring(auth).replace("\n", "")
        self._send_register(0, auth)

    def _on_expire(self):
        self.register()
        return False

    def handle_response(self, response):
        if self._state == "UNREGISTERING":
            self._state = "UNREGISTERED"
            self.emit("unregistered")
        elif self._state != "REGISTERING":
            return # strange !?
        elif response.status is 200:
            self._state = "REGISTERED"
            self.emit("registered")
            timeout = int(response.get_header("Expires", 30))
            self._src = gobject.timeout_add_seconds(timeout, self._on_expire)
            if self._pending_unregister:
                self.unregister()
        else:
            self._state = "UNREGISTERED"
            self.emit("failed")
