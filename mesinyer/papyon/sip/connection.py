# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2009 Collabora Ltd.
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

from papyon.sip.call import SIPCall, SIPRegistration
from papyon.sip.constants import *
from papyon.sip.message import SIPRequest

import gobject
import logging

__all__ = ['SIPConnection', 'SIPTunneledConnection']

logger = logging.getLogger('papyon.sip.connection')


class SIPBaseConnection(gobject.GObject):

    __gsignals__ = {
        'invite-received': (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            (object,)),
        'disconnecting': (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            ()),
        'disconnected': (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            ())
    }

    def __init__(self, client, transport):
        gobject.GObject.__init__(self)
        self._calls = {}
        self._client = client
        self._transport = transport
        self._transport.connect("message-received", self.on_message_received)

    @property
    def transport(self):
        return self._transport

    def create_call(self, peer=None, invite=None, id=None):
        call = SIPCall(self, self._client, peer, invite, id)
        self.add_call(call)
        return call

    def add_call(self, call):
        self._calls[call.id] = call

    def remove_call(self, call):
        if call.id in self._calls:
            del self._calls[call.id]

    def get_call(self, callid):
        return self._calls.get(callid, None)

    def send(self, message, registration=False):
        message.sent = True
        self._transport.send(message)

    def on_message_received(self, parser, message):
        callid = message.get_header("Call-ID")
        call = self.get_call(callid)
        if call is None:
            if isinstance(message, SIPRequest) and message.code == "INVITE":
                logger.info("Call invitation received")
                call = self.create_call(invite=message, id=callid)
                self.emit("invite-received", call)
            else:
                logger.info("Message with invalid call-id received")
                if self.registered:
                    call = SIPCall(self, self._client, invite=message, id=callid)
                    response = call.build_response(message, 481)
                    call.send(response) # call/transaction does not exist
                return
        call.on_message_received(message)


class SIPConnection(SIPBaseConnection):

    def __init__(self, client, transport):
        SIPBaseConnection.__init__(self, client, transport)
        self._tokens = {}
        self._msg_queue = []
        self._registration = SIPRegistration(self, self._client)
        self._registration.connect("registered", self.on_registration_success)
        self._registration.connect("unregistered", self.on_unregistration_success)
        self.add_call(self._registration)

    @property
    def registered(self):
        return self._registration.registered

    @property
    def tunneled(self):
        return False

    def register(self):
        self._registration.register()

    def unregister(self):
        self.emit("disconnecting")
        self._msg_queue = []
        self._registration.unregister()

    def send(self, message, registration=False):
        if self.registered or registration:
            message.sent = True
            self._transport.send(message)
        else:
            self._msg_queue.append(message)
            self.register()

    def remove_call(self, call):
        SIPBaseConnection.remove_call(self, call)
        if len(self._calls) == 1:
            self.unregister()

    def on_registration_success(self, registration):
        while len(self._msg_queue) > 0:
            msg = self._msg_queue.pop(0)
            if not msg.cancelled:
                self.send(msg)

    def on_unregistration_success(self, registration):
        self.emit("disconnected")


class SIPTunneledConnection(SIPBaseConnection):

    @property
    def registered(self):
        return True

    @property
    def tunneled(self):
        return True
