# -*- coding: utf-8 -*-
#
# papylib - an emesene extension for papyon
#
# Copyright (C) 2009 Riccardo (C10uD) <c10ud.dev@gmail.com>
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

from e3.base.Event import Event
import papyon.event

class ClientEvents(papyon.event.ClientEventInterface):
    def on_client_state_changed(self, state):
        if state == papyon.event.ClientState.CLOSED:
            #self._client.quit()
            pass
        elif state == papyon.event.ClientState.OPEN:
            self._client.set_initial_infos()
            
            self._client.session.add_event(Event.EVENT_LOGIN_SUCCEED)
            self._client._fill_contact_list(self._client.address_book)
            
    def on_client_error(self, error_type, error):
        print "ERROR :", error_type, " ->", error    

class InviteEvent(papyon.event.InviteEventInterface):
    def __init__(self, client):
        """Initializer
            @param client: the client we want to be notified for its events
            @type client: L{Client<papyon.Client>}"""
        papyon.event.BaseEventInterface.__init__(self, client)

    def on_invite_conversation(self, conversation):
        """Called when we get invited into a conversation
            @param conversation: the conversation
            @type conversation: L{Conversation<papyon.conversation.ConversationInterface>}"""
        self._client._on_conversation_invite(conversation)

    def on_invite_webcam(self, session, producer):
        """Called when we get invited into a webcam conversation
            @param session: the session
            @type session: L{WebcamSession<papyon.msnp2p.webcam.WebcamSession>}"""
        self._client._on_webcam_invite(session, producer)

    def on_invite_conference(self, call):
        """Called when we get invited into a conference
            @param call: the call
            @type call: L{SIPCall<papyon.sip.sip.SIPCall>}"""
        self._client._on_conference_invite(call)
        
class ConversationEvent(papyon.event.ConversationEventInterface):
    def __init__(self, conversation, _client):
        papyon.event.BaseEventInterface.__init__(self, conversation)
        self._client = _client
        self.conversation = conversation

    def on_conversation_user_joined(self, contact):
        """Called when an user joins the conversation.
            @param contact: the contact whose presence changed
            @type contact: L{Contact<papyon.profile.Contact>}"""
        print "[papyon]", contact, "joined a conversation"

    def on_conversation_user_left(self, contact):
        """Called when an user leaved the conversation.
            @param contact: the contact whose presence changed
            @type contact: L{Contact<papyon.profile.Contact>}"""
        print "[papyon]", contact, "left a conversation"

    def on_conversation_user_typing(self, contact):
        self._client._on_conversation_user_typing(contact, self)

    def on_conversation_message_received(self, sender, message):
        self._client._on_conversation_message_received(sender, message, self)
    
    def on_conversation_nudge_received(self, sender):
        self._client._on_conversation_nudge_received(sender, self)
        
    def on_conversation_error(self, error_type, error):
        print "ERROR :", error_type, " ->", error

class ContactEvent(papyon.event.ContactEventInterface):
    def on_contact_memberships_changed(self, contact):
        """Called when the memberships of a contact changes.
            @param contact: the contact whose presence changed
            @type contact: L{Contact<papyon.profile.Contact>}
            @see: L{Memberships<papyon.profile.Membership>}"""
        pass

    def on_contact_presence_changed(self, contact):
        self._client._on_contact_status_changed(contact)

    def on_contact_display_name_changed(self, contact):
        self._client._on_contact_nick_changed(contact)

    def on_contact_personal_message_changed(self, contact):
        self._client._on_contact_pm_changed(contact)
        
    def on_contact_current_media_changed(self, contact):
        self._client._on_contact_media_changed(contact)

    def on_contact_infos_changed(self, contact, infos):
        """Called when the infos of a contact changes.
            @param contact: the contact whose presence changed
            @type contact: L{Contact<papyon.profile.Contact>}"""
        pass

    def on_contact_client_capabilities_changed(self, contact):
        """Called when the client capabilities of a contact changes.
            @param contact: the contact whose presence changed
            @type contact: L{Contact<papyon.profile.Contact>}"""
        pass

    def on_contact_msn_object_changed(self, contact):
        self._client._on_contact_msnobject_changed(contact)

class AddressBookEvent(papyon.event.AddressBookEventInterface):
    def __init__(self, client):
        papyon.event.BaseEventInterface.__init__(self, client)

    def on_addressbook_messenger_contact_added(self, contact):
        pass

    def on_addressbook_contact_deleted(self, contact):
        pass

    def on_addressbook_contact_blocked(self, contact):
        pass

    def on_addressbook_contact_unblocked(self, contact):
        pass

    def on_addressbook_group_added(self, group):
        pass

    def on_addressbook_group_deleted(self, group):
        pass

    def on_addressbook_group_renamed(self, group):
        pass

    def on_addressbook_group_contact_added(self, group, contact):
        pass

    def on_addressbook_group_contact_deleted(self, group, contact):
        pass
        
class ProfileEvent(papyon.event.ProfileEventInterface):
    def __init__(self, client):
        papyon.event.BaseEventInterface.__init__(self, client)
        self._client = client
        
    def on_profile_presence_changed(self):
        """Called when the presence changes."""
        print "[papyon] profile presence changed"
        
    def on_profile_display_name_changed(self):
        """Called when the display name changes."""
        print "[papyon] profile nick changed"
        
    def on_profile_personal_message_changed(self):
        """Called when the personal message changes."""
        print "[papyon] profile pm changed"

    def on_profile_current_media_changed(self):
        """Called when the current media changes."""
        print "[papyon] profile media changed"

    def on_profile_msn_object_changed(self):
        """Called when the MSNObject changes."""
        print "[papyon] profile dp changed"

class WebcamEvent(papyon.event.WebcamEventInterface):
    def __init__(self, session):
        """Initializer
            @param session: the session we want to be notified for its events
            @type session: L{WebcamSession<papyon.msnp2p.webcam.WebcamSession>}"""
        papyon.event.BaseEventInterface.__init__(self, session)

    def on_webcam_viewer_data_received(self):
        """Called when we received viewer data"""
        print "[webcam] viewer data received"

    def on_webcam_accepted(self):
        """Called when our invitation got accepted"""
        print "[webcam] accepted"

    def on_webcam_rejected(self):
        """Called when our invitation got rejected"""
        print "[webcam] rejected"

    def on_webcam_paused(self):
        """Called when the webcam is paused"""
        print "[webcam] paused"

class CallEvent(papyon.event.CallEventInterface):
    """interfaces allowing the user to get notified about events
    from a L{MediaCall<papyon.media.MediaCall>} object."""

    def __init__(self, call):
        """Initializer
            @param call: the call we want to be notified for its events
            @type call: L{MediaCall<papyon.media.MediaCall>}"""
        papyon.event.BaseEventInterface.__init__(self, call)
        print "dude"

    def on_call_incoming(self):
        """Called once the incoming call is ready."""
        print "[call] ready"

    def on_call_ringing(self):
        """Called when we received a ringing response from the callee."""
        print "[call] ringing"

    def on_call_accepted(self):
        """Called when the callee accepted the call."""
        print "[call] accepted"

    def on_call_rejected(self, response):
        """Called when the callee rejected the call.
            @param response: response associated with the rejection
            @type response: L{SIPResponse<papyon.sip.SIPResponse>}"""
        print "[call] rejected"

    def on_call_error(self, response):
        """Called when an error is sent by the other party.
            @param response: response associated with the error
            @type response: L{SIPResponse<papyon.sip.SIPResponse>}"""
        print "[call] err"

    def on_call_missed(self):
        """Called when the call is missed."""
        print "[call] missd"

    def on_call_connected(self):
        """Called once the call is connected."""
        print "[call] connected"

    def on_call_ended(self):
        """Called when the call is ended."""
        print "[call] ended"
