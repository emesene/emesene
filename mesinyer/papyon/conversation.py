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

"""Conversation

This module contains the classes needed to have a conversation with a
contact."""

import msnp
import p2p
from switchboard_manager import SwitchboardClient
from papyon.event import EventsDispatcher
from papyon.profile import NetworkID

import logging
import gobject
from urllib import quote, unquote

__all__ = ['Conversation', 'ConversationInterface', 'ConversationMessage', 'TextFormat']

logger = logging.getLogger('papyon.conversation')


def Conversation(client, contacts):
    """Factory function used to create the appropriate conversation with the
    given contacts.

    This is the method you need to use to start a conversation with both MSN
    users and Yahoo! users.
        @attention: you can only talk to one Yahoo! contact at a time, and you
        cannot have multi-user conversations with both MSN and Yahoo! contacts.

        @param contacts: The list of contacts to invite into the conversation
        @type contacts: [L{Contact<papyon.profile.Contact>}, ...]

        @returns: a Conversation object implementing L{ConversationInterface<papyon.conversation.ConversationInterface>}
        @rtype: L{ConversationInterface<papyon.conversation.ConversationInterface>}
    """
    msn_contacts = set([contact for contact in contacts \
            if contact.network_id == NetworkID.MSN])
    external_contacts = set(contacts) - msn_contacts

    if len(external_contacts) == 0:
        return SwitchboardConversation(client, contacts)
    elif len(msn_contacts) != 0:
        raise NotImplementedError("The protocol doesn't allow mixing " \
                "contacts from different networks in a single conversation")
    elif len(external_contacts) > 1:
        raise NotImplementedError("The protocol doesn't allow having " \
                "more than one external contact in a conversation")
    elif len(external_contacts) == 1:
        return ExternalNetworkConversation(client, contacts)


class ConversationInterface(object):
    """Interface implemented by all the Conversation objects, a Conversation
    object allows the user to communicate with one or more peers"""

    def send_text_message(self, message):
        """Send a message to all persons in this conversation.

            @param message: the message to send to the users on this conversation
            @type message: L{Contact<papyon.profile.Contact>}"""
        raise NotImplementedError

    def send_nudge(self):
        """Sends a nudge to the contacts on this conversation."""
        raise NotImplementedError

    def send_typing_notification(self):
        """Sends an user typing notification to the contacts on this
        conversation."""
        raise NotImplementedError

    def invite_user(self, contact):
        """Request a contact to join in the conversation.

            @param contact: the contact to invite.
            @type contact: L{Contact<papyon.profile.Contact>}"""
        raise NotImplementedError

    def leave(self):
        """Leave the conversation."""
        raise NotImplementedError


class ConversationMessage(object):
    """A Conversation message sent or received

        @ivar display_name: the display name to show for the sender of this message
        @type display_name: utf-8 encoded string

        @ivar content: the content of the message
        @type content: utf-8 encoded string

        @ivar formatting: the formatting for this message
        @type formatting: L{TextFormat<papyon.conversation.TextFormat>}

        @ivar msn_objects: a dictionary mapping smileys
            to an L{MSNObject<papyon.p2p.MSNObject>}
        @type msn_objects: {smiley: string => L{MSNObject<papyon.p2p.MSNObject>}}
    """
    def __init__(self, content, formatting=None, msn_objects={}):
        """Initializer

            @param content: the content of the message
            @type content: utf-8 encoded string

            @param formatting: the formatting for this message
            @type formatting: L{TextFormat<papyon.conversation.TextFormat>}

            @param msn_objects: a dictionary mapping smileys
                to an L{MSNObject<papyon.p2p.MSNObject>}
            @type msn_objects: {smiley: string => L{MSNObject<papyon.p2p.MSNObject>}}"""
        self.display_name = None
        self.content = content
        self.formatting = formatting
        self.msn_objects = msn_objects

class TextFormat(object):

    DEFAULT_FONT = 'MS Sans Serif'

    # effects
    NO_EFFECT = 0
    BOLD = 1
    ITALIC = 2
    UNDERLINE = 4
    STRIKETHROUGH = 8

    # charset
    ANSI_CHARSET = '0'
    DEFAULT_CHARSET = '1'
    SYMBOL_CHARSET = '2'
    MAC_CHARSETLT = '4d'
    SHIFTJIS_CHARSET = '80'
    HANGEUL_CHARSET = '81'
    JOHAB_CHARSET = '82'
    GB2312_CHARSET = '86'
    CHINESEBIG5_CHARSET = '88'
    GREEK_CHARSET = 'a1'
    TURKISH_CHARSET = 'a2'
    VIETNAMESE_CHARSET = 'a3'
    HEBREW_CHARSET = 'b1'
    ARABIC_CHARSET = 'b2'
    BALTIC_CHARSET = 'ba'
    RUSSIAN_CHARSET_DEFAULT = 'cc'
    THAI_CHARSET = 'de'
    EASTEUROPE_CHARSET = 'ee'
    OEM_DEFAULT = 'ff'

    # family
    FF_DONTCARE = 0
    FF_ROMAN = 1
    FF_SWISS = 2
    FF_MODERN = 3
    FF_SCRIPT = 4
    FF_DECORATIVE = 5

    # pitch
    DEFAULT_PITCH = 0
    FIXED_PITCH = 1
    VARIABLE_PITCH = 2

    @staticmethod
    def parse(format):
        text_format = TextFormat()
        text_format.__parse(format)
        return text_format

    @property
    def font(self):
        return self._font

    @property
    def style(self):
        return self._style

    @property
    def color(self):
        return self._color

    @property
    def right_alignment(self):
        return self._right_alignment

    @property
    def charset(self):
        return self._charset

    @property
    def pitch(self):
        return self._pitch

    @property
    def family(self):
        return self._family

    def __init__(self, font=DEFAULT_FONT, style=NO_EFFECT, color='0',
                 charset=DEFAULT_CHARSET, family=FF_DONTCARE,
                 pitch=DEFAULT_PITCH, right_alignment=False):
        self._font = font
        self._style = style
        self._color = color
        self._charset = charset
        self._pitch = pitch
        self._family = family
        self._right_alignment = right_alignment

    def __parse(self, format):
        for property in format.split(';'):
            key, value =  [p.strip(' \t|').upper() \
                    for p in property.split('=', 1)]
            if key == 'FN':
                # Font
                self._font = unquote(value)
            elif key == 'EF':
                # Effects
                if 'B' in value: self._style |= TextFormat.BOLD
                if 'I' in value: self._style |= TextFormat.ITALIC
                if 'U' in value: self._style |= TextFormat.UNDERLINE
                if 'S' in value: self._style |= TextFormat.STRIKETHROUGH
            elif key == 'CO':
                # Color
                value = value.zfill(6)
                self._color = ''.join((value[4:6], value[2:4], value[0:2]))
            elif key == 'CS':
                # Charset
                self._charset = value
            elif key == 'PF':
                # Family and pitch
                value = value.zfill(2)
                self._family = int(value[0])
                self._pitch = int(value[1])
            elif key == 'RL':
                # Right alignment
                if value == '1': self._right_alignement = True

    def __str__(self):
        style = ''
        if self._style & TextFormat.BOLD == TextFormat.BOLD:
            style += 'B'
        if self._style & TextFormat.ITALIC == TextFormat.ITALIC:
            style += 'I'
        if self._style & TextFormat.UNDERLINE == TextFormat.UNDERLINE:
            style += 'U'
        if self._style & TextFormat.STRIKETHROUGH == TextFormat.STRIKETHROUGH:
            style += 'S'

        color = '%s%s%s' % (self._color[4:6], self._color[2:4], self._color[0:2])

        format = 'FN=%s; EF=%s; CO=%s; CS=%s; PF=%d%d'  % (quote(self._font),
                                                           style, color,
                                                           self._charset,
                                                           self._family,
                                                           self._pitch)
        if self._right_alignment: format += '; RL=1'

        return format

    def __repr__(self):
        return __str__(self)


class AbstractConversation(ConversationInterface, EventsDispatcher):
    def __init__(self, client):
        self._client = client
        ConversationInterface.__init__(self)
        EventsDispatcher.__init__(self)

        self.__last_received_msn_objects = {}

    def send_text_message(self, message):
        if len(message.msn_objects) > 0:
            body = []
            for alias, msn_object in message.msn_objects.iteritems():
                self._client._msn_object_store.publish(msn_object)
                body.append(alias.encode("utf-8"))
                body.append(str(msn_object))
                # FIXME : we need to distinguish animemoticon and emoticons
                # and send the related msn objects in separated messages
            self._send_message(("text/x-mms-animemoticon",), '\t'.join(body))

        content_type = ("text/plain","utf-8")
        body = message.content.encode("utf-8")
        ack = msnp.MessageAcknowledgement.HALF
        headers = {}
        if message.formatting is not None:
            headers["X-MMS-IM-Format"] = str(message.formatting)

        self._send_message(content_type, body, headers, ack)

    def send_nudge(self):
        content_type = "text/x-msnmsgr-datacast"
        body = "ID: 1\r\n\r\n".encode('UTF-8') #FIXME: we need to figure out the datacast objects :D
        ack = msnp.MessageAcknowledgement.NONE
        self._send_message(content_type, body, ack=ack)

    def send_typing_notification(self):
        content_type = "text/x-msmsgscontrol"
        body = "\r\n\r\n".encode('UTF-8')
        headers = { "TypingUser" : self._client.profile.account.encode('UTF_8') }
        ack = msnp.MessageAcknowledgement.NONE
        self._send_message(content_type, body, headers, ack)

    def invite_user(self, contact):
        raise NotImplementedError

    def leave(self):
        raise NotImplementedError

    def _send_message(self, content_type, body, headers={},
            ack=msnp.MessageAcknowledgement.HALF):
        raise NotImplementedError

    def _on_contact_joined(self, contact):
        self._dispatch("on_conversation_user_joined", contact)

    def _on_contact_left(self, contact):
        self._dispatch("on_conversation_user_left", contact)

    def _on_message_received(self, message):
        sender = message.sender
        message_type = message.content_type[0]
        message_encoding = message.content_type[1]
        try:
            message_formatting = message.get_header('X-MMS-IM-Format')
            if not message_formatting:
                message_formatting = '='
        except KeyError:
            message_formatting = '='

        if message_type == 'text/plain':
            msg = ConversationMessage(unicode(message.body, message_encoding),
                    TextFormat.parse(message_formatting),
                    self.__last_received_msn_objects)
            try:
                display_name = message.get_header('P4-Context')
            except KeyError:
                display_name = sender.display_name
            msg.display_name = display_name
            self._dispatch("on_conversation_message_received", sender, msg)
            self.__last_received_msn_objects = {}
        elif message_type == 'text/x-msmsgscontrol':
            self._dispatch("on_conversation_user_typing", sender)
        elif message_type in ['text/x-mms-emoticon',
                              'text/x-mms-animemoticon']:
            msn_objects = {}
            parts = message.body.split('\t')
            logger.debug(parts)
            for i in [i for i in range(len(parts)) if not i % 2]:
                if parts[i] == '': break
                msn_objects[parts[i]] = p2p.MSNObject.parse(self._client,
                        parts[i+1])
            self.__last_received_msn_objects = msn_objects
        elif message_type == 'text/x-msnmsgr-datacast' and \
                message.body.strip() == "ID: 1":
            self._dispatch("on_conversation_nudge_received", sender)

    def _on_message_sent(self, message):
        pass

    def _on_error(self, error_type, error):
        self._dispatch("on_conversation_error", error_type, error)


class ExternalNetworkConversation(AbstractConversation):
    def __init__(self, client, contacts):
        AbstractConversation.__init__(self, client)
        self.participants = set(contacts)
        client._register_external_conversation(self)
        gobject.idle_add(self._open)

    def _open(self):
        for contact in self.participants:
            self._on_contact_joined(contact)
        return False

    def invite_user(self, contact):
        raise NotImplementedError("The protocol doesn't allow multiuser " \
                "conversations for external contacts")

    def leave(self):
        self._client._unregister_external_conversation(self)

    def _send_message(self, content_type, body, headers={},
            ack=msnp.MessageAcknowledgement.HALF):
        if content_type[0]  in ['text/x-mms-emoticon',
                                'text/x-mms-animemoticon']:
            return
        message = msnp.Message(self._client.profile)
        for key, value in headers.iteritems():
            message.add_header(key, value)
        message.content_type = content_type
        message.body = body
        for contact in self.participants:
            self._client._protocol.\
                    send_unmanaged_message(contact, message)


class SwitchboardConversation(AbstractConversation, SwitchboardClient):
    def __init__(self, client, contacts):
        SwitchboardClient.__init__(self, client, contacts, priority=0)
        AbstractConversation.__init__(self, client)

    @staticmethod
    def _can_handle_message(message, switchboard_client=None):
        content_type = message.content_type[0]
        if switchboard_client is None:
            return content_type in ('text/plain', 'text/x-msnmsgr-datacast')
        # FIXME : we need to not filter those 'text/x-mms-emoticon', 'text/x-mms-animemoticon'
        return content_type in ('text/plain', 'text/x-msmsgscontrol',
                'text/x-msnmsgr-datacast', 'text/x-mms-emoticon',
                'text/x-mms-animemoticon')

    def invite_user(self, contact):
        """Request a contact to join in the conversation.

            @param contact: the contact to invite.
            @type contact: L{profile.Contact}"""
        SwitchboardClient._invite_user(self, contact)

    def leave(self):
        """Leave the conversation."""
        SwitchboardClient._leave(self)

    def _send_message(self, content_type, body, headers={},
            ack=msnp.MessageAcknowledgement.HALF):
        SwitchboardClient._send_message(self, content_type, body, headers, ack)
