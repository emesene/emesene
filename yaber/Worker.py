import sys
import time
import xmpp
import Queue

import protocol.Worker
import protocol.Message
import protocol.Contact
from  protocol.Event import Event
from  protocol.Action import Action

import protocol.Logger as Logger

class Worker(protocol.Worker):
    '''wrapper of xmpppy to make it work like protocol.Worker'''

    def __init__(self, app_name, session):
        '''class constructor'''
        protocol.Worker.__init__(self, app_name, session)
        self.jid = xmpp.protocol.JID(session.account.account)
        self.client = xmpp.Client(self.jid.getDomain(), debug=[]) # 'always'])

        self.conversations = {}
        self.roster = None
    
    def run(self):
        '''main method, block waiting for data, process it, and send data back 
        '''
        data = None

        while True:
            if hasattr(self.client, 'Process'):
                self.client.Process(1)

            try:
                action = self.session.actions.get(True, 0.1)

                if action.id_ == Action.ACTION_QUIT:
                    print 'closing thread'
                    self.session.logger.quit()
                    break

                self._process_action(action)
            except Queue.Empty:
                time.sleep(0.1)

    def _on_presence(self, client, presence):
        '''handle the reception of a presence message'''
        message = presence.getStatus() or ''
        show = presence.getShow()
        type_ = presence.getType()
        account = presence.getFrom().getStripped()

        if type_ == 'unavailable':
            stat = protocol.status.OFFLINE
        elif show == 'away':
            stat = protocol.status.AWAY
        elif show == 'dnd':
            stat = protocol.status.BUSY
        else:
            stat = protocol.status.ONLINE

        contact = self.session.contacts.contacts.get(account, None)

        if not contact:
            contact = protocol.Contact(account)
            self.session.contacts.contacts[account] = contact

        old_message = contact.message
        old_status = contact.status
        contact.message = message
        contact.status = stat

        log_account =  Logger.Account(contact.attrs.get('CID', None), None, 
            contact.account, contact.status, contact.nick, contact.message, 
            contact.picture)

        changed = False

        if old_status != stat:
            changed = True
            self.session.logger.log('status change', stat, str(stat), 
                log_account)

        if old_message != contact.message:
            changed = True
            self.session.logger.log('message change', contact.status, 
                contact.message, log_account)

        if changed:
            self.session.add_event(Event.EVENT_CONTACT_ATTR_CHANGED, account)

    def _on_message(self, client, message):
        '''handle the reception of a message'''
        print 'on message', client, message
        body = message.getBody()
        account = message.getFrom()
        msgobj = protocol.Message(protocol.Message.TYPE_MESSAGE, body, account)
        self.session.add_event(Event.EVENT_CONV_MESSAGE, 
            self.cid, account, msgobj)

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

    def _handle_action_login(self, account, password, status_):
        '''handle Action.ACTION_LOGIN
        '''
        if self.client.connect(('talk.google.com', 5223)) == "":
            self.session.add_event(Event.EVENT_LOGIN_FAILED, 
                'Connection error')
            return

        if self.client.auth(self.jid.getNode(), 
            self.session.account.password) == None:
            self.session.add_event(Event.EVENT_LOGIN_FAILED, 
                'Authentication error')
            return

        self.client.sendInitPresence()

        self.session.add_event(Event.EVENT_LOGIN_SUCCEED)

        self.roster = self.client.getRoster()

        for account in self.roster.getItems():
            name = self.roster.getName(account)
            if account in self.session.contacts.contacts:
                contact = self.session.contacts.contacts[account]
            else:
                contact = protocol.Contact(account)
                self.session.contacts.contacts[account] = contact

            contact.nick = name | account

            #for group in self.roster.getGroups(account):
            #    print 'group', group, type(group)

        self.session.add_event(Event.EVENT_CONTACT_LIST_READY)
        self.client.RegisterHandler('message', self._on_message)
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
        pass

    def _handle_action_close_conversation(self, cid):
        '''handle Action.ACTION_CLOSE_CONVERSATION
        '''
        pass

    def _handle_action_send_message(self, cid, message):
        '''handle Action.ACTION_SEND_MESSAGE
        cid is the conversation id, message is a MsnMessage object
        '''

        recipients = self.conversations.get(cid, ())

        # TODO: see if this is correct on jabber
        for recipient in recipients:
            self.client.send(xmpp.protocol.Message(recipient, message, 'chat'))

    # p2p handlers

    def _handle_action_p2p_invite(self, cid, pid, dest, type_, identifier):
        '''handle Action.ACTION_P2P_INVITE,
         cid is the conversation id
         pid is the p2p session id, both are numbers that identify the 
            conversation and the session respectively, time.time() is 
            recommended to be used.
         dest is the destination account
         type_ is one of the protocol.Transfer.TYPE_* constants
         identifier is the data that is needed to be sent for the invitation
        '''
        pass

    def _handle_action_p2p_accept(self, pid):
        '''handle Action.ACTION_P2P_ACCEPT'''
        pass

    def _handle_action_p2p_cancel(self, pid):
        '''handle Action.ACTION_P2P_CANCEL'''
        pass
