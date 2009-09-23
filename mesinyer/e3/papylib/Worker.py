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

import sys
import time
import Queue
import random
import gobject
import shutil
import os

import e3.base.Worker
import e3.base.Message
import e3.base.Contact
import e3.base.Group
from e3.base.Event import Event
from e3.base.Action import Action
from e3.base import status
from e3.cache import *
from e3.common import ConfigDir
import e3.base.Logger as Logger
from debugger import dbg

try:
    # papyon imports
    # get the deb from http://launchpadlibrarian.net/31746931/python-papyon_0.4.2-1%7Eppa9.04%2B1_all.deb
    import logging
    import papyon
    import papyon.event
    ver = papyon.version    
    if ver[1] < 4 or ver[2] < 2:
        raise PapyError
except:
    print "You need python-papyon(>=0.4.2) to be installed in order to use this extension"    

#logging.basicConfig(level=logging.DEBUG)

STATUS_PAPY_TO_E3 = { \
    papyon.Presence.ONLINE : status.ONLINE,
    papyon.Presence.BUSY : status.BUSY,
    papyon.Presence.IDLE : status.IDLE,
    papyon.Presence.AWAY : status.AWAY,
    papyon.Presence.BE_RIGHT_BACK : status.AWAY,
    papyon.Presence.ON_THE_PHONE : status.AWAY,
    papyon.Presence.OUT_TO_LUNCH : status.AWAY,
    papyon.Presence.INVISIBLE : status.OFFLINE,
    papyon.Presence.OFFLINE : status.OFFLINE}
    
STATUS_E3_TO_PAPY = { \
    status.ONLINE : papyon.Presence.ONLINE,
    status.BUSY : papyon.Presence.BUSY,
    status.IDLE : papyon.Presence.IDLE,
    status.AWAY : papyon.Presence.AWAY,
    status.OFFLINE : papyon.Presence.INVISIBLE}
    
def formatting_papy_to_e3(format = papyon.TextFormat()):
    font = format.font
    color = e3.base.Color.from_hex('#' + str(format.color))
    bold = format.style & papyon.TextFormat.BOLD == papyon.TextFormat.BOLD
    italic = format.style & papyon.TextFormat.ITALIC == papyon.TextFormat.ITALIC
    underline = format.style & papyon.TextFormat.UNDERLINE == papyon.TextFormat.UNDERLINE
    strike = format.style & papyon.TextFormat.STRIKETHROUGH == papyon.TextFormat.STRIKETHROUGH
    size_ = format.pitch # wtf?
    
    return e3.base.Style(font, color, bold, italic, underline, strike, size_)
    
def formatting_e3_to_papy(format = e3.base.Style()):
    font = format.font
    style = 0
    if format.bold: style |= papyon.TextFormat.BOLD
    if format.italic: style |= papyon.TextFormat.ITALIC
    if format.underline: style |= papyon.TextFormat.UNDERLINE
    if format.strike: style |= papyon.TextFormat.STRIKETHROUGH
    color = format.color.to_hex()
    charset = papyon.TextFormat.DEFAULT_CHARSET # wtf
    family = papyon.TextFormat.FF_DONTCARE # wtf/2
    pitch = papyon.TextFormat.DEFAULT_PITCH # wtf/3
    right_alignment = False # wtf/4
    
    return papyon.TextFormat(font, style, color, charset, family, pitch, \
        right_alignment)
    
def get_proxies():
    import urllib
    proxies = urllib.getproxies()
    result = {}
    if 'https' not in proxies and \
            'http' in proxies:
        url = proxies['http'].replace("http://", "https://")
        result['https'] = papyon.Proxy(url)
    for type, url in proxies.items():
        if type == 'no': continue
        if type == 'https' and url.startswith('http://'):
            url = url.replace('http://', 'https://', 1)
        result[type] = papyon.Proxy(url)
    return result
    
class ClientEvents(papyon.event.ClientEventInterface):
    def on_client_state_changed(self, state):
        if state == papyon.event.ClientState.CLOSED:
            #self._client.quit()
            pass
        elif state == papyon.event.ClientState.OPEN:
            self._client.session.add_event(Event.EVENT_LOGIN_SUCCEED)
            self._client._fill_contact_list(self._client.address_book)
            
            self._client.set_initial_infos()
            
    def on_client_error(self, error_type, error):
        print "ERROR :", error_type, " ->", error    

class InviteEvent(papyon.event.InviteEventInterface):
    def on_invite_conversation(self, conversation):
        self._client._on_conversation_invite(conversation)
        
    def on_invite_webcam(self, session, producer):
        self._client._on_webcam_invite(session, producer)
        
class ConversationEvent(papyon.event.ConversationEventInterface):
    def __init__(self, conversation, _client):
        papyon.event.BaseEventInterface.__init__(self, conversation)
        self._client = _client
        self.conversation = conversation

    def on_conversation_user_joined(self, contact):
        """Called when an user joins the conversation.
            @param contact: the contact whose presence changed
            @type contact: L{Contact<papyon.profile.Contact>}"""
        print contact, "joined a conversation"

    def on_conversation_user_left(self, contact):
        """Called when an user leaved the conversation.
            @param contact: the contact whose presence changed
            @type contact: L{Contact<papyon.profile.Contact>}"""
        print contact, "left a conversation"

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
        self.client = client
        
    def on_profile_presence_changed(self):
        """Called when the presence changes."""
        print "presence changed"
        
    def on_profile_display_name_changed(self):
        """Called when the display name changes."""
        print "displayname changed"
        
    def on_profile_personal_message_changed(self):
        """Called when the personal message changes."""
        print "pm changed"

    def on_profile_current_media_changed(self):
        """Called when the current media changes."""
        pass

    def on_profile_msn_object_changed(self):
        """Called when the MSNObject changes."""
        print "dp changed"
        
class Worker(e3.base.Worker, papyon.Client):
    '''dummy Worker implementation to make it easy to test emesene'''

    def __init__(self, app_name, session, proxy, use_http=False):
        '''class constructor'''
        e3.base.Worker.__init__(self, app_name, session)
        self.session = session
        server = ('messenger.hotmail.com', 1863)

        if use_http:
            from papyon.transport import HTTPPollConnection
            self.client = papyon.Client.__init__(self, server, get_proxies(), HTTPPollConnection)
        else:
            self.client = papyon.Client.__init__(self, server, proxies = get_proxies())
        
        
        self._event_handler = ClientEvents(self)
        self._contact_handler = ContactEvent(self)
        self._invite_handler = InviteEvent(self)
        self._abook_handler = AddressBookEvent(self)
        self._profile_handler = ProfileEvent(self)
        #TODO fix cache
        #self._avatar_cache = None

        # this stores account : cid
        self.conversations = {}
        # this stores cid : account
        self.rconversations = {}
        # this stores papyon conversations as cid : conversation
        self.papyconv = {}
        # this stores conversation handlers
        self._conversation_handler = {}
        
    def run(self):
        '''main method, block waiting for data, process it, and send data back
        '''
        self._mainloop = gobject.MainLoop(is_running=True)
        while self._mainloop.is_running():    
            try:
                action = self.session.actions.get(True, 0.1)

                if action.id_ == Action.ACTION_QUIT:
                    dbg('closing thread', 'dworker', 1)
                    self.logout()
                    self.session.logger.quit()
                    break

                self._process_action(action)
            except Queue.Empty:
                pass
            
    # some useful methods
    def set_nick(self, nick, updatepapy=True):
        self._handle_action_set_nick(nick)
        
    def set_status(self, status):
        self._handle_action_change_status(status)
        
    def set_pm(self, pm, updatepapy=True):
        self._handle_action_set_message(pm)
        
    def set_msnobj(self, msnobj, updatepapy=True):
        pass
        
    def set_initial_infos(self):
        '''this is called on login'''
        # try content roaming
        nick = self.profile.display_name
        message = self.profile.personal_message
        dp = self.profile.msn_object
        
        self.set_nick(nick, updatepapy=False)
        self.set_pm(message, updatepapy=False)
        self.set_msnobj(dp, updatepapy=False)
        self.set_status(self.session.account.status)
        
    def _set_status(self, stat):
        '''why is this particular function needed? 
           and btw, the button for changing status doesn't work
        '''
        self.session.account.status = stat
        self.session.contacts.me.status = stat
        self.profile.presence = STATUS_E3_TO_PAPY[stat]
        self.session.add_event(Event.EVENT_STATUS_CHANGE_SUCCEED, stat)
        # log the status
        contact = self.session.contacts.me
        account =  Logger.Account(contact.attrs.get('CID', None), None,
            contact.account, stat, contact.nick, contact.message,
            contact.picture)

        self.session.logger.log('status change', stat, str(stat), account)

    def _fill_contact_list(self, ab):
        ''' fill the contact list with papy contacts '''
        for group in ab.groups:
            self._add_group(group.name)
        
        for contact in ab.contacts:
            self._add_contact(contact.account, contact.display_name, \
                STATUS_PAPY_TO_E3[contact.presence], contact.personal_message, \
                False)
                # TODO: 'BLOCKED' in contact.memberships)
                # TODO: eventual friendly name (alias)
            for group in contact.groups:
                self._add_contact_to_group(contact.account, group.name)
        
        self.session.add_event(Event.EVENT_CONTACT_LIST_READY)

    def _add_contact(self, mail, nick, status_, pm, blocked, alias=''):
        ''' helper method to add a contact to the (gui) contact list '''
        # wtf, why 2 mails?
        self.session.contacts.contacts[mail] = e3.base.Contact(mail, mail,
            nick, pm, status_, alias, blocked)

    def _add_group(self, name):
        ''' method to add a group to the (gui) contact list '''
        self.session.groups[name] = e3.base.Group(name, name)

    def _add_contact_to_group(self, account, group):
        ''' method to add a contact to a (gui) group '''
        self.session.groups[group].contacts.append(account)
        self.session.contacts.contacts[account].groups.append(group)
    
    def _get_msn_object_path(self, msn_object):
        '''method to get an MSNObject path'''

        #TODO why 2 callbacks and not 1?Let's investigate!
        if msn_object._type == papyon.p2p.MSNObjectType.DISPLAY_PICTURE or \
            msn_object._type == papyon.p2p.MSNObjectType.DYNAMIC_DISPLAY_PICTURE:
            try:
                #TODO Search in AVATAR CACHE
                path = open( os.path.expanduser(os.path.join('~', '.config', 
                'emesene2', self.session.account.account,
                msn_object._checksum_sha + ".png")), "r").name
            except:
                #Download the content
                self.cbs = (self._download_avatar, self._download_avatar)
                self.msn_object_store.request(msn_object, self.cbs)
                #TODO now the content MUST be in cache! (got to handle transfer error)
                path = os.path.expanduser(os.path.join('~', '.config', 
                'emesene2', self.session.account.account,
                msn_object._checksum_sha + ".png"))
        elif msn_object._type == papyon.p2p.MSNObjectType.BACKGROUND_PICTURE:
            try:
                #TODO Search in BACKGROUND CACHE
                path = open( os.path.expanduser(os.path.join('~', '.config', 
                'emesene2', self.session.account.account,
                msn_object._checksum_sha + ".jpg")), "r").name
            except:
                #Download the content
                self.cbs = (self._download_background, self._download_background)
                self.msn_object_store.request(msn_object, self.cbs)
                #TODO now the content MUST be in cache! (got to handle transfer error)
                path = os.path.expanduser(os.path.join('~', '.config', 
                'emesene2', self.session.account.account,
                msn_object._checksum_sha + ".jpg"))

        elif msn_object._type == papyon.p2p.MSNObjectType.CUSTOM_EMOTICON:
            try:
                #TODO Search in EMOTICON CACHE
                path = open( os.path.expanduser(os.path.join('~', '.config', 
                'emesene2', self.session.account.account,
                msn_object._checksum_sha + ".gif")), "r").name
            except:
                #Download the content
                self.cbs = (self._download_custom_emoticon, self._download_custom_emoticon)
                self.msn_object_store.request(msn_object, self.cbs)
                #TODO now the content MUST be in cache! (got to handle transfer error)
                path = os.path.expanduser(os.path.join('~', '.config', 
                'emesene2', self.session.account.account,
                msn_object._checksum_sha + ".gif"))
        
        return path
        
        
    def _download_avatar(self, msn_object, _msn_object_content):
        '''this callback saves the avatar, _msn_object_content is a callback
        maybe the second invoked by _request_avatar with method "request"??'''
        #A Little workaround before caching implementation
        image = open( os.path.expanduser(os.path.join('~', '.config', 
            'emesene2', self.session.account.account,
            msn_object._checksum_sha + ".png")), "w") 
        image.write(msn_object._data.getvalue())
        image.close()
        #TODO this should be moved in a better method
        contact = self.session.contacts.contacts.get(msn_object._creator, None)
        contact.picture = image.name
        print "Used " + image.name + " as " + contact.account +"'s image"
        #TODO check this one: why doesn't update the contact's image?
        self.session.add_event( Event.EVENT_CONTACT_ATTR_CHANGED , contact.account, 'picture' , image.name)
        #TODO fix cache
        #self._avatar_cache.insert(msn_object._data.getvalue())

    def _download_custom_emoticon(self, msn_object, _msn_object_content):
        '''this callback saves the avatar, _msn_object_content is a callback
        maybe the second invoked by _request_avatar with method "request"??'''
        #A Little workaround before caching implementation
        image = open( os.path.expanduser(os.path.join('~', '.config', 
            'emesene2', self.session.account.account,
            msn_object._checksum_sha + ".gif")), "w") 
        image.write(msn_object._data.getvalue())
        image.close()
        #TODO fix cache
        #self._emoticon_cache.insert(msn_object._data.getvalue())

    def _download_background(self, msn_object, _msn_object_content):
        '''this callback saves the avatar, _msn_object_content is a callback
        maybe the second invoked by _request_avatar with method "request"??'''
        #A Little workaround before caching implementation
        image = open( os.path.expanduser(os.path.join('~', '.config', 
            'emesene2', self.session.account.account,
            msn_object._checksum_sha + ".jpg")), "w") 
        image.write(msn_object._data.getvalue())
        image.close()
        print "Used " + image.name + " as " + contact.account +"'s Background Image"
        #TODO fix cache
        #self._background_cache.insert(msn_object._data.getvalue())

    # invite handlers
    def _on_conversation_invite(self, papyconversation):
        ''' create a cid and append the event handler to papyconv dict '''
        cid = time.time()
        newconversationevent = ConversationEvent(papyconversation, self)
        self._conversation_handler[cid] = newconversationevent
        
    def _on_webcam_invite(self, session, producer):
        raise NotImplementedError
        
    # conversation handlers
    def _on_conversation_user_typing(self, papycontact, pyconvevent):
        ''' handle user typing event '''
        account = papycontact.account
        if account in self.conversations:
            # emesene conversation already exists
            cid = self.conversations[account]
        else:
            # we don't care about users typing if no conversation is opened
            return
        
        # TODO: find how to do this    
        #self.session.add_event(Event.EVENT_USER_TYPING, cid, account, msgobj)
        
    def _on_conversation_message_received(self, papycontact, papymessage, \
        pyconvevent):
        ''' handle the reception of a message '''
        account = papycontact.account
        if account in self.conversations:
            # emesene conversation already exists
            cid = self.conversations[account]
        else:
            # emesene must create another conversation
            cid = time.time()
            self.conversations[account] = cid # add to account:cid
            self.rconversations[cid] = account
            self._conversation_handler[cid] = pyconvevent # add conv handler
            self.papyconv[cid] = pyconvevent.conversation # add papy conv
            self.session.add_event(Event.EVENT_CONV_FIRST_ACTION, cid,
                [account])
        
        msgobj = e3.base.Message(e3.base.Message.TYPE_MESSAGE, \
            papymessage.content, account, \
            formatting_papy_to_e3(papymessage.formatting))
        # convert papyon msnobjects to a simple dict {shortcut:identifier}
        cedict = {}
        for msnobj in papymessage.msn_objects:
        # which identifier do we want? shac? 
        # then we must request the data if not available in our 
        # (not implemented) cache
            cedict[msnobj] = papymessage.msn_objects[msnobj]._checksum_sha
        
        self.session.add_event(Event.EVENT_CONV_MESSAGE, cid, account, msgobj, cedict)
       
    def _on_conversation_nudge_received(self, papycontact, pyconvevent):
        ''' handle received nudges '''
        account = papycontact.account
        if account in self.conversations:
            # emesene conversation already exists
            cid = self.conversations[account]
        else:
            #print "must create another conversation"
            cid = time.time()
            self.conversations[account] = cid # add to account:cid
            self.rconversations[cid] = account
            self._conversation_handler[cid] = pyconvevent # add conv handler
            self.papyconv[cid] = pyconvevent.conversation # add papy conv
            self.session.add_event(Event.EVENT_CONV_FIRST_ACTION, cid,
                [account])
                
        msgobj = e3.base.Message(e3.base.Message.TYPE_NUDGE, None, \
            account, None)
                
        self.session.add_event(Event.EVENT_CONV_MESSAGE, cid, account, msgobj)
       
    # contact changes handlers
    def _on_contact_status_changed(self, papycontact):
        status_ = STATUS_PAPY_TO_E3[papycontact.presence]    
        contact = self.session.contacts.contacts.get(papycontact.account, None)
        if not contact:
            return
        account = contact.account
        old_status = contact.status
        contact.status = status_
        
        log_account = Logger.Account(contact.attrs.get('CID', None), None, \
            contact.account, contact.status, contact.nick, contact.message, \
            contact.picture)
        if old_status != status_:
            self.session.add_event(Event.EVENT_CONTACT_ATTR_CHANGED, account, \
                'status', old_status) 
            self.session.logger.log('status change', status_, str(status_), \
                log_account)
            
    def _on_contact_nick_changed(self, papycontact):
        contact = self.session.contacts.contacts.get(papycontact.account, None)
        if not contact:
            return
        account = contact.account
        old_nick = contact.nick
        nick = papycontact.display_name
        contact.nick = nick
        status_ = contact.status
        
        log_account = Logger.Account(contact.attrs.get('CID', None), None, \
            contact.account, contact.status, contact.nick, contact.message, \
            contact.picture)

        if old_nick != nick:
            self.session.add_event(Event.EVENT_CONTACT_ATTR_CHANGED, account, \
                'nick', old_nick)
            self.session.logger.log('nick change', status_, nick, \
                log_account)

    def _on_contact_pm_changed(self, papycontact):
        contact = self.session.contacts.contacts.get(papycontact.account, None)
        if not contact:
            return
        account = contact.account
        old_message = contact.message
        contact.message = papycontact.personal_message
        
        if old_message == contact.message:
            return

        if old_message != contact.message:
            self.session.add_event(Event.EVENT_CONTACT_ATTR_CHANGED, account, \
                'message', old_message)
            self.session.logger.log('message change', contact.status, \
                contact.message, Logger.Account(contact.attrs.get('CID', None), \
                    None, contact.account, contact.status, contact.nick, \
                    contact.message, contact.picture))

    def _on_contact_media_changed(self, papycontact):
        contact = self.session.contacts.contacts.get(papycontact.account, None)
        if not contact:
            return
        account = contact.account
        old_media = contact.media
        contact.media = papycontact.current_media
        
        if old_media == contact.media:
            return

        if old_media == contact.media:
            self.session.add_event(Event.EVENT_CONTACT_ATTR_CHANGED, account, 
                'media', old_media)
            # TODO: log the media change
    
    def _on_contact_msnobject_changed(self, contact):
        resource_path = self._get_msn_object_path(contact.msn_object)
        print resource_path
        
    # action handlers
    def _handle_action_add_contact(self, account):
        ''' handle Action.ACTION_ADD_CONTACT '''
        papycontact = self.address_book.contacts.search_by('account', account)
        
        # TODO: move succeed to papyon callbacks
        self.session.add_event(Event.EVENT_CONTACT_ADD_SUCCEED,
            account)

    def _handle_action_add_group(self, name):
        '''handle Action.ACTION_ADD_GROUP
        '''
        self.address_book.add_group(name)
        
        # TODO: move succeed to papyon callbacks
        self.session.add_event(Event.EVENT_GROUP_ADD_SUCCEED,
            name)

    def _handle_action_add_to_group(self, account, gid):
        ''' handle Action.ACTION_ADD_TO_GROUP '''
        self.session.add_event(Event.EVENT_GROUP_ADD_CONTACT_SUCCEED,
            gid, account)

    def _handle_action_block_contact(self, account):
        ''' handle Action.ACTION_BLOCK_CONTACT '''
        self.session.add_event(Event.EVENT_CONTACT_BLOCK_SUCCEED, account)

    def _handle_action_unblock_contact(self, account):
        '''handle Action.ACTION_UNBLOCK_CONTACT '''
        self.session.add_event(Event.EVENT_CONTACT_UNBLOCK_SUCCEED,
            account)

    def _handle_action_change_status(self, status_):
        '''handle Action.ACTION_CHANGE_STATUS '''
        self._set_status(status_)
        
    def _handle_action_login(self, account, password, status_):
        '''handle Action.ACTION_LOGIN '''
        self.session.account.account = account
        self.session.account.password = password
        self.session.account.status = status_
        self.session.add_event(Event.EVENT_LOGIN_STARTED)
        self.login(account, password)
        #TODO Fix Cache
        #self._avatar_cache = AvatarCache(os.path.expanduser(os.path.join('~', '.config',
        #        'emesene2')),self.session.account.account)
        
    def _handle_action_logout(self):
        ''' handle Action.ACTION_LOGOUT '''
        self.quit()
        
    def _handle_action_move_to_group(self, account, src_gid, dest_gid):
        '''handle Action.ACTION_MOVE_TO_GROUP '''
        self.session.add_event(Event.EVENT_CONTACT_MOVE_SUCCEED,
            account, src_gid, dest_gid)

    def _handle_action_remove_contact(self, account):
        '''handle Action.ACTION_REMOVE_CONTACT '''
        papycontact = self.address_book.contacts.search_by('account', account)
        self.address_book.delete_contact(papycontact)
        # TODO: move to ab callback
        self.session.add_event(Event.EVENT_CONTACT_REMOVE_SUCCEED, account)

    def _handle_action_reject_contact(self, account):
        '''handle Action.ACTION_REJECT_CONTACT '''
        papycontact = self.address_book.contacts.search_by('account', account)
        self.address_book.decline_contact_invitation(papycontact)
        
        # TODO: move to ab callback
        self.session.add_event(Event.EVENT_CONTACT_REJECT_SUCCEED, account)

    def _handle_action_remove_from_group(self, account, gid):
        ''' handle Action.ACTION_REMOVE_FROM_GROUP '''
        self.session.add_event(Event.EVENT_GROUP_REMOVE_CONTACT_SUCCEED,
            gid, account)

    def _handle_action_remove_group(self, gid):
        ''' handle Action.ACTION_REMOVE_GROUP '''
        self.session.add_event(Event.EVENT_GROUP_REMOVE_SUCCEED, gid)

    def _handle_action_rename_group(self, gid, name):
        ''' handle Action.ACTION_RENAME_GROUP '''
        self.address_book.rename_group(name, newname = 'todo')
        
        self.session.add_event(Event.EVENT_GROUP_RENAME_SUCCEED,
            gid, name)

    def _handle_action_set_contact_alias(self, account, alias):
        ''' handle Action.ACTION_SET_CONTACT_ALIAS '''
        self.session.add_event(Event.EVENT_CONTACT_ALIAS_SUCCEED, account)

    def _handle_action_set_message(self, message):
        ''' handle Action.ACTION_SET_MESSAGE '''
        # set the message in papyon
        self.profile.personal_message = message
        # set the message in emesene
        self.session.contacts.me.message = message
        # log the change
        contact = self.session.contacts.me
        account =  Logger.Account(contact.attrs.get('CID', None), None,
            contact.account, contact.status, contact.nick, message,
            contact.picture)

        # TODO: move to profile callbacks
        self.session.logger.log('message change', contact.status, message, account)
        self.session.add_event(Event.EVENT_MESSAGE_CHANGE_SUCCEED, message)

    def _handle_action_set_nick(self, nick):
        '''handle Action.ACTION_SET_NICK '''
        self.profile.display_name = nick
        
        # TODO: move to profile callbacks
        contact = self.session.contacts.me
        account =  Logger.Account(contact.attrs.get('CID', None), None,
            contact.account, contact.status, nick, contact.message,
            contact.picture)
        self.session.add_event(Event.EVENT_NICK_CHANGE_SUCCEED, nick)            

    def _handle_action_set_picture(self, picture_name):
        '''handle Action.ACTION_SET_PICTURE'''
        pass

    def _handle_action_set_preferences(self, preferences):
        '''handle Action.ACTION_SET_PREFERENCES
        '''
        pass

    def _handle_action_new_conversation(self, account, cid):
        ''' handle Action.ACTION_NEW_CONVERSATION '''
        #print "you opened conversation %(ci)s with %(acco)s, are you happy?" % { 'ci' : cid, 'acco' : account }
        # append cid to emesene conversations
        if account in self.conversations:
            #print "there's already a conversation with this user wtf"
            # update cid
            oldcid = self.conversations[account]
            self.conversations[account] = cid
            self.rconversations[cid] = account
            # create a papyon conversation
            contact = self.address_book.contacts.search_by('account', account)
            conv = papyon.Conversation(self, contact)
            self.papyconv[cid] = conv
            # attach the conversation event handler
            convhandler = ConversationEvent(conv, self)
            self._conversation_handler[cid] = convhandler
            
        else:
            #print "creating a new conversation et. al"
            # new emesene conversation
            self.conversations[account] = cid
            self.rconversations[cid] = account
            contact = self.address_book.contacts.search_by('account', account)
            # create a papyon conversation
            conv = papyon.Conversation(self, contact)
            self.papyconv[cid] = conv
            # attach the conversation event handler
            convhandler = ConversationEvent(conv, self)
            self._conversation_handler[cid] = convhandler

    def _handle_action_close_conversation(self, cid):
        '''handle Action.ACTION_CLOSE_CONVERSATION
        '''
        #print "you close conversation %s, are you happy?" % cid
        del self.conversations[self.rconversations[cid]]

    def _handle_action_send_message(self, cid, message):
        ''' handle Action.ACTION_SEND_MESSAGE '''
        #print "you're guin to send %(msg)s in %(ci)s" % { 'msg' : message, 'ci' : cid }
        print "type:", message
        # find papyon conversation by cid
        papyconversation = self.papyconv[cid]
        if message.type == e3.base.Message.TYPE_NUDGE:
            papyconversation.send_nudge()
            
        elif message.type == e3.base.Message.TYPE_MESSAGE:
            # format the text for papy
            formatting = formatting_e3_to_papy(message.style)
            # create papymessage
            msg = papyon.ConversationMessage(message.body, formatting)
            # send through the network
            papyconversation.send_text_message(msg)
        
        # log the message
        contact = self.session.contacts.me
        src =  Logger.Account(contact.attrs.get('CID', None), None, \
            contact.account, contact.status, contact.nick, contact.message, \
            contact.picture)

        '''if error: # isn't there a conversation event like msgid ok or fail?
            event = 'message-error'
        else:
            event = 'message'

        for dst_account in papyconversation.accounts:
            dst = self.session.contacts.get(dst_account)

            if dst is None:
                dst = e3.base.Contact(message.account)

                dest =  Logger.Account(dst.attrs.get('CID', None), None, \
                    dst.account, dst.status, dst.nick, dst.message, dst.picture)

                self.session.logger.log(event, contact.status, msgstr, 
                    src, dest)
        '''
    # p2p handlers

    def _handle_action_p2p_invite(self, cid, pid, dest, type_, identifier):
        '''handle Action.ACTION_P2P_INVITE,
         cid is the conversation id
         pid is the p2p session id, both are numbers that identify the 
            conversation and the session respectively, time.time() is 
            recommended to be used.
         dest is the destination account
         type_ is one of the e3.base.Transfer.TYPE_* constants
         identifier is the data that is needed to be sent for the invitation
        '''
        pass

    def _handle_action_p2p_accept(self, pid):
        '''handle Action.ACTION_P2P_ACCEPT'''
        pass

    def _handle_action_p2p_cancel(self, pid):
        '''handle Action.ACTION_P2P_CANCEL'''
        pass
