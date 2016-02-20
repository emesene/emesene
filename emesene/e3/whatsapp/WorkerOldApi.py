# -*- coding: utf-8 -*-
import Queue
import random

import e3
import gobject
import time

import api
import hashlib

import logging
log = logging.getLogger('whatsapp.Worker')


class Worker(e3.Worker, api.WAClient):
    '''dummy Worker implementation to make it easy to test emesene'''

    def __init__(self, session, proxy, use_http=False, use_ipv6=False):
        '''class constructor'''
        e3.Worker.__init__(self, session)
        
        self.conversations = {}
        self.rconversations = {}
        

    def _add_pending_contacts(self):
        tmp_cont = e3.base.Contact("test1@test.com", 1,
            "test1", "test1nick",
            e3.status.BUSY, '',
            True)
        self.session.contacts.pending["test1@test.com"] = tmp_cont

        tmp_cont = e3.base.Contact("test2@test.com", 2,
            "test2", "test2nick",
            e3.status.ONLINE, '',
            True)
        self.session.contacts.pending["test2@test.com"] = tmp_cont

    def _late_contact_add(self):
        '''this simulates adding a contact after we show the contactlist'''
        tmp_cont = e3.base.Contact("testlate1@test.com", 1,
            "testlate1", "testlate1nick",
            e3.status.BUSY, '',
            True)
        self.session.contacts.pending["testlate1@test.com"] = tmp_cont
        self.session.contact_added_you()
        return False

    def _return_message(self, cid, account, message):
        ''' Method to return a message after some timeout '''
        self.session.conv_message(cid, account, message)
        message.account = account
        e3.Logger.log_message(self.session, None, message, False)
        return False

    def _add_contact(self, mail, nick, status_, alias, blocked, msg="..."):
        """
        method to add a contact to the contact list
        """
        self.session.contacts.contacts[mail] = e3.Contact(mail, mail,
            nick, msg, status_, alias, blocked)

    def _add_group(self, name):
        pass

    def _add_contact_to_group(self, account, group):
        pass

    # action handlers
    def _handle_action_add_contact(self, account):
        '''handle Action.ACTION_ADD_CONTACT
        '''
        self.session.contact_add_succeed(account)

    def _handle_action_add_group(self, name):
        pass

    def _handle_action_add_to_group(self, account, gid):
        pass

    def _handle_action_block_contact(self, account):
        '''handle Action.ACTION_BLOCK_CONTACT
        '''
        self.session.contact_block_succeed(account)

    def _handle_action_unblock_contact(self, account):
        '''handle Action.ACTION_UNBLOCK_CONTACT
        '''
        self.session.contact_unblock_succeed(account)

    def _handle_action_change_status(self, status_):
        '''handle Action.ACTION_CHANGE_STATUS'''
        self.session.account.status = status_
        self.session.contacts.me.status = status_
        self.session.status_change_succeed(status_)
        
        if status_ == 1:
            self.send_presence("invisible", account)
        else:
            self.send_presence("available", account)



    def _wa_login_succeeded(self, status, kind, creation, expiration):
        log.info("Login succeeded")
        
    def _wa_connected(self):
        log.info("Connected")
        
    def _wa_login_failed(self):
        log.info("Login failed")
        self.session.disconnected(_("Login failed"), False)
	
	
    def _wa_callback_command(self, uid, command, args):
        try:
            pass
        except Exception as e:
            self.chat_add_error(uid, str(e))
            
            
    def _wa_last_seen_received(self, sender, seconds):
        print "LAST SEEN RESPONSE:", sender, seconds
    
    def _wa_event_socket_recv(self, sock, condition):
        self.recv_and_handle()
        return True
        
    def _wa_message_received(self, message_id, sender, message, realname, offline_stamp):
        if offline_stamp is not None:
            offline_stamp = time.strftime("%Y-%m-%d %H:%M:%S", offline_stamp)
        print "%s (%s, %s): %s" % (realname, sender.split('@')[0],
                offline_stamp, message)
                
        self._on_message({'id':message_id, 'from':{'jid':sender, 'realname':realname}, 'type':'chat', 'body':message})
        
    
    def _on_message(self, message):
        '''handle the reception of a message'''
        if message['type'] not in ('chat'):
            log.error("Unhandled message: %s" % message)
            return

        body = message['body']
        account = message['from']['jid']
        realname = message['from']['realname']

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

        msgobj = e3.Message(type_, body, account, display_name=realname)
        # override font size!
        msgobj.style.size = self.session.config.i_font_size
        self.session.conv_message(cid, account, msgobj)
        # log message
        e3.Logger.log_message(self.session, None, msgobj, False)
        
        self.send_message_ack(account, message['id'])
        
                	
    def _handle_action_login(self, account, password, status_):
        '''handle Action.ACTION_LOGIN'''
                
        self.session.login_started()
        
		#TODO: replace status with the name
        #print account, hashlib.md5(password[::-1]).hexdigest()
        api.WAClient.__init__(self, account, hashlib.md5(password[::-1]).hexdigest(), account)
        
        
        self.callback_command = self._wa_callback_command
        
        
        self.set_event_handler('login_succeeded', self._wa_login_succeeded)
        self.set_event_handler('connected', self._wa_connected)
        self.set_event_handler('login_failed', self._wa_login_failed)
        self.set_event_handler('message_received', self._wa_message_received)
        self.set_event_handler('last_seen_received', self._wa_last_seen_received)
        
        
        """
        self.set_event_handler('last_seen_received', self.last_seen_received)
        self.set_event_handler('server_notice_received',
                self.server_notice_received)
        self.set_event_handler('message_received_at_server',
                self.message_received_at_server)
        self.set_event_handler('message_received_at_client',
                self.message_received_at_client)
        self.set_event_handler('chatstate_changed', self.chatstate_changed)
        """
        
        try:
            self.connect()
        except:
            self.session.disconnected(_("Network problem"), True)
            return
        
        gobject.io_add_watch(self.socket, gobject.IO_IN, self._wa_event_socket_recv)
        
             
        time.sleep(3)
        self.session.login_succeed()
        self.session.contact_list_ready()
        
        self._handle_action_set_nick(account)
        
        self.session.contacts.me.status = self.session.account.status
        self.send_presence("available", account)
        
        
        # Your account
        #tmp_cont = e3.base.Contact(account, 1, account, account, e3.status.BUSY, '', True)
        #self.session.contacts.contacts[account] = tmp_cont
        
                
		#TEST        
        self.send_message("393471217796", "test")
        
        
        

    def _handle_action_logout(self):
        '''handle Action.ACTION_LOGOUT'''
        self.disconnect()

    def _handle_action_move_to_group(self, account, src_gid, dest_gid):
        pass

    def _handle_action_remove_contact(self, account):
        '''handle Action.ACTION_REMOVE_CONTACT
        '''
        self.session.contact_remove_succeed(account)

    def _handle_action_reject_contact(self, account):
        pass

    def _handle_action_remove_from_group(self, account, gid):
        pass

    def _handle_action_remove_group(self, gid):
        pass

    def _handle_action_rename_group(self, gid, name):
        pass
       

    def _handle_action_set_contact_alias(self, account, alias):
        '''handle Action.ACTION_SET_CONTACT_ALIAS'''
        self.session.contact_alias_succeed(account)

    def _handle_action_set_message(self, message):
        '''handle Action.ACTION_SET_MESSAGE'''
        self.session.message_change_succeed(message)

    def _handle_action_set_nick(self, nick):
        '''handle Action.ACTION_SET_NICK'''
        self.set_name(nick)
        self.send_presence()
        self.session.contacts.me.nick = nick
        self.session.nick_change_succeed(nick)


    def _handle_action_set_picture(self, picture_name):
        '''handle Action.ACTION_SET_PICTURE
        '''
        self.session.contacts.me.picture = picture_name
        self.session.picture_change_succeed(self.session.account.account,
                picture_name)

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
        cid is the conversation id, message is a Message object
        '''
        if message.type not in (e3.Message.TYPE_MESSAGE, e3.Message.TYPE_TYPING,
           e3.Message.TYPE_NUDGE):
            return # Do NOT process other message types

        recipients = self.rconversations.get(cid, ())
        for recipient in recipients:
            self.send_message(recipient.split('@')[0], message.body)


        e3.Logger.log_message(self.session, recipients, message, True)
