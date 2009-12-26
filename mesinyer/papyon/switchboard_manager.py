# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2005-2007 Ali Sabil <ali.sabil@gmail.com>
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

"""Switchboard Manager
The switchboard manager is responsible for managing all the switchboards in
use, it simplifies the complexity of the switchboard crack."""

import logging
import gobject
import weakref

import papyon.msnp as msnp
from papyon.transport import ServerType
from papyon.util.weak import WeakSet
from papyon.event import ConversationErrorType, ContactInviteError, MessageError

__all__ = ['SwitchboardManager']

logger = logging.getLogger('papyon.protocol.switchboard_manager')

class SwitchboardClient(object):
    def __init__(self, client, contacts, priority=99):
        self._client = client
        self._switchboard_manager = weakref.proxy(self._client._switchboard_manager)
        self.__switchboard = None
        self._switchboard_requested = False
        self._switchboard_priority = priority

        self._pending_invites = set(contacts)
        self._pending_messages = []

        if self._client.protocol_version >= 16:
            self._pending_invites.add(self._client.profile)

        self.participants = set()
        self._process_pending_queues()

    @staticmethod
    def _can_handle_message(message, switchboard_client=None):
        return False

    # properties
    @property
    def total_participants(self):
        return self.participants | self._pending_invites

    def __get_switchboard(self):
        return self.__switchboard
    def __set_switchboard(self, switchboard):
        self.__switchboard = weakref.proxy(switchboard)
        self._switchboard_requested = False
        self.participants = set(switchboard.participants.values())

        self.switchboard.connect("notify::inviting",
                lambda sb, pspec: self.__on_user_inviting_changed())
        self.switchboard.connect("user-joined",
                lambda sb, contact: self.__on_user_joined(contact))
        self.switchboard.connect("user-left",
                lambda sb, contact: self.__on_user_left(contact))
        self.switchboard.connect("user-invitation-failed",
                lambda sb, contact: self.__on_user_invitation_failed(contact))
        self.switchboard.connect("message-undelivered",
                lambda sb, command: self.__on_message_undelivered(command))
        logger.info("New switchboard attached")
        def process_pending_queues():
            self._process_pending_queues()
            return False
        gobject.idle_add(process_pending_queues)

    _switchboard = property(__get_switchboard, __set_switchboard)
    switchboard = property(__get_switchboard)

    # protected
    def _send_message(self, content_type, body, headers={},
            ack=msnp.MessageAcknowledgement.HALF, callback=None, cb_args=()):
        message = msnp.Message(self._client.profile)
        message.add_header('MIME-Version', '1.0')
        message.content_type = content_type
        for key, value in headers.iteritems():
            message.add_header(key, value)
        message.body = body

        self._pending_messages.append((message, ack, callback, cb_args))
        self._process_pending_queues()

    def _invite_user(self, contact):
        self._pending_invites.add(contact)
        self._process_pending_queues()

    def _leave(self):
        self._switchboard_manager.close_handler(self)

    # callbacks
    def _on_message_received(self, message):
        raise NotImplementedError

    def _on_message_sent(self, message):
        raise NotImplementedError

    def _on_contact_joined(self, contact):
        raise NotImplementedError

    def _on_contact_left(self, contact):
        raise NotImplementedError

    def _on_error(self, error_type, error):
        raise NotImplementedError

    # private
    def __on_user_inviting_changed(self):
        if not self.switchboard.inviting:
            self._process_pending_queues()

    def __on_user_joined(self, contact):
        self.participants.add(contact)
        self._pending_invites.discard(contact)
        self._on_contact_joined(contact)

    def __on_user_left(self, contact):
        self._on_contact_left(contact)
        self.participants.remove(contact)
        if len(self.participants) == 0:
            self._pending_invites.add(contact)
            try:
                self._switchboard.leave()
            except:
                pass

    def __on_user_invitation_failed(self, contact):
        self._pending_invites.discard(contact)
        self._on_error(ConversationErrorType.CONTACT_INVITE,
                ContactInviteError.NOT_AVAILABLE)

    def __on_message_undelivered(self, command):
        self._on_error(ConversationErrorType.MESSAGE,
                MessageError.DELIVERY_FAILED)

    # Helper functions
    def _process_pending_queues(self):
        if len(self._pending_invites) == 0 and \
                len(self._pending_messages) == 0:
            return

        if self._request_switchboard():
            return

        for contact in self._pending_invites:
            if contact not in self.participants:
                self.switchboard.invite_user(contact)
        self._pending_invites = set()

        if not self.switchboard.inviting:
            for message, ack, callback, cb_args in self._pending_messages:
                self.switchboard.send_message(message, ack, callback, cb_args)
            self._pending_messages = []

    def _request_switchboard(self):
        if (self.switchboard is not None) and \
                self.switchboard.state == msnp.ProtocolState.OPEN:
            return False
        if self._switchboard_requested:
            return True
        logger.info("requesting new switchboard")
        self._switchboard_requested = True
        self._pending_invites |= self.participants
        self.participants = set()
        self._switchboard_manager.request_switchboard(self, self._switchboard_priority) # may set the switchboard immediatly
        return self._switchboard_requested


class SwitchboardManager(gobject.GObject):
    """Switchboard management

        @undocumented: do_get_property, do_set_property
        @group Handlers: _handle_*, _default_handler, _error_handler"""
    __gsignals__ = {
            "handler-created": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object, object))
            }

    def __init__(self, client):
        """Initializer

            @param client: the main Client instance"""
        gobject.GObject.__init__(self)
        self._client = weakref.proxy(client)

        self._handlers_class = set()
        self._orphaned_handlers = WeakSet()
        self._switchboards = {}
        self._orphaned_switchboards = set()
        self._pending_switchboards = {}

        self._client._protocol.connect("switchboard-invitation-received",
                self._ns_switchboard_invite)

    def close(self):
        for switchboard in self._orphaned_switchboards:
            switchboard.leave()
        for switchboard in self._pending_switchboards:
            switchboard.leave()
        for switchboard in self._switchboards:
            switchboard.leave()

    def register_handler(self, handler_class, *extra_arguments):
        self._handlers_class.add((handler_class, extra_arguments))

    def request_switchboard(self, handler, priority=99):
        handler_participants = handler.total_participants

        # If the Handler was orphan, then it is no more
        self._orphaned_handlers.discard(handler)

        # Check already open switchboards
        for switchboard in self._switchboards.keys():
            switchboard_participants = set(switchboard.participants.values())
            if handler_participants == switchboard_participants:
                self._switchboards[switchboard].add(handler)
                handler._switchboard = switchboard
                return

        # Check Orphaned switchboards
        for switchboard in list(self._orphaned_switchboards):
            switchboard_participants = set(switchboard.participants.values())
            if handler_participants == switchboard_participants:
                self._switchboards[switchboard] = set([handler]) #FIXME: WeakSet ?
                self._orphaned_switchboards.discard(switchboard)
                handler._switchboard = switchboard
                return

        # Check being requested switchboards
        for switchboard, handlers in self._pending_switchboards.iteritems():
            pending_handler = handlers.pop()
            handlers.add(pending_handler)
            switchboard_participants = pending_handler.total_participants
            if handler_participants == switchboard_participants:
                self._pending_switchboards[switchboard].add(handler)
                return

        self._client._protocol.\
                request_switchboard(priority, self._ns_switchboard_request_response, handler)

    def close_handler(self, handler):
        self._orphaned_handlers.discard(handler)
        for switchboard in self._switchboards.keys():
            handlers = self._switchboards[switchboard]
            handlers.discard(handler)
            if len(handlers) == 0:
                switchboard.leave()
                del self._switchboards[switchboard]
                self._orphaned_switchboards.add(switchboard)

        for switchboard in self._pending_switchboards.keys():
            handlers = self._pending_switchboards[switchboard]
            handlers.discard(handler)
            if len(handlers) == 0:
                del self._pending_switchboards[switchboard]
                self._orphaned_switchboards.add(switchboard)

    def _ns_switchboard_request_response(self, session, handler):
        switchboard = self._build_switchboard(session)
        self._pending_switchboards[switchboard] = set([handler]) #FIXME: WeakSet ?

    def _ns_switchboard_invite(self, protocol, session, inviter):
        switchboard = self._build_switchboard(session)
        self._orphaned_switchboards.add(switchboard)

    def _build_switchboard(self, session):
        server, session_id, key = session
        client = self._client
        proxies = client._proxies

        transport_class = client._transport_class
        transport = transport_class(server, ServerType.SWITCHBOARD, proxies)
        switchboard = msnp.SwitchboardProtocol(client, transport,
                session_id, key, proxies)
        switchboard.connect("notify::state", self._sb_state_changed)
        switchboard.connect("message-received", self._sb_message_received)
        transport.establish_connection()
        return switchboard

    def _sb_state_changed(self, switchboard, param_spec):
        state = switchboard.state
        if state == msnp.ProtocolState.OPEN:
            self._switchboards[switchboard] = set() #FIXME: WeakSet ?

            # Requested switchboards
            if switchboard in self._pending_switchboards:
                handlers = self._pending_switchboards[switchboard]
                while True:
                    try:
                        handler = handlers.pop()
                        self._switchboards[switchboard].add(handler)
                        handler._switchboard = switchboard
                    except KeyError:
                        break
                del self._pending_switchboards[switchboard]

            # Orphaned Handlers
            for handler in list(self._orphaned_handlers):
                switchboard_participants = set(switchboard.participants.values())
                handler_participants = handler.total_participants
                if handler_participants == switchboard_participants:
                    self._switchboards[switchboard].add(handler)
                    self._orphaned_handlers.discard(handler)
                    self._orphaned_switchboards.discard(switchboard)
                    handler._switchboard = switchboard

            # no one wants it, it is an orphan
            if len(self._switchboards[switchboard]) == 0:
                del self._switchboards[switchboard]
                self._orphaned_switchboards.add(switchboard)

        elif state == msnp.ProtocolState.CLOSED:
            if switchboard in self._switchboards.keys():
                for handler in self._switchboards[switchboard]:
                    self._orphaned_handlers.add(handler)
                del self._switchboards[switchboard]
            self._orphaned_switchboards.discard(switchboard)

    def _sb_message_received(self, switchboard, message):
        switchboard_participants = set(switchboard.participants.values())
        if switchboard in self._switchboards.keys():
            handlers = self._switchboards[switchboard]
            handlers_class = [type(handler) for handler in handlers]
            for handler in list(handlers):
                if not handler._can_handle_message(message, handler):
                    continue
                handler._on_message_received(message)
            for handler_class, extra_args in self._handlers_class:
                if handler_class in handlers_class:
                    continue
                if not handler_class._can_handle_message(message):
                    continue
                handler = handler_class(self._client, (), *extra_args)
                handlers.add(handler)
                handler._switchboard = switchboard
                self.emit("handler-created", handler_class, handler)
                handler._on_message_received(message)

        if switchboard in list(self._orphaned_switchboards):
            for handler_class, extra_args in self._handlers_class:
                if not handler_class._can_handle_message(message):
                    continue
                handler = handler_class(self._client, (), *extra_args)
                self._switchboards[switchboard] = set([handler]) #FIXME: WeakSet ?
                self._orphaned_switchboards.discard(switchboard)
                handler._switchboard = switchboard
                self.emit("handler-created", handler_class, handler)
                handler._on_message_received(message)
