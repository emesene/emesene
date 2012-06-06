# -*- coding: utf-8 -*-
#
# papylib - an emesene extension for papyon
#
# Copyright (C) 2009-2010 Riccardo (C10uD) <c10ud.dev@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
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

from e3.base.Event import Event

import papyon.event
import papyon.gnet.errors

import logging
log = logging.getLogger('papylib.Events')

PROFILE_URL = "http://profile.live.com/details/Edit/Pic"

class ClientEvents(papyon.event.ClientEventInterface):
    def on_client_state_changed(self, state):
        if state == papyon.event.ClientState.CLOSED:
            #self._client.quit()
            pass
        elif state == papyon.event.ClientState.OPEN:
            # move event-login-succeed after content roaming stuff is retrieved?            
            self._client.session.add_event(Event.EVENT_LOGIN_SUCCEED)
            self._client.set_initial_infos()
            self._client._fill_contact_list(self._client.address_book)
        else:
            #if state == papyon.event.ClientState.CONNECTING:
                #message = 'Connecting...'
            #elif state == papyon.event.ClientState.CONNECTED:
                #message = 'Connected'
            if state == papyon.event.ClientState.AUTHENTICATING:
                message = 'Authenticating...'
            #elif state == papyon.event.ClientState.AUTHENTICATED:
                #message = 'Authenticated'
            elif state == papyon.event.ClientState.SYNCHRONIZING:
                message = 'Downloading your contact list,\n'+\
                          '             please wait...'
            #elif state == papyon.event.ClientState.SYNCHRONIZED:
                #message = 'Contact list downloaded successfully.\nHappy Chatting'
            else:
                return
            self._client.session.add_event(Event.EVENT_LOGIN_INFO, message)
            
    def on_client_error(self, error_type, error):
        if error_type == papyon.event.ClientErrorType.AUTHENTICATION:
            self._client.session.add_event(Event.EVENT_LOGIN_FAILED,
                                           _('Authentication failure'))      
        elif error_type == papyon.event.ClientErrorType.NETWORK:
            self._client.session.add_event(Event.EVENT_DISCONNECTED,
                                           _('Network error'), 1)#for reconnecting
        elif error_type == papyon.event.ClientErrorType.PROTOCOL:
            if error == papyon.event.ProtocolError.OTHER_CLIENT:
                self._client.session.add_event(Event.EVENT_DISCONNECTED,
                              _('Logged in from another location'), 0)
            elif error == papyon.event.ProtocolError.SERVER_DOWN:
                self._client.session.add_event(Event.EVENT_DISCONNECTED,
                                               _('Server down'), 1)#for reconnecting
            elif error == papyon.event.ProtocolError.AUTHENTICATION_FAILED:
                self._client.session.add_event(Event.EVENT_DISCONNECTED,
                                               _('Authentication failure'), 0)
            else:
                self._client.session.add_event(Event.EVENT_DISCONNECTED,
                                               _('Protocol error'), 0)
        elif error_type == papyon.event.ClientErrorType.CONTENT_ROAMING:
            if isinstance(error, papyon.gnet.errors.HTTPError) and \
               error.response and error.response.status and \
               error.response.status == 404:
                self._client.session.add_event(Event.EVENT_BROKEN_PROFILE,
                                               PROFILE_URL)
                return
            try:
                if error._fault == "ItemDoesNotExist":
                    self._client.session.add_event(Event.EVENT_BROKEN_PROFILE,
                                                   PROFILE_URL)
            except AttributeError:
                log.error("Client got an error: %s %s" % (error_type, error))
        elif error_type == papyon.event.ClientErrorType.ADDRESSBOOK:
            log.error("Client got an error handling addressbook: %s %s" % (error_type, error))
            self._client.session.add_event(Event.EVENT_DISCONNECTED, "%s %s" % (error, error_type), 0)
        elif error_type == papyon.event.ClientErrorType.OFFLINE_MESSAGES:#TODO
            log.error("Client got an error handling offline messages: %s %s" % (error_type, error))
        else:
            log.error("Client got an error: %s %s" % (error_type, error))

class InviteEvent(papyon.event.InviteEventInterface):
    def on_invite_conversation(self, conversation):
        self._client._on_conversation_invite(conversation)

    def on_invite_webcam(self, session, producer):
        pass # silently ignore invites, they're deprecated by calls.

    def on_invite_conference(self, call):
        self._client._on_conference_invite(call)

    def on_invite_file_transfer(self, session):
        self._client._on_invite_file_transfer(session)
        
class ConversationEvent(papyon.event.ConversationEventInterface):
    def __init__(self, conversation, _client):
        papyon.event.BaseEventInterface.__init__(self, conversation)
        self._client = _client
        self.conversation = conversation

    def on_conversation_user_joined(self, contact):
        self._client._on_conversation_user_joined(contact, self)

    def on_conversation_user_left(self, contact):
        self._client._on_conversation_user_left(contact, self)

    def on_conversation_user_typing(self, contact):
        self._client._on_conversation_user_typing(contact, self)

    def on_conversation_message_received(self, sender, message):
        self._client._on_conversation_message_received(sender, message, self)
    
    def on_conversation_nudge_received(self, sender):
        self._client._on_conversation_nudge_received(sender, self)
        
    def on_conversation_error(self, error_type, error):
        self._client._on_conversation_message_error(error_type, error, self)

class ContactEvent(papyon.event.ContactEventInterface):
    def on_contact_memberships_changed(self, contact):
        self._client._on_contact_membership_changed(contact)

    def on_contact_presence_changed(self, contact):
        self._client._on_contact_status_changed(contact)

    def on_contact_display_name_changed(self, contact):
        self._client._on_contact_nick_changed(contact)

    def on_contact_personal_message_changed(self, contact):
        self._client._on_contact_pm_changed(contact)
        
    def on_contact_current_media_changed(self, contact):
        self._client._on_contact_media_changed(contact)

    def on_contact_infos_changed(self, contact, infos):
        '''called when setting stuff such as alias'''
        log.info("Contact informations changed: %s %s" % (contact, infos))

    def on_contact_client_capabilities_changed(self, contact):
        """Called when the client capabilities of a contact changes.
            @param contact: the contact whose presence changed
            @type contact: L{Contact<papyon.profile.Contact>}"""
        # TODO: handle this -- capabilities? wtf?
        log.info("Contact's client capabilities changed: %s" % contact)

    def on_contact_msn_object_changed(self, contact):
        self._client._on_contact_msnobject_changed(contact)

class AddressBookEvent(papyon.event.AddressBookEventInterface):
    def on_addressbook_contact_pending(self, contact):
        self._client._on_addressbook_contact_pending(contact)

    def on_addressbook_messenger_contact_added(self, contact):
        self._client._on_addressbook_messenger_contact_added(contact)

    def on_addressbook_contact_deleted(self, contact):
        self._client._on_addressbook_contact_deleted(contact)

    def on_addressbook_contact_blocked(self, contact):
        self._client._on_addressbook_contact_blocked(contact)

    def on_addressbook_contact_unblocked(self, contact):
        self._client._on_addressbook_contact_unblocked(contact)

    def on_addressbook_group_added(self, group):
        self._client._on_addressbook_group_added(group)

    def on_addressbook_group_deleted(self, group):
        self._client._on_addressbook_group_deleted(group)

    def on_addressbook_group_renamed(self, group):
        self._client._on_addressbook_group_renamed(group)

    def on_addressbook_group_contact_added(self, group, contact):
        self._client._on_addressbook_group_contact_added(group, contact)

    def on_addressbook_group_contact_deleted(self, group, contact):
        self._client._on_addressbook_group_contact_deleted(group, contact)
        
class ProfileEvent(papyon.event.ProfileEventInterface):
    def on_profile_presence_changed(self):
        self._client._on_profile_presence_changed()
        
    def on_profile_display_name_changed(self):
        self._client._on_profile_display_name_changed()
        
    def on_profile_personal_message_changed(self):
        self._client._on_profile_personal_message_changed()

    def on_profile_current_media_changed(self):
        self._client._on_profile_current_media_changed()

    def on_profile_msn_object_changed(self):
        self._client._on_profile_msn_object_changed()

    def on_profile_end_point_added(self, ep):
        self._client._on_profile_end_point_added(ep)

    def on_profile_end_point_removed(self, ep):
        self._client._on_profile_end_point_removed(ep)

    def on_profile_end_point_updated(self, ep):
        self._client._on_profile_end_point_updated(ep)

class CallEvent(papyon.event.CallEventInterface):
    def __init__(self, call, client):
        papyon.event.CallEventInterface.__init__(self, call)
        self._client = client
        self._call = call

    def on_call_incoming(self):
        self._client._on_call_incoming(self)

    def on_call_ringing(self):
        self._client._on_call_ringing(self)

    def on_call_accepted(self):
        self._client._on_call_accepted(self)

    def on_call_rejected(self, response):
        self._client._on_call_rejected(self, response)

    def on_call_error(self, response):
        self._client._on_call_error(self, response)

    def on_call_missed(self):
        self._client._on_call_missed(self)

    def on_call_connected(self):
        self._client._on_call_connected(self)

    def on_call_ended(self):
        self._client._on_call_ended(self)

class OfflineEvent(papyon.event.OfflineMessagesEventInterface):
    """interfaces allowing the user to get notified about events from the
    Offline IM box."""

    def __init__(self, client):
        self._client = client
        papyon.event.OfflineMessagesEventInterface.__init__(self, client)

    def on_oim_state_changed(self, state):
        ''' NOT_SYNCHRONIZED = 0 SYNCHRONIZING = 1 SYNCHRONIZED = 2 '''
        log.info("OIM service state changed: %s" % state)

    def on_oim_messages_received(self, messages):
        self._client.oim_box.fetch_messages(messages)

    def on_oim_messages_fetched(self, messages):
        for message in sorted(messages):
            self._client._on_conversation_oim_received(message)
        self._client.oim_box.delete_messages()

    def on_oim_messages_deleted(self, *messages):
        log.info("OIMs deleted on the server")

    def on_oim_message_sent(self, recipient, message):
        log.info("OIM sent correctly: %s" % (recipient, message))

class MailboxEvent(papyon.event.MailboxEventInterface):
    """interfaces allowing the user to get notified about events from the Inbox.
    """

    def __init__(self, client):
        papyon.event.BaseEventInterface.__init__(self, client)

    def on_mailbox_unread_mail_count_changed(self, unread_mail_count, 
                                                   initial=False):
        self._client._on_mailbox_unread_mail_count_changed(unread_mail_count, initial)

    def on_mailbox_new_mail_received(self, mail_message):
        self._client._on_mailbox_new_mail_received(mail_message)
