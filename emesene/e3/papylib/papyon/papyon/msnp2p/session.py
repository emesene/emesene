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

from papyon.event import EventsDispatcher
from papyon.msnp2p.constants import *
from papyon.msnp2p.SLP import *
from papyon.msnp2p.transport import *
from papyon.util.parsing import build_account
from papyon.util.timer import Timer
import papyon.util.element_tree as ElementTree

import gobject
import base64
import logging
import random
import uuid
import os

__all__ = ['P2PSession']

logger = logging.getLogger('papyon.msnp2p.session')

MAX_INT32 = 0x7fffffff
MAX_INT16 = 0x7fff


class P2PSession(gobject.GObject, EventsDispatcher, Timer):

    __gsignals__ = {
            "accepted" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                ()),
            "rejected" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                ()),
            "completed" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),
            "progressed" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),
            "canceled" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                ()),
            "disposed" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                ())
    }

    def __init__(self, session_manager, peer, peer_guid=None, euf_guid="",
            application_id=0, message=None):
        gobject.GObject.__init__(self)
        EventsDispatcher.__init__(self)
        Timer.__init__(self)
        self._session_manager = session_manager
        self._transport_manager = session_manager._transport_manager
        self._client = session_manager._client
        self._peer = peer
        self._peer_guid = peer_guid

        self._euf_guid = euf_guid
        self._application_id = application_id
        self._completed = False

        self._version = 1
        if self._client.profile.client_id.supports_p2pv2 and \
                peer.client_capabilities.supports_p2pv2:
            self._version = 2

        if message is not None:
            self._id = message.body.session_id
            self._call_id = message.call_id
            self._cseq = message.cseq
            self._branch = message.branch
            self._incoming = True
        else:
            self._id =  self._generate_id()
            self._call_id = "{%s}" % uuid.uuid4()
            self._cseq = 0
            self._branch = "{%s}" % uuid.uuid4()
            self._incoming = False

        self._session_manager._register_session(self)

    def _generate_id(self, max=MAX_INT32):
        """
        Returns a random ID.

        @return: a random integer between 1000 and sys.maxint
        @rtype: integer
        """
        return random.randint(1000, max)

    @property
    def id(self):
        return self._id

    @property
    def incoming(self):
        return self._incoming

    @property
    def completed(self):
        return self._completed

    @property
    def call_id(self):
        return self._call_id

    @property
    def peer(self):
        return self._peer

    @property
    def peer_guid(self):
        return self._peer_guid

    @property
    def local_id(self):
        if self._version >= 2:
            return build_account(self._client.profile.account,
                    self._client.machine_guid)
        return self._client.profile.account

    @property
    def remote_id(self):
        if self._version >= 2:
            return build_account(self._peer.account, self._peer_guid)
        return self._peer.account

    def set_receive_data_buffer(self, buffer, size):
        self._transport_manager.register_data_buffer(self.peer,
                self.peer_guid, self.id, buffer, size)

    def _invite(self, context):
        body = SLPSessionRequestBody(self._euf_guid, self._application_id,
                context, self._id)
        message = SLPRequestMessage(SLPRequestMethod.INVITE,
                "MSNMSGR:" + self.remote_id,
                to=self.remote_id,
                frm=self.local_id,
                branch=self._branch,
                cseq=self._cseq,
                call_id=self._call_id)
        message.body = body
        self._send_slp_message(message)
        self.start_timeout("response", 60)

    def _transreq(self):
        self._cseq = 0
        body = SLPTransportRequestBody(self._id, 0, 1)
        message = SLPRequestMessage(SLPRequestMethod.INVITE,
                "MSNMSGR:" + self.remote_id,
                to=self.remote_id,
                frm=self.local_id,
                branch=self._branch,
                cseq=self._cseq,
                call_id=self._call_id)
        message.body = body
        self._send_slp_message(message)

    def _respond(self, status_code):
        body = SLPSessionRequestBody(session_id=self._id, capabilities_flags=None,
                s_channel_state=None)
        self._cseq += 1
        response = SLPResponseMessage(status_code,
            to=self.remote_id,
            frm=self.local_id,
            cseq=self._cseq,
            branch=self._branch,
            call_id=self._call_id)
        response.body = body
        self._send_slp_message(response)

        # close other end points so we are the only one answering
        self._close_end_points(status_code)

    def _accept(self):
        self._respond(200)

    def _decline(self, status_code):
        self._respond(status_code)
        self._dispose()

    def _respond_transreq(self, transreq, status, body):
        self._cseq += 1
        response = SLPResponseMessage(status,
            to=self.remote_id,
            frm=self.local_id,
            cseq=self._cseq,
            branch=transreq.branch,
            call_id=self._call_id)
        response.body = body
        self._send_slp_message(response)

    def _accept_transreq(self, transreq, bridge, listening, nonce, local_ip,
            local_port, extern_ip, extern_port):
        body = SLPTransportResponseBody(bridge, listening, nonce, [local_ip],
                local_port, [extern_ip], extern_port, self._id, 0, 1)
        self._respond_transreq(transreq, 200, body)

    def _decline_transreq(self, transreq):
        body = SLPTransportResponseBody(session_id=self._id)
        self._respond_transreq(transreq, 603, body)
        self._dispose()

    def _close(self, context=None, reason=None):
        body = SLPSessionCloseBody(context=context, session_id=self._id,
                reason=reason, s_channel_state=0)
        self._cseq = 0
        self._branch = "{%s}" % uuid.uuid4()
        message = SLPRequestMessage(SLPRequestMethod.BYE,
                "MSNMSGR:" + self.remote_id,
                to=self.remote_id,
                frm=self.local_id,
                branch=self._branch,
                cseq=self._cseq,
                call_id=self._call_id)
        message.body = body
        self._send_slp_message(message)
        self._dispose()

    def _close_end_points(self, status):
        """Send BYE to other end points; this client already answered.
            @param status: response we sent to the peer"""
        if len(self._peer.end_points) > 0:
            return # if the peer supports MPOP, let him do the work

        for end_point in self._client.profile.end_points.values():
            if end_point.id == self._client.machine_guid:
                continue
            self._close_end_point(end_point, status)

    def _close_end_point(self, end_point, status):
        reason = (status, self._client.machine_guid)
        body = SLPSessionCloseBody(session_id=self._id, reason=reason,
                s_channel_state=0)
        self._cseq = 0
        self._branch = "{%s}" % uuid.uuid4()
        message = SLPRequestMessage(SLPRequestMethod.BYE,
                "MSNMSGR:" + self._client.profile.account,
                to=self._client.profile.account,
                frm=self._peer.account,
                branch=self._branch,
                cseq=self._cseq,
                call_id=self._call_id,
                on_behalf=self._peer.account)
        message.body = body
        self._transport_manager.send_slp_message(self._client.profile,
                end_point.id, self._application_id, message)

    def _dispose(self):
        logger.info("Session %s disposed" % self._id)
        self.stop_all_timeout()
        self._session_manager._transport_manager.cleanup(self.peer,
                self.peer_guid, self._id)
        self._session_manager._unregister_session(self)
        self._emit("disposed")

    def _send_slp_message(self, message):
        self._transport_manager.send_slp_message(self.peer, self.peer_guid,
                self._application_id, message)

    def _send_data(self, data):
        self._transport_manager.send_data(self.peer, self.peer_guid,
                self._application_id, self._id, data)

    def _on_slp_message_received(self, message):
        if isinstance(message, SLPRequestMessage):
            if isinstance(message.body, SLPSessionRequestBody):
                self._on_invite_received(message)
            elif isinstance(message.body, SLPSessionCloseBody):
                self._on_bye_received(message)
            else:
                print "Unhandled signaling blob :", message
        elif isinstance(message, SLPResponseMessage):
            if isinstance(message.body, SLPSessionRequestBody):
                self.stop_timeout("response")
                if message.status == 200:
                    self._emit("accepted")
                    self._on_session_accepted()
                elif message.status == 603:
                    self._emit("rejected")
                    self._on_session_rejected(message)
            else:
                print "Unhandled response blob :", message

    def _on_data_sent(self, data):
        logger.info("Session data transfer completed")
        data.seek(0, os.SEEK_SET)
        self._completed = True
        self._emit("completed", data)
        self.start_timeout("bye", 5)

    def _on_data_received(self, data):
        logger.info("Session data transfer completed")
        data.seek(0, os.SEEK_SET)
        self._completed = True
        self._emit("completed", data)
        self._close()

    def _on_data_transferred(self, size):
        self._emit("progressed", size)

    def on_response_timeout(self):
        self._close()

    def on_bye_timeout(self):
        self._dispose()

    # Methods to implement in different P2P applications

    def _on_invite_received(self, message):
        pass

    def _on_bye_received(self, message):
        self._dispose()

    def _on_session_accepted(self):
        pass

    def _on_session_rejected(self, message):
        self._dispose()

    # Utilities methods

    def _emit(self, signal, *args):
        self._dispatch("on_session_%s" % signal, *args)
        self.emit(signal, *args)

gobject.type_register(P2PSession)
