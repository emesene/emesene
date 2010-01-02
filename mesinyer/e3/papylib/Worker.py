''' papylib's worker - an emesene extension for papyon library '''
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

import gobject
import hashlib
import os
import Queue
import random
import shutil
import sys
import time

from e3 import cache
import e3.base.Contact
import e3.base.Group
import e3.base.Message
import e3.base.Worker
from e3.base import status
from e3.base.Action import Action
from e3.base.Event import Event
import e3.base.Logger as Logger
from e3.common import ConfigDir

import logging
log = logging.getLogger('papylib.Worker')

try:
    REQ_VER = (0, 4, 3)
    # papyon imports
    # get the deb from http://packages.debian.org/sid/python-papyon
    import logging
    import papyon
    import papyon.event
    import papyon.util.string_io as StringIO
    papyver = papyon.version
    if papyver[1] < REQ_VER[1] or papyver[2] < REQ_VER[2]:
        raise Exception
except Exception, e:
    log.exception("You need python-papyon(>=%s.%s.%s) to be installed " \
                  "in order to use this extension" % REQ_VER)
from PapyEvents import *
from PapyConvert import *
from PapyConference import *
    
#logging.basicConfig(level=logging.DEBUG)

class Worker(e3.base.Worker, papyon.Client):
    ''' papylib's worker - an emesene extension for papyon library '''

    def __init__(self, app_name, session, proxy, use_http=False):
        '''class constructor'''
        e3.base.Worker.__init__(self, app_name, session)
        self.session = session
        server = ('messenger.hotmail.com', 1863)

        if use_http:
            from papyon.transport import HTTPPollConnection
            self.client = papyon.Client.__init__( \
               self, server, get_proxies(), HTTPPollConnection)
        else:
            self.client = papyon.Client.__init__( \
               self, server, proxies = get_proxies())

        self._event_handler = ClientEvents(self)
        self._contact_handler = ContactEvent(self)
        self._invite_handler = InviteEvent(self)
        self._abook_handler = AddressBookEvent(self)
        self._profile_handler = ProfileEvent(self)
        self._oim_handler = OfflineEvent(self)
        # this stores account : cid
        self.conversations = {}
        # this stores cid : account
        self.rconversations = {}
        # this stores papyon conversations as cid : conversation
        self.papyconv = {}
        # this stores conversation handlers
        self._conversation_handler = {}

        self.caches = e3.cache.CacheManager(self.session.config_dir.base_dir)

    def run(self):
        '''main method, block waiting for data, process it, and send data back
        '''
        self._mainloop = gobject.MainLoop(is_running=True)
        while self._mainloop.is_running():
            try:
                action = self.session.actions.get(True, 0.1)

                if action.id_ == Action.ACTION_QUIT:
                    log.debug('closing thread')
                    self.logout()
                    self.session.logger.quit()
                    break

                self._process_action(action)
            except Queue.Empty:
                pass

    # some useful methods
    def set_initial_infos(self):
        '''this is called on login'''
        # loads or create a config for this session
        self.session.load_config()
        self.session.create_config()
        # sets the login-chosen presence in papyon
        presence = self.session.account.status
        self._set_status(presence)

        return
        message = self.profile.personal_message
        displaypic = self.profile.msn_object
        print "Initial infos:", nick, message, displaypic, presence
        
    def _set_status(self, stat):
        ''' changes the presence in papyon given an e3 status '''
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

    def _fill_contact_list(self, abook):
        ''' fill the contact list with papy contacts '''
        for group in abook.groups:
            self._add_group(group.name)

        for contact in abook.contacts:
            self._add_contact(contact.account, contact.display_name, \
                STATUS_PAPY_TO_E3[contact.presence], contact.personal_message, \
                False)
                # TODO: 'BLOCKED' in contact.memberships)
                # TODO: eventual friendly name (alias)
            for group in contact.groups:
                self._add_contact_to_group(contact.account, group.name)

        self.session.add_event(Event.EVENT_CONTACT_LIST_READY)

    def _add_contact(self, mail, nick, status_, message, blocked, alias=''):
        ''' helper method to add a contact to the (gui) contact list '''
        # wtf, why 2 mails?
        contact = e3.base.Contact(\
            mail, mail, nick, message, status_, alias, blocked)
        self.session.contacts.contacts[mail] = contact

        avatars = self.caches.get_avatar_cache(mail)
        if 'last' in avatars:
            contact.picture = os.path.join(avatars.path, 'last')

    def _add_group(self, name):
        ''' method to add a group to the (gui) contact list '''
        self.session.groups[name] = e3.base.Group(name, name)

    def _add_contact_to_group(self, account, group):
        ''' method to add a contact to a (gui) group '''
        self.session.groups[group].contacts.append(account)
        self.session.contacts.contacts[account].groups.append(group)

    # invite handlers
    def _on_conversation_invite(self, papyconversation):
        ''' create a cid and append the event handler to papyconv dict '''
        cid = time.time()
        newconversationevent = ConversationEvent(papyconversation, self)
        self._conversation_handler[cid] = newconversationevent

    def _on_webcam_invite(self, session, producer):
        print "New webcam invite", session, producer
        websess = MediaSessionHandler(session.media_session)
        if 0:
            session.reject()
        else:
            session.accept()
                
    def _on_conference_invite(self, call):
        print "New conference invite", call
        callhandler = CallEvent(call)
        callsess = MediaSessionHandler(call.media_session)
        print "new call session", callsess
        if 0:
            call.reject()            
        else:
            call.accept()

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

        emotes = self.caches.get_emoticon_cache(account)
        def download_failed(reason):
            print reason

        def download_ok(msnobj, download_failed_func):
            emotes.insert_raw((msnobj._friendly, msnobj._data))
            self.session.add_event(Event.EVENT_P2P_FINISHED, \
                account, 'emoticon', emoticon_path)

        for shortcut, msn_object in papymessage.msn_objects.iteritems():
            cedict[shortcut] = None

            emoticon_hash = msn_object._data_sha.encode("hex")
            emoticon_path = os.path.join(emotes.path, emoticon_hash)

            if emoticon_hash in emotes:
                cedict[shortcut] = emoticon_path
            else:
                self.msn_object_store.request(msn_object, \
                    (download_ok, download_failed))

        self.session.add_event(\
            Event.EVENT_CONV_MESSAGE, cid, account, msgobj, cedict)

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

    def _on_conversation_message_error(self, err_type, error, papyconversation):
        print "error sending message because", err_type, error
        
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
                contact.message, Logger.Account(contact.attrs.get('CID', None),\
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
        msn_object = contact.msn_object
        if msn_object._type == papyon.p2p.MSNObjectType.DISPLAY_PICTURE:
            avatars = self.caches.get_avatar_cache(contact.account)
            avatar_hash = msn_object._data_sha.encode("hex")
            avatar_path = os.path.join(avatars.path, avatar_hash)

            if avatar_hash in avatars:
                self.session.add_event(Event.EVENT_PICTURE_CHANGE_SUCCEED,
                        contact.account, avatar_path)
                return avatar_path

            def download_failed(reason):
                print reason

            def download_ok(msnobj, callback):
                avatars.insert_raw(msnobj._data)
                ctct = self.session.contacts.get(contact.account)

                if ctct:
                    ctct.picture = avatar_path

                self.session.add_event(Event.EVENT_PICTURE_CHANGE_SUCCEED,
                        contact.account, avatar_path)

            if msn_object._type not in (
                    papyon.p2p.MSNObjectType.DYNAMIC_DISPLAY_PICTURE,
                        papyon.p2p.MSNObjectType.DISPLAY_PICTURE):
                return

            if avatar_hash not in avatars:
                self.msn_object_store.request(msn_object, \
                    (download_ok, download_failed))

    # address book events
    def _on_addressbook_messenger_contact_added(contact):
        print "contact added", contact
    def _on_addressbook_contact_deleted(self, contact):
        print "contact deleted", contact
    def _on_addressbook_contact_blocked(self, contact):
        print "contact blocked", contact
    def _on_addressbook_contact_unblocked(self, contact):
        print "contact unblocked", contact
    def _on_addressbook_group_added(self, group):
        print "group added", group
    def _on_addressbook_group_deleted(self, group):
        print "group deleted", group
    def _on_addressbook_group_renamed(self, group):
        print "group renamed", group
    def _on_addressbook_group_contact_added(self, group, contact):
        print "group contact added", group, contact
    def _on_addressbook_group_contact_deleted(self, group, contact):
        print "group contact deleted", group, contact

    # profile events
    def _on_profile_presence_changed(self):
        """Called when the presence changes."""
        pass
        
    def _on_profile_display_name_changed(self):
        """Called when the display name changes."""
        self.session.display_name = "asd"
        self._handle_action_set_nick(self.profile.display_name)

    def _on_profile_personal_message_changed(self):
        """Called when the personal message changes."""
        print "pm", self.profile.personal_message

    def _on_profile_current_media_changed(self):
        """Called when the current media changes."""
        print "currentmedia", self.profile.personal_message

    def _on_profile_msn_object_changed(self):
        """Called when the MSNObject changes."""
        print "on profile msn obj changed"
        msn_object = self.profile.msn_object
        if msn_object is not None:
            self._handle_action_set_picture(msn_object)
    
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
        self.session.logger.log(\
            'message change', contact.status, message, account)
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
        if isinstance(picture_name, papyon.p2p.MSNObject):
            # this is/can be used for initial avatar changing and caching
            # like dp roaming and stuff like that
            # now it doesn't work, btw
            self.profile.msn_object = picture_name
            self._on_contact_msnobject_changed(self.session.contacts.me)
            #self.session.contacts.me.picture = picture_name
            #self.session.add_event(e3.Event.EVENT_PICTURE_CHANGE_SUCCEED,
            #    self.session.account.account, picture_name)
            return

        try:
            f = open(picture_name, 'r')
            avatar = f.read()
            f.close()
        except:
            return

        if not isinstance(avatar, str):
            avatar = "".join([chr(b) for b in avatar])
        msn_object = papyon.p2p.MSNObject(self.profile,
                         len(avatar),
                         papyon.p2p.MSNObjectType.DISPLAY_PICTURE,
                         hashlib.sha1(avatar).hexdigest() + '.tmp',
                         "",
                         data=StringIO.StringIO(avatar))
        self.profile.msn_object = msn_object

        self.session.contacts.me.picture = picture_name
        self.session.add_event(e3.Event.EVENT_PICTURE_CHANGE_SUCCEED,
                self.session.account.account, picture_name)

    def _handle_action_set_preferences(self, preferences):
        '''handle Action.ACTION_SET_PREFERENCES
        '''
        pass

    def _handle_action_new_conversation(self, account, cid):
        ''' handle Action.ACTION_NEW_CONVERSATION '''
        #print "you opened conversation %(ci)s with %(acco)s, are you happy?" \
        # % { 'ci' : cid, 'acco' : account }
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
        #print "you're guin to send %(msg)s in %(ci)s" % \
        #{ 'msg' : message, 'ci' : cid }
        #print "type:", message
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
