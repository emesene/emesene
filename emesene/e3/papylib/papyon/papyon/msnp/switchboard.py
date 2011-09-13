# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2005-2007 Ali Sabil <ali.sabil@gmail.com>
# Copyright (C) 2005-2006 Ole André Vadla Ravnås <oleavr@gmail.com>
# Copyright (C) 2007 Johann Prieur <johann.prieur@gmail.com>
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

"""Switchboard protocol Implementation
Implements the protocol used to communicate with the Switchboard Server."""

from base import BaseProtocol
from constants import ProtocolError, ProtocolState
from message import Message
import papyon.profile

from papyon.util.async import run
from papyon.util.parsing import build_account, parse_account

import logging
import urllib
import gobject

__all__ = ['SwitchboardProtocol']

logger = logging.getLogger('papyon.protocol.switchboard')


class SwitchboardProtocol(BaseProtocol):
    """Protocol used to communicate with the Switchboard Server

        @undocumented: do_get_property, do_set_property
        @group Handlers: _handle_*, _default_handler, _error_handler

        @ivar _state: the current protocol state
        @type _state: L{ProtocolState}"""
    __gsignals__ = {
            "message-received": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),

            "message-sent": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),

            "message-delivered": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),

            "message-undelivered": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),

            "user-joined": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),

            "user-left": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),

            "user-invitation-failed": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,))}

    __gproperties__ = {
            "inviting":  (gobject.TYPE_BOOLEAN,
                "Inviting",
                "True if an invite was sent, and the contact didn't join yet",
                False,
                gobject.PARAM_READABLE)
            }

    def __init__(self, client, transport, session_id, key=None, proxies={}):
        """Initializer

            @param client: the Client instance

            @param transport: The transport to use to speak the protocol
            @type transport: L{transport.BaseTransport}

            @param session_id: the session to join if any
            @type session_id: string

            @param key: the key used to authenticate to server when connecting
            @type key: string

            @param proxies: a dictonary mapping the proxy type to a
                L{gnet.proxy.ProxyInfos} instance
            @type proxies: {type: string, proxy:L{gnet.proxy.ProxyInfos}}
        """
        BaseProtocol.__init__(self, client, transport, proxies)
        self.participants = {}
        self.end_points = {}
        self.inactivity_timer_id = 0
        self.keepalive_timer_id = 0
        self.__session_id = session_id
        self.__key = key
        self.__state = ProtocolState.CLOSED
        self.__inviting = False

        self.__invitations = {}

        logger.info("New switchboard session %s" % session_id)
        client.profile.connect("end-point-added", self._on_end_point_added)
        if client.keepalive_conversations:
            self.keepalive_timer_id = gobject.timeout_add_seconds(8, self._keepalive_conversation)

    # Properties ------------------------------------------------------------
    @property
    def session_id(self):
        return self.__session_id

    def __get_state(self):
        return self.__state
    def __set_state(self, state):
        self.__state = state
        self.notify("state")
    state = property(__get_state)
    _state = property(__get_state, __set_state)

    def __get_inviting(self):
        return self.__inviting
    def __set_inviting(self, value):
        if self.__inviting != value:
            self.__inviting = value
            self.notify("inviting")
    inviting = property(__get_inviting)
    _inviting = property(__get_inviting, __set_inviting)

    def do_get_property(self, pspec):
        if pspec.name == "state":
            return self.__state
        elif pspec.name == "inviting":
            return self.__inviting
        else:
            raise AttributeError, "unknown property %s" % pspec.name

    def do_set_property(self, pspec, value):
        raise AttributeError, "unknown property %s" % pspec.name

    # Public API -------------------------------------------------------------
    def invite_user(self, contact):
        """Invite user to join in the conversation

            @param contact: the contact to invite
            @type contact: L{profile.Contact}"""
        assert(self.state == ProtocolState.OPEN)
        if contact in self.__invitations.values():
            return
        self.__invitations[self._transport.transaction_id] = contact
        self._inviting = True
        self._send_command('CAL', (contact.account,))

    def send_message(self, message, ack, callback=None, errback=None):
        """Send a message to all contacts in this switchboard

            @param message: the message to send
            @type message: L{message.Message}"""
        assert(self.state == ProtocolState.OPEN)
        # TODO: FIXME: MSNP18 doesn't reply with ACKs?
        self._update_switchboard_timeout()
        message.add_header('MIME-Version', '1.0')
        return self._send_command('MSG', (ack,), message, True,
                (self._on_message_sent, message, callback), errback)

    def leave(self, inactivity=False):
        """Leave the conversation"""
        if self.state != ProtocolState.OPEN:
            return
        if self.inactivity_timer_id:
            gobject.source_remove(self.inactivity_timer_id)
            self.inactivity_timer_id = 0
        if self.keepalive_timer_id:
            gobject.source_remove(self.keepalive_timer_id)
            self.keepalive_timer_id = 0
        if inactivity:
            logger.info("Switchboard timed out. Going to leave it.")
        logger.info("Leaving switchboard %s" % self.__session_id)
        self._send_command('OUT')
        self._state = ProtocolState.CLOSING

    # Handlers ---------------------------------------------------------------
    # --------- Authentication -----------------------------------------------
    def _handle_ANS(self, command):
        if command.arguments[0] == 'OK':
            self._state = ProtocolState.SYNCHRONIZED
            self._state = ProtocolState.OPEN
        else:
            self._state = ProtocolState.AUTHENTICATED
            self._state = ProtocolState.SYNCHRONIZING

    def _handle_USR(self, command):
        self._state = ProtocolState.AUTHENTICATED
        self._state = ProtocolState.SYNCHRONIZING
        self._state = ProtocolState.SYNCHRONIZED
        self._state = ProtocolState.OPEN
        if self._client.protocol_version >= 16:
            self.invite_user(self._client.profile)

    def _handle_OUT(self, command):
        pass

    # --------- Invitation ---------------------------------------------------
    def __search_account(self, account, display_name):
        """Search account in address book and make sure it's not ourself."""
        contact = self._client.address_book.search_or_build_contact(account,
                papyon.profile.NetworkID.MSN, display_name)
        return contact

    def __discard_invitation(self, account):
        for trid, contact in self.__invitations.items():
            if contact.account.lower() == account:
                del self.__invitations[trid]
                return
            
    def __participant_join(self, account, guid, display_name, client_id):
        if guid is not None:
            places = self.end_points.setdefault(account, [])
            places.append(guid)
            return # wait for the command without GUID
        if account == self._client.profile.account.lower():
            return # ignore our own user
        if account in self.participants:
            return # ignore duplicate users
        contact = self.__search_account(account, display_name)
        contact._server_property_changed("client-capabilities", client_id)
        self.participants[account] = contact
        self.emit("user-joined", contact)

    def __participant_left(self, account, guid):
        if guid is not None:
            places = self.end_points.setdefault(account, [])
            places.remove(guid)
            return # wait for the command without GUID to remove from participants
        if account == self._client.profile.account.lower():
            return # ignore our own user
        participant = self.participants.pop(account)
        self.emit("user-left", participant)

    def _handle_IRO(self, command):
        account, guid = parse_account(command.arguments[2])
        display_name = urllib.unquote(command.arguments[3])
        client_id = command.arguments[4]
        self.__participant_join(account, guid, display_name, client_id)

    def _handle_CAL(self, command):
        pass

    def _handle_JOI(self, command):
        account, guid = parse_account(command.arguments[0])
        display_name = urllib.unquote(command.arguments[1])
        client_id = command.arguments[2]
        self.__participant_join(account, guid, display_name, client_id)
        if guid is None:
            self.__discard_invitation(account)
            if len(self.__invitations) == 0:
                self._inviting = False

    def _handle_BYE(self, command):
        account, guid = parse_account(command.arguments[0])
        self.__participant_left(account, guid)
        end_points = self.end_points.get(self._client.profile.account.lower(), [])
        if len(self.participants) == 0 and len(end_points) == 0:
            self.leave()

    # --------- Messenging ---------------------------------------------------
    def _handle_MSG(self, command):
        account = command.arguments[0]
        display_name = urllib.unquote(command.arguments[1])
        contact = self.__search_account(account, display_name)
        message = Message(contact, command.payload)
        self._update_switchboard_timeout()
        self.emit("message-received", message)

    def _handle_ACK(self, command):
        # TODO: FIXME: MSNP18 doesn't reply with ACKs?
        self._update_switchboard_timeout()
        self.emit("message-delivered", command.transaction_id)

    def _handle_NAK(self, command):
        self.emit("message-undelivered", command.transaction_id)

    def _error_handler(self, error):
        """Handles errors

            @param error: an error command object
            @type error: L{command.Command}
        """
        if error.name in ('208', '215', '216', '217', '713'):
            try:
                contact = self.__invitations[error.transaction_id]
                self.emit("user-invitation-failed", contact)
                del self.__invitations[error.transaction_id]
                if len(self.__invitations) == 0:
                    self._inviting = False
            except:
                pass
        else:
            logger.error('Notification got error :' + unicode(error))

    def _update_switchboard_timeout(self):
        if self.inactivity_timer_id:
            gobject.source_remove(self.inactivity_timer_id)
            self.inactivity_timer_id = 0
        if len(self.participants) == 1 and not self.keepalive_timer_id:
            self.inactivity_timer_id = gobject.timeout_add_seconds(60, self.leave, True)

    # callbacks --------------------------------------------------------------
    def _connect_cb(self, transport):
        self._state = ProtocolState.OPENING
        account = self._client.profile.account
        if self._client.protocol_version >= 16:
            account = build_account(self._client.profile.account,
                    self._client.machine_guid)
        if self.__key is not None:
            arguments = (account, self.__key, self.__session_id)
            self._send_command('ANS', arguments)
        else:
            arguments = (account, self.__session_id)
            self._send_command('USR', arguments)
        self._state = ProtocolState.AUTHENTICATING

    def _disconnect_cb(self, transport, reason):
        logger.info("Disconnected (%s)" % self.__session_id)
        self._state = ProtocolState.CLOSED

    def _on_message_sent(self, message, user_callback):
        run(user_callback)
        self.emit("message-sent", message)

    def _on_end_point_added(self, profile, end_point):
        if self.state != ProtocolState.OPEN:
            return
        logger.info("New end point connected, re-invite local user")
        self.invite_user(profile)

    def _keepalive_conversation(self):
        if self.state != ProtocolState.OPEN:
            return True
        message = Message()
        message.add_header('Content-Type', 'text/x-keep-alive')
        self._send_command('MSG', 'N', message, True)
        return True

