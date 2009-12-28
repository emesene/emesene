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

from papyon.msnp2p.transport import *
from papyon.msnp2p.exceptions import *
from papyon.msnp2p.SLP import *
from papyon.msnp2p.constants import SLPContentType, SLPRequestMethod

import papyon.profile

import gobject
import weakref
import logging

__all__ = ['P2PSessionManager']

logger = logging.getLogger('papyon.msnp2p.session_manager')

class P2PSessionManager(gobject.GObject):
    __gsignals__ = {
            "incoming-session" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,))
    }

    def __init__(self, client):
        """Initializer"""
        gobject.GObject.__init__(self)

        self._client = client
        self._sessions = weakref.WeakValueDictionary() # session_id => session
        self._handlers = []
        self._transport_manager = P2PTransportManager(self._client)
        self._transport_manager.connect("blob-received",
                lambda tr, blob: self._on_blob_received(blob))
        self._transport_manager.connect("blob-sent",
                lambda tr, blob: self._on_blob_sent(blob))
        self._transport_manager.connect("chunk-transferred",
                lambda tr, chunk: self._on_chunk_transferred(chunk))

    def register_handler(self, handler_class):
        self._handlers.append(handler_class)

    def _register_session(self, session):
        self._sessions[session.id] = session

    def _unregister_session(self, session):
        del self._sessions[session.id]

    def _on_chunk_transferred(self, chunk):
        session_id = chunk.header.session_id
        if session_id == 0:
            return
        session = self._get_session(session_id)
        if session is None:
            return
        session._on_data_chunk_transferred(chunk)

    def _get_session(self, session_id):
        if session_id in self._sessions:
            return self._sessions[session_id]
        else:
            return None

    def _search_session_by_call(self, call_id):
        for session in self._sessions.itervalues():
            if session.call_id == call_id:
                return session
        return None

    def _blob_to_session(self, blob):
        session_id = blob.session_id

        # Check to see if it's a signaling message
        if session_id == 0:
            slp_data = blob.read_data()
            try:
                message = SLPMessage.build(slp_data)
            except ParseError:
                print slp_data
                logger.warning('Received blob with SessionID=0 and non SLP data')
                raise SLPError("Non SLP data for blob with null sessionID")
            session_id = message.body.session_id

        # Backward compatible with older clients that use the call-id
        # for responses
        if session_id == 0:
            return self._search_session_by_call(message.call_id)

        return self._get_session(session_id)

    def _on_blob_received(self, blob):
        try:
            session = self._blob_to_session(blob)
        except SLPError:
            # If the blob has a null session id but a badly formed SLP
            # Then we should do nothing. The official client doesn't answer.
            # We can't send a '500 Internal Error' response since we can't
            # parse the SLP, so we don't know who to send it to, or the call-id, etc...
            return

        # The session could not be found, create a new one if necessary
        if session is None:
            if blob.session_id != 0:
                # This means that we received a data packet for an unknown session
                # We must RESET the session just like the official client does
                # TODO send a TLP
                logger.error("SLPSessionError")
                return

            # No need to 'try', if it was invalid, we would have received an SLPError
            slp_data = blob.read_data()
            message = SLPMessage.build(slp_data)
            session_id = message.body.session_id

            # Make sure the SLP has a session_id, otherwise, it means it's invite
            # if it's a signaling SLP and the call-id could not be matched to
            # an existing session
            if session_id == 0:
                # TODO send a 500 internal error
                logger.error("Session_id == 0")
                return

            # If there was no session then create one only if it's an INVITE
            if isinstance(message, SLPRequestMessage) and \
                    message.method == SLPRequestMethod.INVITE:
                if isinstance(message.body, SLPSessionRequestBody):
                    # Find the contact we received the message from
                    peer = self._client.address_book.search_or_build_contact(
                            message.frm, papyon.profile.NetworkID.MSN)
                    try:
                        for handler in self._handlers:
                            if handler._can_handle_message(message):
                                session = handler._handle_message(peer, message)
                                if session is not None:
                                    self._register_session(session)
                                    break
                        if session is None:
                            logger.error("No handler could handle euf-guid %s" % (message.body.euf_guid))
                            return
                    except SLPError:
                        #TODO: answer with a 603 Decline ?
                        logger.error("SLPError")
                        return None
                elif isinstance(message.body, SLPTransferRequestBody):
                    session = self._sessions[session_id]
                else:
                    return None
            else:
                logger.warning('Received initial blob with SessionID=0 and non INVITE SLP data')
                #TODO: answer with a 500 Internal Error
                return None

        session._on_blob_received(blob)

    def _on_blob_sent(self, blob):
        session = None
        try:
            session = self._blob_to_session(blob)
        except SLPError, e:
            # Something is fishy.. we shouldn't have to send anything abnormal..
            logger.warning("Sent a bad message : %s" % (e))
            session = None
        except SLPSessionError, e:
            # May happen when we close the session
            pass

        if session is None:
            return
        session._on_blob_sent(blob)

gobject.type_register(P2PSessionManager)
