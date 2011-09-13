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
from papyon.profile import Presence
from papyon.transport import ServerType
from papyon.util.async import run
from papyon.util.weak import WeakSet
from papyon.event import ConversationErrorType, ContactInviteError, MessageError

__all__ = ['SwitchboardManager']

logger = logging.getLogger('papyon.protocol.switchboard_manager')

class SwitchboardHandler(object):
    def __init__(self, client, contacts, priority=99):
        self._client = client
        self._switchboard_manager = weakref.proxy(self._client._switchboard_manager)
        self.__switchboard = None
        self.__switchboard_handles = []
        self._switchboard_requested = False
        self._switchboard_priority = priority

        self.participants = set()
        self._pending_invites = set()
        self._pending_messages = []
        self._pending_handles = {}
        self._delivery_callbacks = {} # transaction_id => (callback, errback)

        for contact in contacts:
            self.__add_pending(contact)

        self._switchboard_manager.register_handler(self)

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
        self.__disconnect_switchboard()
        self.__switchboard = weakref.proxy(switchboard)
        self._switchboard_requested = False
        self.participants = set(switchboard.participants.values())

        handles = []
        handles.append(self.switchboard.connect("notify::inviting",
                lambda sb, pspec: self.__on_user_inviting_changed()))
        handles.append(self.switchboard.connect("notify::state",
                lambda sb, pspec: self.__on_switchboard_state_changed()))
        handles.append(self.switchboard.connect("user-joined",
                lambda sb, contact: self.__on_user_joined(contact)))
        handles.append(self.switchboard.connect("user-left",
                lambda sb, contact: self.__on_user_left(contact)))
        handles.append(self.switchboard.connect("user-invitation-failed",
                lambda sb, contact: self.__on_user_invitation_failed(contact)))
        handles.append(self.switchboard.connect("message-delivered",
                lambda sb, trid: self.__on_message_delivered(trid)))
        handles.append(self.switchboard.connect("message-undelivered",
                lambda sb, trid: self.__on_message_undelivered(trid)))
        self.__switchboard_handles = handles

        logger.info("Handler %s attached to switchboard %s" %
                (repr(self), switchboard.session_id))
        def process_pending_queues():
            self._process_pending_queues()
            return False
        gobject.idle_add(process_pending_queues)

    _switchboard = property(__get_switchboard, __set_switchboard)
    switchboard = property(__get_switchboard)

    # protected
    def _send_message(self, message, ack, callback=None, errback=None):
        self._pending_messages.append((message, ack, callback, errback))
        self._process_pending_queues()

    def _invite_user(self, contact):
        self.__add_pending(contact)
        self._process_pending_queues()

    def _leave(self):
        self.__disconnect_switchboard()
        self._switchboard_manager.close_handler(self)

    def __disconnect_switchboard(self):
        try:
            # try to disconnect old switchboard handles
            for handle in self.__switchboard_handles:
                self.__switchboard.disconnect(handle)
        except:
            pass
        self.__switchboard_handles = []

    # callbacks
    def _on_message_received(self, message):
        raise NotImplementedError

    def _on_message_sent(self, message):
        raise NotImplementedError

    def _on_contact_joined(self, contact):
        raise NotImplementedError

    def _on_contact_left(self, contact):
        raise NotImplementedError

    def _on_switchboard_closed(self):
        raise NotImplementedError

    def _on_closed(self):
        raise NotImplementedError

    def _on_error(self, error_type, error):
        raise NotImplementedError

    # private
    def __add_pending(self, contact):
        if contact in self._pending_invites or contact is self._client.profile:
            return
        self._pending_invites.add(contact)
        handle = contact.connect("notify::presence",
                lambda contact, pspec: self.__on_user_presence_changed(contact))
        self._pending_handles[contact] = handle

    def __remove_pending(self, contact):
        self._pending_invites.discard(contact)
        if contact in self._pending_handles:
            contact.disconnect(self._pending_handles[contact])
            del self._pending_handles[contact]

    def __on_user_inviting_changed(self):
        if not self.switchboard.inviting:
            self._process_pending_queues()

    def __on_user_joined(self, contact):
        self.participants.add(contact)
        self.__remove_pending(contact)
        self._on_contact_joined(contact)

    def __on_user_left(self, contact):
        self._on_contact_left(contact)
        self.participants.remove(contact)
        if len(self.participants) == 0:
            self.__add_pending(contact)

    def __on_user_presence_changed(self, contact):
        if (self._switchboard and self.switchboard.state == msnp.ProtocolState.OPEN) or self._switchboard_requested:
            return
        for contact in self._pending_invites:
            if contact.presence != Presence.OFFLINE:
                return
        # Switchboard was already closed and there is (almost) no chance
        # a new one will be created now.
        logger.info("All pending invites are now offline, closing handler")
        self._leave()

    def __on_switchboard_state_changed(self):
        if self._switchboard.state == msnp.ProtocolState.CLOSED:
            for contact in self._pending_invites:
                if contact.presence != Presence.OFFLINE:
                    return
            # Might be that an "appear offline" contact closed the
            # switchboard or that the switchboard has been explicitely closed
            self._leave()

    def __on_user_invitation_failed(self, contact):
        self.__remove_pending(contact)
        self._on_error(ConversationErrorType.CONTACT_INVITE,
                ContactInviteError.NOT_AVAILABLE)

    def __on_message_delivered(self, trid):
        callback, errback = self._delivery_callbacks.pop(trid, (None, None))
        run(callback)

    def __on_message_undelivered(self, trid):
        callback, errback = self._delivery_callbacks.pop(trid, (None, None))
        error = MessageError.DELIVERY_FAILED
        run(errback, error)
        self._on_error(ConversationErrorType.MESSAGE, error)

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
        for contact, handle in self._pending_handles.items():
            contact.disconnect(handle)
        self._pending_invites = set()
        self._pending_handles = dict()

        if not self.switchboard.inviting:
            for message, ack, callback, errback in self._pending_messages:
                # if ack type is FULL or MSNC, wait for ACK before calling back
                if ack in (msnp.MessageAcknowledgement.FULL,
                           msnp.MessageAcknowledgement.MSNC):
                    transaction_id = self.switchboard.send_message(message, ack)
                    self._delivery_callbacks[transaction_id] = (callback, errback)
                else:
                    transaction_id = self.switchboard.send_message(message, ack, callback)
                    self._delivery_callbacks[transaction_id] = (None, errback)

            self._pending_messages = []

    def _request_switchboard(self):
        if (self.switchboard is not None) and \
                self.switchboard.state == msnp.ProtocolState.OPEN:
            return False
        if self._switchboard_requested:
            return True
        self._switchboard_requested = True
        for participant in self.participants:
            self.__add_pending(participant)
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

        self._reset()
        self._handlers_class = set()

        self._client._protocol.connect("switchboard-invitation-received",
                self._ns_switchboard_invite)

    def _reset(self):
        self._switchboards = {}
        self._orphaned_switchboards = set()
        self._requested_switchboards = {}
        self._pending_switchboards = {}
        self._orphaned_handlers = WeakSet()

    def close(self):
        for switchboard in self._orphaned_switchboards:
            switchboard.leave()
        for switchboard in self._pending_switchboards:
            switchboard.leave()
        for switchboard in self._switchboards:
            switchboard.leave()
        self._reset()

    def register_handler_class(self, handler_class, *extra_arguments):
        self._handlers_class.add((handler_class, extra_arguments))

    def register_handler(self, handler):
        self._orphaned_handlers.add(handler)

    def request_switchboard(self, handler, priority=99):
        handler_participants = handler.total_participants
        participants = ", ".join(map(lambda c: c.account, handler_participants))
        logger.info("Requesting switchboard for participant(s) %s" % participants)

        # If the Handler was orphan, then it is no more
        self._orphaned_handlers.discard(handler)

        # Check already open switchboards
        for switchboard in self._switchboards.keys():
            switchboard_participants = set(switchboard.participants.values())
            if handler_participants == switchboard_participants:
                logger.info("Using already opened switchboard %s" %
                        switchboard.session_id)
                self._switchboards[switchboard].add(handler)
                handler._switchboard = switchboard
                return

        # Check Orphaned switchboards
        for switchboard in list(self._orphaned_switchboards):
            switchboard_participants = set(switchboard.participants.values())
            if handler_participants == switchboard_participants:
                logger.info("Using orphaned switchboard %s" %
                        switchboard.session_id)
                self._switchboards[switchboard] = set([handler]) #FIXME: WeakSet ?
                self._orphaned_switchboards.discard(switchboard)
                handler._switchboard = switchboard
                return

        # Check pending switchboards
        for switchboard, handlers in self._pending_switchboards.iteritems():
            pending_handler = handlers.pop()
            handlers.add(pending_handler)
            switchboard_participants = pending_handler.total_participants
            if handler_participants == switchboard_participants:
                self._pending_switchboards[switchboard].add(handler)
                logger.info("Using pending switchboard")
                return

        # Check switchboards being requested for same participants
        if participants in self._requested_switchboards:
            self._requested_switchboards[participants].add(handler)
            logger.info("Using already requested switchboard for same contacts")
            return

        logger.info("Requesting new switchboard")
        self._requested_switchboards[participants] = set([handler])
        self._client._protocol.request_switchboard(priority,
                (self._ns_switchboard_request_response, participants))

    def close_handler(self, handler):
        logger.info("Closing switchboard handler %s" % repr(handler))
        self._orphaned_handlers.discard(handler)
        handler._on_closed()
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

    def _ns_switchboard_request_response(self, session, participants):
        switchboard = self._build_switchboard(session)
        handlers = self._requested_switchboards.pop(participants, set())
        self._pending_switchboards[switchboard] = handlers

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
                    handler._on_switchboard_closed()
                del self._switchboards[switchboard]
            self._orphaned_switchboards.discard(switchboard)

    def _sb_message_received(self, switchboard, message):
        switchboard_participants = set(switchboard.participants.values())

        # Get current handlers for this switchboard
        if switchboard in self._switchboards.keys():
            handlers = self._switchboards[switchboard]
            handlers_class = [type(handler) for handler in handlers]
        elif switchboard in list(self._orphaned_switchboards):
            handlers = set() #FIXME: WeakSet ?
            handlers_class = []
            self._switchboards[switchboard] = handlers
        else:
            logger.warning("Message received on unknown switchboard")
            return

        # Signal message to existing handlers
        for handler in list(handlers):
            if not handler._can_handle_message(message, handler):
                continue
            handler._on_message_received(message)
            return
        # Create first handler that could handle this message
        for handler_class, extra_args in self._handlers_class:
            if not handler_class._can_handle_message(message):
                continue
            handler = handler_class.handle_message(self._client,
                    message, *extra_args)
            if handler is None:
                continue
            self._orphaned_handlers.discard(handler)
            self._orphaned_switchboards.discard(switchboard)
            handlers.add(handler)
            handler._switchboard = switchboard
            self.emit("handler-created", handler_class, handler)
            handler._on_message_received(message)
            return
