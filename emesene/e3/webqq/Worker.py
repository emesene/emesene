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
import libwebqqpython
import simplejson as json

log = logging.getLogger('WebQQ.Worker')

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
STATUS_MAP[e3.status.BUSY] = 'busy'
STATUS_MAP[e3.status.AWAY] = 'away'
STATUS_MAP[e3.status.IDLE] = 'xa'
STATUS_MAP[e3.status.ONLINE] = 'chat'
STATUS_MAP[e3.status.OFFLINE] = 'unavailable'

STATUS_MAP_REVERSE = {}
STATUS_MAP_REVERSE['busy'] = e3.status.BUSY
STATUS_MAP_REVERSE['away'] = e3.status.AWAY
STATUS_MAP_REVERSE['xa'] = e3.status.IDLE
STATUS_MAP_REVERSE['chat'] = e3.status.ONLINE
STATUS_MAP_REVERSE['unavailable'] = e3.status.OFFLINE

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
    nick_uin_map = {}
    uin_nick_map = {}   
    def __init__(self, app_name, session, proxy, use_http=False, use_ipv6=False):
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
        self.caches = e3.cache.CacheManager(self.session.config_dir.base_dir)
        
        self. webqq_plugin = libwebqqpython.SingletonQQPlugin_getInstance()
        self.res_manager = libwebqqpython.SingletonResourceManager_getInstance()
        
    def run(self):
        '''main method, block waiting for data, process it, and send data back
        '''
        while self._continue == True:
            try:
                event_queue = self.res_manager.event_queue
                if not event_queue.empty() :
                    self.res_manager.lock()
                    while not event_queue.empty():
                        item = event_queue.pop()
        
                        if item[0] == libwebqqpython.ON_BUDDY_MESSAGE :
                            
                            self._on_message(item[1])
                        elif item[0] == libwebqqpython.ON_NICK_CHANGE:

                            self._on_nick_update(item[1])
                            
                        else:
                            print 'Un implementation callback functions'
                            
                    self.res_manager.ulock()
                    
                action = self.session.actions.get(True, 0.1)
                self._process_action(action)

            except Queue.Empty:
                pass

    def _session_started(self):
        """
        Process the session_start event.

        Typical actions for the session_start event are
        requesting the roster and broadcasting an initial
        presence stanza.

        Arguments:
            event -- An empty dictionary. The session_start
                     event does not provide any additional
                     data.
        """
      
        categories_dict = {}
        default_group = e3.Group('Friends','Friends')
        categories_dict[0] = default_group
        
        for index in self.res_manager.categories.keys():
            group = e3.Group( self.res_manager.categories[index].name, index)
            categories_dict[index] = group
            
        for uin in self.res_manager.contacts.keys():
            #nick = self.res_manager.contacts[uin].nick
            _status = e3.status.OFFLINE
            if not self.res_manager.contacts[uin].status  == '':
                _status = e3.status.ONLINE
                
            contact = e3.Contact(account = uin, identifier = int(uin),  message = self.res_manager.contacts[uin].lnick, _status = _status, blocked = False, cid = uin)
            '''
            if contact.cid  == self.session.account.account :
                self.session.contacts.me.nick = nick
                self.session.nick_change_succeed(nick)
                continue
            '''
            index = self.res_manager.contacts[uin].cate_index
            group = categories_dict[index]
            self._add_contact_to_group( contact, group.name )
            self.session.contacts.contacts[uin] = contact
            #self.nick_uin_map[nick] = uin
       	    #self.uin_nick_map[uin] = nick
            
        self.session.login_succeed()
        self.session.contact_list_ready()

    def _change_status(self, status_):
        '''change the user status'''
        contact = self.session.contacts.me
        stat = STATUS_MAP[status_]

        e3.base.Worker._handle_action_change_status(self, status_)


    def _on_message(self, message):
        '''handle the reception of a message'''
        data = json.loads(message)
                            
        from_uin = str(data['from_uin'])
        #account = self.uin_nick_map[from_uin]
        
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
        print 'log message'
        e3.Logger.log_message(self.session, None, msgobj, False)

    def _on_nick_update(self, value):
        data = json.loads(value)
        uin = data["uin"]
        nick = data["nick"]
        print nick
        contact = self.session.contacts.contacts.get(uin, None)
        account = uin
        old_nick = contact.nick
        if not contact:
            contact = e3.Contact(account)
            self.session.contacts.contacts[account] = contact

        if contact.cid  == self.session.account.account :
                self.session.contacts.me.nick = nick
                self.session.nick_change_succeed(nick)
        
        status_ = contact.status
        log_account = e3.Logger.Account(contact.cid, None, contact.account, contact.status, contact.nick, contact.message, contact.picture)
        if not nick == "" :
           contact.nick = nick
           contact.alias = nick
           self.session.contact_attr_changed(account, 'nick', old_nick)
           self.session.log('nick change', status_, nick,  log_account)
        
        
    def _on_photo_update(self, session, stanza):
        pass
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
        log.debug('closing thread')
        self.session.events.queue.clear()
        self.session.logger.quit()
        self.session.signals.quit()
        self._continue = False
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
        self.my_avatars = self.caches.get_avatar_cache(
                self.session.account.account)

        if self.webqq_plugin.webqq_login(account, password) is True:
            print "Login Success"
        else:
            print "Login Fail"
        ### Fix this if login fail
        
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
        pass

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
	print "New conversation account : %s, cid : %s" %(account, cid)
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

        recipients = self.rconversations.get(cid, ())
        print "Message : " +message.body
        
        for recipient in recipients:
	    #recipient = self.nick_uin_map[nick]
            self.webqq_plugin.send_buddy_message( str(recipient), str(message.body))
            # log message
        e3.Logger.log_message(self.session, recipients, message, True)

    # p2p handlers

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
