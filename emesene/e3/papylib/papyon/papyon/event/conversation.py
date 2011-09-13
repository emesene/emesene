# -*- coding: utf-8 -*-
#
# Copyright (C) 2007  Ali Sabil <ali.sabil@gmail.com>
# Copyright (C) 2007  Johann Prieur <johann.prieur@gmail.com>
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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

"""Conversation event interfaces

The interfaces defined in this module allow receiving notification events
from a L{Conversation<papyon.conversation.ConversationInterface>} object."""

from papyon.event import BaseEventInterface

__all__ = ["ConversationEventInterface", "ConversationErrorType",
        "ContactInviteError", "MessageError"]


class ConversationErrorType(object):
    """L{Client<papyon.Client>} error types
        @see: L{ClientEventInterface.on_client_error}"""

    NETWORK = 0
    "Network related errors"
    AUTHENTICATION = 1
    "Authentication related errors"
    PROTOCOL = 2
    "Protocol related errors"
    CONTACT_INVITE = 3
    "Contact invitation related errors"
    MESSAGE = 4
    "Message sending related errors"


class ContactInviteError(object):
    "Contact invitation related errors"
    UNKNOWN = 0

    NOT_AVAILABLE = 1


class MessageError(object):
    "Message related errors"
    UNKNOWN = 0

    DELIVERY_FAILED = 1


class ConversationEventInterface(BaseEventInterface):
    """Interfaces allowing the user to get notified about events
    from a L{Conversation<papyon.conversation.ConversationInterface>} object."""

    def __init__(self, conversation):
        """Initializer
            @param conversation: the conversation we want to be notified for its events
            @type conversation: L{Conversation<papyon.conversation.ConversationInterface>}"""
        BaseEventInterface.__init__(self, conversation)

    def on_conversation_state_changed(self, state):
        """@attention: not implemented"""
        pass

    def on_conversation_error(self, type, error):
        """Called when an error occurs in the L{Client<papyon.conversation>}.

            @param type: the error type
            @type type: L{ClientErrorType}

            @param error: the error code
            @type error: L{NetworkError} or L{AuthenticationError} or
                L{ProtocolError} or L{ContactInviteError} or
                L{MessageError}"""
        pass

    def on_conversation_user_joined(self, contact):
        """Called when an user joins the conversation.
            @param contact: the contact whose presence changed
            @type contact: L{Contact<papyon.profile.Contact>}"""
        pass

    def on_conversation_user_left(self, contact):
        """Called when an user leaved the conversation.
            @param contact: the contact whose presence changed
            @type contact: L{Contact<papyon.profile.Contact>}"""
        pass

    def on_conversation_user_typing(self, contact):
        """Called when an user is typing.
            @param contact: the contact whose presence changed
            @type contact: L{Contact<papyon.profile.Contact>}"""
        pass

    def on_conversation_message_received(self, sender, message):
        """Called when an user sends a message.
            @param sender: the contact who sent the message
            @type sender: L{Contact<papyon.profile.Contact>}

            @param message: the message
            @type message: L{ConversationMessage<papyon.conversation.ConversationMessage>}"""
        pass
    
    def on_conversation_nudge_received(self, sender):
        """Called when an user sends a nudge.
            @param sender: the contact who sent the nudge
            @type sender: L{Contact<papyon.profile.Contact>}"""
        pass

    def on_conversation_message_sent(self, message):
        """Called when a message is sent.
            @param message: the message
            @type message: L{ConversationMessage<papyon.conversation.ConversationMessage>}
            @note doesn't guarantee the message has been delivered."""
        pass

    def on_conversation_nudge_sent(self):
        """Called when a nudge is sent."""
        pass

    def on_conversation_closed(self):
        """Called when the conversation is closed."""
        pass
