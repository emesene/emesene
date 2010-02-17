import sys
import time
import xmpp
import Queue

import e3

import logging
log = logging.getLogger('jabber.Worker')

class Worker(e3.Worker):
    '''wrapper of xmpppy to make it work like e3.Worker'''

    NOTIFICATION_DELAY = 60

    def __init__(self, app_name, session, proxy, use_http=False):
        '''class constructor'''
        e3.Worker.__init__(self, app_name, session)
        self.jid = xmpp.protocol.JID(session.account.account)
        #self.client = xmpp.Client(self.jid.getDomain(), debug=[])
        self.client = xmpp.Client(self.jid.getDomain(), debug=['always'])

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
        self.start_time = None

    def run(self):
        '''main method, block waiting for data, process it, and send data back
        '''
        data = None

        while True:
            if hasattr(self.client, 'Process'):
                self.client.Process(1)

            try:
                action = self.session.actions.get(True, 0.1)

                if action.id_ == e3.Action.ACTION_QUIT:
                    log.debug('closing thread')
                    self.session.logger.quit()
                    break

                self._process_action(action)
            except Queue.Empty:
                pass

    def _on_presence(self, client, presence):
        '''handle the reception of a presence message'''
        message = presence.getStatus() or ''
        show = presence.getShow()
        type_ = presence.getType()
        account = presence.getFrom().getStripped()

        if type_ == 'unavailable':
            stat = e3.status.OFFLINE
        elif show == 'away':
            stat = e3.status.AWAY
        elif show == 'dnd':
            stat = e3.status.BUSY
        else:
            stat = e3.status.ONLINE

        contact = self.session.contacts.contacts.get(account, None)

        if not contact:
            contact = e3.Contact(account)
            self.session.contacts.contacts[account] = contact

        old_message = contact.message
        old_status = contact.status
        contact.message = message
        contact.status = stat

        log_account =  e3.Logger.Account(contact.attrs.get('CID', None), None,
            contact.account, contact.status, contact.nick, contact.message,
            contact.picture)

        if old_status != stat:
            change_type = 'status'

            if old_status == e3.status.OFFLINE:
                change_type = 'online'

            if stat == e3.status.OFFLINE:
                change_type = 'offline'

            do_notify = (self.start_time + Worker.NOTIFICATION_DELAY) < \
                    time.time()

            self.session.add_event(e3.Event.EVENT_CONTACT_ATTR_CHANGED, account,
                change_type, old_status, do_notify)
            self.session.logger.log('status change', stat, str(stat),
                log_account)

        if old_message != contact.message:
            self.session.add_event(e3.Event.EVENT_CONTACT_ATTR_CHANGED, account,
                'message', old_message)
            self.session.logger.log('message change', contact.status,
                contact.message, log_account)

    def _on_message(self, client, message):
        '''handle the reception of a message'''
        body = message.getBody()
        account = message.getFrom().getStripped()

        if account in self.conversations:
            cid = self.conversations[account]
        else:
            cid = time.time()
            self.conversations[account] = cid
            self.rconversations[cid] = [account]
            self.session.add_event(e3.Event.EVENT_CONV_FIRST_ACTION, cid,
                [account])

        if body is None:
            type_ = e3.Message.TYPE_TYPING
        else:
            type_ = e3.Message.TYPE_MESSAGE

        msgobj = e3.Message(type_, body, account)
        self.session.add_event(e3.Event.EVENT_CONV_MESSAGE, cid, account, msgobj)

    # action handlers
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
        pass

    def _handle_action_login(self, account, password, status_, host, port):
        '''handle Action.ACTION_LOGIN
        '''
        if self.client.connect((host, port),
                proxy=self.proxy_data) == "":
            self.session.add_event(e3.Event.EVENT_LOGIN_FAILED,
                'Connection error')
            return

        if self.client.auth(self.jid.getNode(),
            self.session.account.password) == None:
            self.session.add_event(e3.Event.EVENT_LOGIN_FAILED,
                'Authentication error')
            return

        self.session.add_event(e3.Event.EVENT_LOGIN_SUCCEED)
        self.start_time = time.time()

        self.client.RegisterHandler('message', self._on_message)

        self.client.sendInitPresence()

        while self.client.Process(1) != '0':
            pass

        self.roster = self.client.getRoster()

        for account in self.roster.getItems():
            name = self.roster.getName(account)

            if account == self.session.account.account:
                if name is not None:
                    self.session.contacts.me.nick = name
                    self.session.add_event(e3.Event.EVENT_NICK_CHANGE_SUCCEED,
                        nick)

                continue

            if account in self.session.contacts.contacts:
                contact = self.session.contacts.contacts[account]
            else:
                contact = e3.Contact(account)
                self.session.contacts.contacts[account] = contact

            if name is not None:
                contact.nick = name

        self.session.add_event(e3.Event.EVENT_CONTACT_LIST_READY)
        self.client.RegisterHandler('presence', self._on_presence)

    def _handle_action_logout(self):
        '''handle Action.ACTION_LOGOUT
        '''
        self.client.disconnect()

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

    def _handle_action_set_nick(self, nick):
        '''handle Action.ACTION_SET_NICK
        '''
        pass

    def _handle_action_set_picture(self, picture_name):
        '''handle Action.ACTION_SET_PICTURE
        '''
        pass

    def _handle_action_set_preferences(self, preferences):
        '''handle Action.ACTION_SET_PREFERENCES
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
        pass

    def _handle_action_send_message(self, cid, message):
        '''handle Action.ACTION_SEND_MESSAGE
        cid is the conversation id, message is a Message object
        '''

        recipients = self.rconversations.get(cid, ())

        for recipient in recipients:
            self.client.send(xmpp.protocol.Message(recipient, message.body,
                'chat'))

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
