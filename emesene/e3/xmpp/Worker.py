''' XMPP's worker '''
# -*- coding: utf-8 -*-
#
# xmpp - an emesene extension for xmpp
#
# Copyright (C) 2009-2012 emesene
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

import os
import sys
import time
import Queue
import base64
import hashlib
import e3
import StringIO
import logging

log = logging.getLogger('xmpp.Worker')

sleekpath = os.path.abspath("e3" + os.sep + "xmpp" + os.sep + "SleekXMPP")
if os.path.exists(sleekpath):
    sys.path.insert(0, sleekpath)

import sleekxmpp as xmpp
# Python versions before 3.0 do not use UTF-8 encoding
# by default. To ensure that Unicode is handled properly
# throughout SleekXMPP, we will set the default encoding
# ourselves to UTF-8.
if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')
else:
    raw_input = input

STATUS_MAP = {}
STATUS_MAP[e3.status.BUSY] = 'dnd'
STATUS_MAP[e3.status.AWAY] = 'away'
STATUS_MAP[e3.status.IDLE] = 'xa'
STATUS_MAP[e3.status.ONLINE] = 'chat'
STATUS_MAP[e3.status.OFFLINE] = 'unavailable'

STATUS_MAP_REVERSE = {}
STATUS_MAP_REVERSE['dnd'] = e3.status.BUSY
STATUS_MAP_REVERSE['away'] = e3.status.AWAY
STATUS_MAP_REVERSE['xa'] = e3.status.IDLE
STATUS_MAP_REVERSE['chat'] = e3.status.ONLINE
STATUS_MAP_REVERSE['unavailable'] = e3.status.OFFLINE

class Worker(e3.Worker):
    '''xmpp's Worker thread'''

    def __init__(self, session, proxy, use_http=False):
        '''class constructor'''
        e3.Worker.__init__(self, session)

        self.client = None

        self.proxy = proxy
        self.proxy_data = None

        if self.proxy.use_proxy:
            self.proxy_data = {}
            self.proxy_data['host'] = self.proxy.host
            self.proxy_data['port'] = self.proxy.port

            if self.proxy.use_auth:
                self.proxy_data['username'] = self.proxy.user
                self.proxy_data['password'] = self.proxy.passwd

        self.conversations = {}
        self.rconversations = {}
        self.roster = None
        self.caches = e3.cache.CacheManager(self.session.config_dir.base_dir)

    def _session_started(self, event):
        '''Process the session_start event'''
        self.client.get_roster(block=True)
        self.client.send_presence()

        for jid in self.client.client_roster.keys():
            state = self.client.client_roster[jid]
            if jid == self.session.account.account:
                self.session.contacts.me.nick = state['name']
                self.session.nick_change_succeed(state['name'])
                continue

            if jid in self.session.contacts.contacts:
                contact = self.session.contacts.contacts[jid]
            else:
                contact = e3.Contact(jid, jid)
                self.session.contacts.contacts[jid] = contact

            avatars = self.caches.get_avatar_cache(jid)
            if 'last' in avatars:
                contact.picture = os.path.join(avatars.path, 'last')
            contact.nick = state['name']
            #TODO: Support other infos like groups, etc.
            # account, identifier=None, nick='', message=None,
            # _status=status.OFFLINE, alias='', blocked=False, cid=None

            for group in state['groups']:
                self._add_contact_to_group(contact, group)

        self.session.login_succeed()
        self.session.contact_list_ready()

    def _add_group(self, group):
        ''' method to add a group to the (gui) contact list '''
        self.session.groups[group] = e3.base.Group(group, group)

    def _add_contact_to_group(self, contact, group):
        ''' method to add a contact to a (gui) group '''
        if group not in self.session.groups.keys():
            self._add_group(group)
        self.session.groups[group].contacts.append(contact.account)
        contact.groups.append(group)

    def _change_status(self, status_):
        '''change the user status'''
        contact = self.session.contacts.me
        stat = STATUS_MAP[status_]

        self.client.send_presence(pshow=stat, pstatus=contact.message)
        e3.base.Worker._handle_action_change_status(self, status_)

    def _on_presence(self, presence):
        '''handle the reception of a presence message'''
        message = presence['status']
        show = presence.get_type()
        account = presence.get_from().bare

        #TODO: ask for vcard only when vcard-temp:x:update and photo are
        #      in presence (?)
        self.client.plugin['xep_0054'].get_vcard(jid=presence.get_from(),
            block=False, callback=self._on_vcard_get)

        stat = STATUS_MAP_REVERSE.get(show, e3.status.ONLINE)
        contact = self.session.contacts.contacts.get(account, None)

        if not contact:
            contact = e3.Contact(account)
            self.session.contacts.contacts[account] = contact

        old_message = contact.message
        old_status = contact.status
        contact.message = message
        contact.status = stat

        log_account =  e3.Logger.Account(contact.cid, None,
            contact.account, contact.status, contact.nick, contact.message,
            contact.picture)

        if old_status != stat:
            self.session.contact_attr_changed(account, 'status', old_status)
            self.session.log('status change', stat, str(stat), log_account)

        if old_message != contact.message:
            self.session.contact_attr_changed(account, 'message', old_message)
            self.session.log('message change', contact.status,
                contact.message, log_account)

    def _on_vcard_get(self, stanza):
        ''' vcard_get callback '''
        vcard_temp = stanza.get('vcard_temp')
        account = stanza.get_from().bare
        photo = vcard_temp['PHOTO']
        if not photo:
            return
        photo_bin = photo.get('BINVAL')
        if not photo_bin:
            return
        photo_hash = hashlib.sha1()
        photo_hash.update(photo_bin)
        photo_hash = photo_hash.hexdigest()

        ctct = self.session.contacts.get(account)
        avatars = self.caches.get_avatar_cache(account)
        avatar_path = os.path.join(avatars.path, photo_hash)
        ctct.picture = avatar_path

        if photo_hash not in avatars:
            avatars.insert_raw(StringIO.StringIO(photo_bin))

        self.session.picture_change_succeed(account, avatar_path)

    def _on_message(self, message):
        '''handle the reception of a message'''
        if message['type'] not in ('chat', 'normal'):
            log.error("Unhandled message: %s" % message)
            return

        body = message['body']
        account = message['from'].bare

        if account in self.conversations:
            cid = self.conversations[account]
        else:
            cid = time.time()
            self.conversations[account] = cid
            self.rconversations[cid] = [account]
            self.session.conv_first_action(cid, [account])

        if body is None:
            type_ = e3.Message.TYPE_TYPING
        else:
            type_ = e3.Message.TYPE_MESSAGE

        msgobj = e3.Message(type_, body, account)
        self.session.conv_message(cid, account, msgobj)
        # log message
        e3.Logger.log_message(self.session, None, msgobj, False)

    # mailbox handlers
    def _on_mailbox_unread_mail_count_changed(self, unread_mail_count,
            initial):

        log.info("Mailbox count changed (initial? %s): %s" % (initial,
            unread_mail_count))
        self.session.mail_count_changed(unread_mail_count)

    def _on_mailbox_new_mail_received(self, mail_message):
        log.info("New mailbox message received: %s" % mail_message)
        self.session.mail_received(mail_message)

    def _on_social_external_request(self, conn_url):
        self.session.social_request(conn_url)

    # action handlers
    def _handle_action_quit(self):
        '''handle Action.ACTION_QUIT
        '''
        #chain up to base class
        e3.base.Worker._handle_action_quit(self)
        self.session.disconnected(None, False)
        self.client.disconnect(wait=True)

    def _handle_action_add_contact(self, account):
        '''handle Action.ACTION_ADD_CONTACT
        '''
        pass

    def _handle_action_add_group(self, name):
        '''handle Action.ACTION_ADD_GROUP
        '''
        pass

    def _handle_action_add_to_group(self, account, gid):
        '''handle Action.ACTION_ADD_TO_GROUP
        '''
        pass

    def _handle_action_block_contact(self, account):
        '''handle Action.ACTION_BLOCK_CONTACT
        '''
        pass

    def _handle_action_unblock_contact(self, account):
        '''handle Action.ACTION_UNBLOCK_CONTACT
        '''
        pass

    def _handle_action_change_status(self, status_):
        '''handle Action.ACTION_CHANGE_STATUS
        '''
        self._change_status(status_)

    def _handle_action_login(self, account, password, status_, host, port):
        '''handle Action.ACTION_LOGIN
        '''
        self.my_avatars = self.caches.get_avatar_cache(
                self.session.account.account)

        self.client = xmpp.ClientXMPP(account, password)
        self.client.process(block=False)
        self.client.register_plugin('xep_0004') # Data Forms
        self.client.register_plugin('xep_0030') # Service Discovery
        self.client.register_plugin('xep_0054') # vcard-temp
        self.client.register_plugin('xep_0060') # PubSub
        # MSN will kill connections that have been inactive for even
        # short periods of time. So use pings to keep the session alive;
        # whitespace keepalives do not work.
        if not self.session._is_facebook:
            self.client.register_plugin('xep_0199', {'keepalive': True, 'frequency': 60})

        self.client.add_event_handler('session_start', self._session_started)
        self.client.add_event_handler('changed_status', self._on_presence)
        self.client.add_event_handler('message', self._on_message)

        self.client.connect((host, port))

        self.session.login_started()

    def _handle_action_logout(self):
        '''handle Action.ACTION_LOGOUT
        '''
        self.client.disconnect(wait=True)

    def _handle_action_move_to_group(self, account, src_gid, dest_gid):
        '''handle Action.ACTION_MOVE_TO_GROUP
        '''
        pass

    def _handle_action_remove_contact(self, account):
        '''handle Action.ACTION_REMOVE_CONTACT
        '''
        pass

    def _handle_action_reject_contact(self, account):
        '''handle Action.ACTION_REJECT_CONTACT
        '''
        pass

    def _handle_action_remove_from_group(self, account, gid):
        '''handle Action.ACTION_REMOVE_FROM_GROUP
        '''
        pass

    def _handle_action_remove_group(self, gid):
        '''handle Action.ACTION_REMOVE_GROUP
        '''
        pass

    def _handle_action_rename_group(self, gid, name):
        '''handle Action.ACTION_RENAME_GROUP
        '''
        pass

    def _handle_action_set_contact_alias(self, account, alias):
        '''handle Action.ACTION_SET_CONTACT_ALIAS
        '''
        pass

    def _handle_action_set_message(self, message):
        '''handle Action.ACTION_SET_MESSAGE
        '''
        contact = self.session.contacts.me
        stat = STATUS_MAP[contact.status]

        self.client.send_presence(pshow=stat, pstatus=contact.message)

        if self.session.facebook_client and self.session.config.b_fb_status_write:
            # update facebook message
            self.session.facebook_client.message = message

        e3.base.Worker._handle_action_set_message(self, message)

    def _handle_action_set_media(self, message):
        '''handle Action.ACTION_SET_MEDIA
        '''
        contact = self.session.contacts.me
        stat = STATUS_MAP[contact.status]

        self.client.send_presence(pshow=stat, pstatus=contact.message)

        e3.base.Worker._handle_action_set_media(self, message)

    def _handle_action_set_nick(self, nick):
        '''handle Action.ACTION_SET_NICK
        '''
        pass

    def _handle_action_set_picture(self, picture_name):
        '''handle Action.ACTION_SET_PICTURE
        '''
        avatar = self._filedata_to_string(picture_name)
        vcard = self.client.plugin['xep_0054'].make_vcard()
        if avatar:
            vcard['PHOTO']['BINVAL'] = avatar
        else: # set empty photo
            vcard['PHOTO'] = ''

        self.client.plugin['xep_0054'].publish_vcard(vcard, block=False)

        if not avatar:
            return # TODO: reset avatar locally and remove it from the UI

        avatar_hash = hashlib.sha1(avatar).hexdigest().encode("hex")

        if avatar_hash in self.my_avatars:
            avatar_path = os.path.join(self.my_avatars.path, avatar_hash)
            self.session.picture_change_succeed(self.session.account.account,
                    avatar_path)
            self.session.contacts.me.picture = avatar_path
        else:
            result = self.my_avatars.insert_raw(StringIO.StringIO(avatar))
            if result:
                avatar_hash = result[1]
                avatar_path = os.path.join(self.my_avatars.path, avatar_hash)
                self.session.picture_change_succeed(self.session.account.account,
                        avatar_path)
                self.session.contacts.me.picture = avatar_path

    def _handle_action_new_conversation(self, account, cid):
        '''handle Action.ACTION_NEW_CONVERSATION
        '''
        self.conversations[account] = cid
        self.rconversations[cid] = [account]

    def _handle_action_close_conversation(self, cid):
        '''handle Action.ACTION_CLOSE_CONVERSATION
        '''
        if cid in self.rconversations:
            account = self.rconversations[cid][0]
            del self.conversations[account]
            del self.rconversations[cid]
        else:
            log.warning('Conversation %s not found' % cid)

    def _handle_action_send_message(self, cid, message):
        '''handle Action.ACTION_SEND_MESSAGE
        cid is the conversation id, message is a Message object
        '''

        recipients = self.rconversations.get(cid, ())
        for recipient in recipients:
            self.client.send_message(recipient, message.body)

        e3.Logger.log_message(self.session, recipients, message, True)

