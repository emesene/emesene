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
import papyon.util.element_tree as ElementTree

import gobject
import base64
import logging
import random
import uuid

__all__ = ['P2PSession']

logger = logging.getLogger('papyon.msnp2p.session')

MAX_INT32 = 0x7fffffff
MAX_INT16 = 0x7fff


class P2PSession(gobject.GObject):

    __gsignals__ = {
            "accepted" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                ()),
            "completed" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),
            "progressed" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,))
    }

    def __init__(self, session_manager, peer, euf_guid="", application_id=0,
            message=None):
        gobject.GObject.__init__(self)
        self._session_manager = session_manager
        self._peer = peer

        self._euf_guid = euf_guid
        self._application_id = application_id

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
    def call_id(self):
        return self._call_id

    @property
    def peer(self):
        return self._peer

    def set_receive_data_buffer(self, buffer, total_size):
        blob = MessageBlob(self._application_id, buffer, total_size, self.id)
        self._session_manager._transport_manager.register_writable_blob(blob)

    def _invite(self, context):
        body = SLPSessionRequestBody(self._euf_guid, self._application_id,
                context, self._id)
        message = SLPRequestMessage(SLPRequestMethod.INVITE,
                "MSNMSGR:" + self._peer.account,
                to=self._peer.account,
                frm=self._session_manager._client.profile.account,
                branch=self._branch,
                cseq=self._cseq,
                call_id=self._call_id)
        message.body = body
        self._send_p2p_data(message)

    def _transreq(self):
        self._cseq = 0
        body = SLPTransferRequestBody(self._id, 0, 1)
        message = SLPRequestMessage(SLPRequestMethod.INVITE,
                "MSNMSGR:" + self._peer.account,
                to=self._peer.account,
                frm=self._session_manager._client.profile.account,
                branch=self._branch,
                cseq=self._cseq,
                call_id=self._call_id)
        message.body = body
        self._send_p2p_data(message)

    def _respond(self, status_code):
        body = SLPSessionRequestBody(session_id=self._id, capabilities_flags=None,
                s_channel_state=None)
        self._cseq += 1
        response = SLPResponseMessage(status_code,
            to=self._peer.account,
            frm=self._session_manager._client.profile.account,
            cseq=self._cseq,
            branch=self._branch,
            call_id=self._call_id)
        response.body = body
        self._send_p2p_data(response)

    def _respond_transreq(self, transreq, status, body):
        self._cseq += 1
        response = SLPResponseMessage(status,
            to=self._peer.account,
            frm=self._session_manager._client.profile.account,
            cseq=self._cseq,
            branch=transreq.branch,
            call_id=self._call_id)
        response.body = body
        self._send_p2p_data(response)

    def _accept_transreq(self, transreq, bridge, listening, nonce, local_ip,
            local_port, extern_ip, extern_port):
        body = SLPTransferResponseBody(bridge, listening, nonce, [local_ip],
                local_port, [extern_ip], extern_port, self._id, 0, 1)
        self._respond_transreq(transreq, 200, body)

    def _decline_transreq(self, transreq):
        body = SLPTransferResponseBody(session_id=self._id)
        self._respond_transreq(transreq, 603, body)

    def _close(self, context=None):
        body = SLPSessionCloseBody(context=context, session_id=self._id,
                s_channel_state=0)
        self._cseq = 0
        self._branch = "{%s}" % uuid.uuid4()
        message = SLPRequestMessage(SLPRequestMethod.BYE,
                "MSNMSGR:" + self._peer.account,
                to=self._peer.account,
                frm=self._session_manager._client.profile.account,
                branch=self._branch,
                cseq=self._cseq,
                call_id=self._call_id)
        message.body = body
        self._send_p2p_data(message)
        self._dispose()

    def _dispose(self):
        self._session_manager._unregister_session(self)

    def _send_p2p_data(self, data_or_file, is_file=False):
        if isinstance(data_or_file, SLPMessage):
            session_id = 0
            data = str(data_or_file)
            total_size = len(data)
        else:
            session_id = self._id
            data = data_or_file
            total_size = None

        blob = MessageBlob(self._application_id,
                data, total_size, session_id, None, is_file)
        self._session_manager._transport_manager.send(self.peer, blob)

    def _on_blob_sent(self, blob):
        if blob.session_id == 0:
            # FIXME: handle the signaling correctly
            return
        data = blob.read_data()
        if blob.total_size == 4 and data == ('\x00' * 4):
            self._on_data_preparation_blob_sent(blob)
        else:
            self._on_data_blob_sent(blob)

    def _on_blob_received(self, blob):
        data = blob.read_data()

        if blob.session_id == 0:
            message = SLPMessage.build(data)
            if isinstance(message, SLPRequestMessage):
                if isinstance(message.body, SLPSessionRequestBody):
                    self._on_invite_received(message)
                elif isinstance(message.body, SLPTransferRequestBody):
                    self._decline_transreq(message)
                elif isinstance(message.body, SLPSessionCloseBody):
                    self._on_bye_received(message)
                else:
                    print "Unhandled signaling blob :", message
            elif isinstance(message, SLPResponseMessage):
                if message.status is 200:
                    self._on_session_accepted()
                    self.emit("accepted")
                elif message.status is 603:
                    self._on_session_rejected(message)
                else:
                    print "Unhandled response blob :", message
            return

        if blob.total_size == 4 and data == ('\x00' * 4):
            self._on_data_preparation_blob_received(blob)
        else:
            self._on_data_blob_received(blob)

    def _on_data_chunk_transferred(self, chunk):
        if chunk.has_progressed():
            self.emit("progressed", len(chunk.body))

    def _on_data_preparation_blob_received(self, blob):
        pass

    def _on_data_preparation_blob_sent(self, blob):
        pass

    def _on_data_blob_sent(self, blob):
        logger.info("Session data transfer completed")
        blob.data.seek(0, 0)
        self.emit("completed", blob.data)

    def _on_data_blob_received(self, blob):
        logger.info("Session data transfer completed")
        blob.data.seek(0, 0)
        self.emit("completed", blob.data)
        self._close()

    # Methods to implement in different P2P applications

    def _on_invite_received(self, message):
        pass

    def _on_bye_received(self, message):
        pass

    def _on_session_accepted(self):
        pass

    def _on_session_rejected(self, message):
        pass

gobject.type_register(P2PSession)
