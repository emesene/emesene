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

from papyon.msnp2p.constants import SLPContentType, SLPRequestMethod
from papyon.msnp2p.transport import *
from papyon.msnp2p.SLP import *
from papyon.util.parsing import parse_account

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
        self._transport_manager.connect("data-received",
                lambda tr, peer, guid, session_id, data:
                    self._on_data_received(peer, guid, session_id, data))
        self._transport_manager.connect("data-sent",
                lambda tr, peer, guid, session_id, data:
                    self._on_data_sent(peer, guid, session_id, data))
        self._transport_manager.connect("data-transferred",
                lambda tr, peer, guid, session_id, size:
                    self._on_data_transferred(peer, guid, session_id, size))
        self._transport_manager.connect("slp-message-received",
                lambda tr, peer, guid, msg:
                    self._on_slp_message_received(peer, guid, msg))

    def register_handler(self, handler_class):
        self._handlers.append(handler_class)

    def close(self):
        for session in self._sessions.values():
            session._close()
        self._transport_manager.close()

    def _register_session(self, session):
        self._sessions[session.id] = session
        self._transport_manager.remove_from_blacklist(session.peer,
                session.peer_guid, session.id)

    def _unregister_session(self, session):
        del self._sessions[session.id]
        self._transport_manager.add_to_blacklist(session.peer,
                session.peer_guid, session.id)

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

    def _find_contact(self, account):
        account, guid = parse_account(account)
        peer = self._client.address_book.search_or_build_contact(
                account, papyon.profile.NetworkID.MSN)

        return peer, guid

    def _on_data_received(self, peer, peer_guid, session_id, data):
        session = self._get_session(session_id)
        if session is None:
            # This means that we received a data packet for an unknown session
            # We must RESET the session just like the official client does
            # TODO send a TLP
            logger.error("Received data packet for unknown session %s" % session_id)
            return
        session._on_data_received(data)

    def _on_data_sent(self, peer, peer_guid, session_id, data):
        session = self._get_session(session_id)
        if session is None:
            return
        session._on_data_sent(data)

    def _on_data_transferred(self, peer, peer_guid, session_id, size):
        session = self._get_session(session_id)
        if session is None:
            return
        session._on_data_transferred(size)

    def _on_slp_message_received(self, peer, peer_guid, message):
        session_id = message.body.session_id
        # Backward compatible with older clients that use the call-id
        # for responses
        if session_id == 0:
            session = self._search_session_by_call(message.call_id)
        else:
            session = self._get_session(session_id)

        # The session could not be found, create a new one if necessary
        if session is None:
            # Make sure the SLP has a session_id, otherwise, it means it's invite
            # if it's a signaling SLP and the call-id could not be matched to
            # an existing session
            if session_id == 0:
                # TODO send a 500 internal error
                logger.error("Session_id == 0")
                return

            # If there was no session then create one only if it's an INVITE
            if isinstance(message, SLPRequestMessage) and \
                    isinstance(message.body, SLPSessionRequestBody) and \
                    message.method == SLPRequestMethod.INVITE:
                try:
                    # Find the contact we received the message from
                    peer, guid = self._find_contact(message.frm)
                    for handler in self._handlers:
                        if handler._can_handle_message(message):
                            session = handler._handle_message(peer, guid, message)
                            if session is not None:
                                break
                    if session is None:
                        logger.error("No handler could handle euf-guid %s" % (message.body.euf_guid))
                        return
                except Exception, err:
                    #TODO: answer with a 603 Decline ?
                    logger.exception(err)
                    logger.error("Could not handle SLP invite message")
                    return None
            else:
                logger.warning('Received initial blob with SessionID=0 and non INVITE SLP data')
                #TODO: answer with a 500 Internal Error
                return None

        session._on_slp_message_received(message)

gobject.type_register(P2PSessionManager)
