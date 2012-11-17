import os
import sys
import ssl
import time
import Queue
import base64
import hashlib
import e3
import StringIO
import logging


import libwebqqboost as webqqboost
try:
    import simplejson as json
except ImportError , e:
    import json

log = logging.getLogger('WebQQ.Worker')

STATUS_MAP = {}
STATUS_MAP[e3.status.BUSY] = 'busy'
STATUS_MAP[e3.status.AWAY] = 'away'
STATUS_MAP[e3.status.IDLE] = 'silent'
STATUS_MAP[e3.status.ONLINE] = 'online'
STATUS_MAP[e3.status.OFFLINE] = 'offline'

STATUS_MAP_REVERSE = {}
STATUS_MAP_REVERSE['busy'] = e3.status.BUSY
STATUS_MAP_REVERSE['away'] = e3.status.AWAY
STATUS_MAP_REVERSE['silent'] = e3.status.IDLE
STATUS_MAP_REVERSE['online'] = e3.status.ONLINE
STATUS_MAP_REVERSE['offline'] = e3.status.OFFLINE

PHOTO_TYPES = {
    'image/png': '.png',
    'image/jpg': '.jpg',
    'image/jpeg': '.jpg',
    'image/gif': '.gif',
    'image/bmp': '.bmp',
    }

class Worker(e3.Worker):
    '''webqq's Worker thread'''

    webqq_plugin = None
    res_manager = None

    def __init__(self, session, proxy, use_http=False, use_ipv6=False):
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

        singleton = webqqboost.SingletonInstance()
        self.webqq_plugin = singleton.getQQPluginSingletonInstance()
        self.res_manager = singleton.getResManagerSingletonInstance()

    def run(self):
        '''main method, block waiting for data, process it, and send data back
        '''

        call_back_dict = { 512 : self._on_message, 513 : self._on_group_message,
                           515 : self._on_photo_update , 516 : self._on_status_change,
                           517 : self._on_nick_update , 518 : self._on_shake_message}

        while self._continue :
            try:
                event_queue = self.res_manager.event_queue
                if not event_queue.empty() :
                    self.res_manager.lock()
                    while not event_queue.empty():
                        item = event_queue.pop()
                        try:
                            call_back_dict[item[0]](item[1])
                        except KeyError , e:
                            log.error('Un implemented callback function')

                    self.res_manager.ulock()

                action = self.session.actions.get(True, 0.1)
                self._process_action(action)

            except Queue.Empty:
                pass

    def _session_started(self):

        categories_dict = {}
        default_group = e3.Group('Friends','Friends')
        group_group = e3.Group('Groups', 'Groups')
        categories_dict[0] = default_group
        categories_dict[-1] = group_group

        for index in self.res_manager.categories:
            key = index.key()
            group = e3.Group( self.res_manager.categories[key].name, key)
            categories_dict[key] = group

        for uin in self.res_manager.contacts:
            key =  uin.key()
            #nick = self.res_manager.contacts[uin].nick
            _status = e3.status.OFFLINE
            try:
                if not self.res_manager.contacts[key].status  == '':
                    _status = STATUS_MAP_REVERSE[self.res_manager.contacts[key].status]
            except KeyError , e:
                _stauts = e3.status.ONLINE

            contact = e3.Contact(account = key, identifier = str(key),  message = self.res_manager.contacts[key].lnick, _status = _status, blocked = False, cid = key)

            index = self.res_manager.contacts[key].cate_index
            group = categories_dict[index]
            self._add_contact_to_group( contact, group.name )
            self.session.contacts.contacts[key] = contact

        for group_id in self.res_manager.groups:
            group_id_key = group_id.key()
            _status = e3.status.ONLINE
            contact = e3.Contact(account = group_id_key, identifier = str(group_id_key), nick =  self.res_manager.groups[group_id_key].name ,
                                 message = self.res_manager.groups[group_id_key].memo,  _status = _status, blocked = False, cid = group_id_key)
            self._add_contact_to_group(contact, group_group.name)

            self.session.contacts.contacts[group_id_key] = contact
            
            '''
            for uins in self.res_manager.group_contacts[group_id_key]:
                uin_key = uins.key()
                buddy = self.res_manager.group_contacts[group_id_key][uin_key]
                uin = buddy.uin
                _status = e3.status.ONLINE
                contact = e3.Contact(account = uin, identifier = str(uin),  nick = buddy.nick, message = buddy.lnick  , _status = _status, blocked = False, cid = uin)
                #self.session.contacts.contacts[uin] = contact
            '''
            
        self.session.login_succeed()
        self.session.contact_list_ready()

    def _change_status(self, status_):
        '''change the user status'''
        contact = self.session.contacts.me
        stat = STATUS_MAP[status_]
        self.webqq_plugin.change_status(stat)
        e3.base.Worker._handle_action_change_status(self, status_)


    def _on_message(self, message):
        '''handle the reception of a message'''
        data = json.loads(message)

        from_uin = str(data['from_uin'])

        account = from_uin
        body = data['content'][-1]
        type_ = e3.Message.TYPE_MESSAGE

        if account in self.conversations:
            cid = self.conversations[account]
        else:
            cid = time.time()
            self.conversations[account] = cid
            self.rconversations[cid] = [account]
            self.session.conv_first_action(cid, [account])

        msgobj = e3.Message(type_, body, account)
        self.session.conv_message(cid, account, msgobj)

        # log message
        e3.Logger.log_message(self.session, None, msgobj, False)

    def _on_group_message(self, message):
        data = json.loads(message)
        group_code = str(data["group_code"])
        send_uin = str(data["send_uin"])
        body = data['content'][-1]
        display_name=send_uin

        for group in self.res_manager.group_contacts:
            group_key = group.key()
            try:
                display_name = self.res_manager.group_contacts[group_key][send_uin].nick
                break
            except KeyError, e:
                log.error("Can not get group buddy display name")
                pass

        account = group_code
        if account in self.conversations:
            cid = self.conversations[account]
        else:
            cid = time.time()
            self.conversations[account] = cid
            self.rconversations[cid] = [account]
            self.session.conv_first_action(cid, [account])

        type_ = e3.Message.TYPE_MESSAGE
        msgobj = e3.Message(type_, body, display_name)
        self.session.conv_message(cid, display_name, msgobj)
        e3.Logger.log_message(self.session, None, msgobj, False)


    def _on_nick_update(self, value):
        data = json.loads(value)
        uin = str(data["uin"])
        nick = data["nick"]
        contact = self.session.contacts.contacts.get(uin, None)

        if contact is None:
            return
        account = uin
        old_nick = contact.nick
        status_ = contact.status

        log_account = e3.Logger.Account(contact.cid, None, contact.account, contact.status, contact.nick, contact.message, contact.picture)
        if not nick == "" :
           contact.nick = nick
           contact.alias = nick
           self.session.contact_attr_changed(account, 'nick', old_nick)
           self.session.log('nick change', status_, nick,  log_account)

        if contact.account  == self.session.account.account :
            me = self.session.contacts.me
            log_account =e3.Logger.Account(me.cid, None, me.account,
                                         me.status, nick, me.message, me.picture)
            self.session.log('nick change', contact.status, nick,
                             log_account)
            self.session.contacts.me.nick = nick
            self.session.contacts.me.alias = nick

            e3.base.Worker._handle_action_set_message(self, self.res_manager.contacts[me.account].lnick)
            self.session.nick_change_succeed(nick)

    def _on_status_change(self, value):
        data = json.loads(value)
        uin = str(data["uin"])
        status_ = data["status"]
        contact = self.session.contacts.contacts.get(uin, None)
        if contact is None:
            return
        account = uin
        old_status = contact.status
        stat = None
        try:
            stat = STATUS_MAP_REVERSE[status_]
        except:
            stat = e3.status.ONLINE
        contact.status = stat
        self.session.contact_attr_changed(account, 'status', old_status)

        acc = e3.Logger.Account.from_contact(self.session.contacts.me)
        self.session.log('status change', contact.status,
                         old_status, acc)

    def _on_photo_update(self, uin):
        account = uin
        photo_bin = self.res_manager.contacts[account].face

        contact = self.session.contacts.contacts.get(account, None)
        if contact is None:
            return
        if not photo_bin:
            return
        photo_hash = hashlib.sha1()
        photo_hash.update(photo_bin)
        photo_hash = photo_hash.hexdigest()

        ctct = self.session.contacts.get(account)
        avatars = None
        qqnumber = None

        try:
            qqnumber = self.res_manager.contacts[account].qqnumber
        except KeyError, e:
            try:
                qqnumber = self.res_manager.groups[account].gnumber
            except KeyError, e:
                qqnumber = None

        if qqnumber is None:
            avatars = self.session.caches.get_avatar_cache(account)
        else:
            avatars = self.session.caches.get_avatar_cache(qqnumber)
        avatar_path = os.path.join(avatars.path, photo_hash)
        ctct.picture = avatar_path

        if photo_hash not in avatars:
            avatars.insert_raw(StringIO.StringIO(photo_bin))

        self.session.picture_change_succeed(account, avatar_path)


    def _on_shake_message(self, value):

        data = json.loads(value)
        from_uin = data["from_uin"]
        account = str(from_uin)
        contact = self.session.contacts.contacts.get(account, None)
        if contact is None:
            return

        if account in self.conversations:
            cid = self.conversations[account]
        else:
            cid = time.time()
            self.conversations[account] = cid
            self.rconversations[cid] = [account]
            self.session.conv_first_action(cid, [account])


        msgobj = e3.Message(e3.Message.TYPE_MESSAGE,
                            '%s requests your attention' % (contact.nick, ), account)
        self.session.conv_message(cid, account, msgobj)
        # log message
        e3.Logger.log_message(self.session, None, msgobj, False)

    def _on_contact_jabber_changed(self, session, stanza):
        pass
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

    def _add_group(self, group):
        self.session.groups[group] = e3.base.Group(group, group)

    def _add_contact_to_group(self, contact, group):
        ''' method to add a contact to a (gui) group '''
        if group not in self.session.groups.keys():
            self._add_group(group)
        self.session.groups[group].contacts.append(contact.account)
        contact.groups.append(group)

    # action handlers
    def _handle_action_quit(self):
        '''handle Action.ACTION_QUIT
        '''
        e3.base.Worker._handle_action_quit(self)
        self.session.disconnected(None, False)

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
        
        self.session.account.account = account
        self.session.account.password = password
        self.session.account.status = status_
        self.session.contacts.me.status = status_
        
        if self.webqq_plugin.webqq_login(account, password,"online") :
            self._session_started()
            self.session.login_started()

    def _handle_action_logout(self):
        '''handle Action.ACTION_LOGOUT
        '''
        pass

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
        
        self.webqq_plugin.set_long_nick(message)
        e3.base.Worker._handle_action_set_message(self, message)
        
    def _handle_action_set_media(self, message):
        '''handle Action.ACTION_SET_MEDIA
        '''
        pass

    def _handle_action_set_nick(self, nick):
        '''handle Action.ACTION_SET_NICK
        '''
        pass

    def _handle_action_set_picture(self, picture_name):
        '''handle Action.ACTION_SET_PICTURE
        '''
        pass

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
            log.warning('conversation %s not found' % cid)

    def _handle_action_send_message(self, cid, message):

        '''handle Action.ACTION_SEND_MESSAGE
        cid is the conversation id, message is a Message object
        '''
        if message.type not in (e3.Message.TYPE_MESSAGE, e3.Message.TYPE_TYPING,
           e3.Message.TYPE_NUDGE):
            return # Do NOT process other message types

        recipients = self.rconversations.get(cid, ())

        for recipient in recipients:
            group_keys = []
            for group in self.res_manager.groups:
                group_keys.append(group.key())
            if str(recipient) in group_keys:
                self.webqq_plugin.send_group_message( str(recipient), str(message.body))
            else:
                self.webqq_plugin.send_buddy_message( str(recipient), str(message.body))
            # log message
        e3.Logger.log_message(self.session, recipients, message, True)

    # p2p handlers

    def send_buddy_nudge(self, cid):
        recipients = self.rconversations.get(cid, ())
        for recipient in recipients:
            self.webqq_plugin.send_buddy_nudge(str(recipient))

    def _handle_action_p2p_invite(self, cid, pid, dest, type_, identifier):
        '''handle Action.ACTION_P2P_INVITE,
         cid is the conversation id
         pid is the p2p session id, both are numbers that identify the
            conversation and the session respectively, time.time() is
            recommended to be used.
         dest is the destination account
         type_ is one of the e3.Transfer.TYPE_* constants
         identifier is the data that is needed to be sent for the invitation
        '''
        pass

    def _handle_action_p2p_accept(self, pid):
        '''handle Action.ACTION_P2P_ACCEPT'''
        pass

    def _handle_action_p2p_cancel(self, pid):
        '''handle Action.ACTION_P2P_CANCEL'''
        pass
