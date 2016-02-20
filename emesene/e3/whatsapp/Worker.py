# -*- coding: utf-8 -*-
import Queue
import random

import e3
import gobject
import time
import os
import base64

import hashlib
from Yowsup.Common.utilities import Utilities
from Yowsup.Common.debugger import Debugger
from Yowsup.Common.constants import Constants
from Yowsup.ConnectionIO.protocoltreenode import ProtocolTreeNode
from Yowsup.connectionmanager import YowsupConnectionManager

import logging
log = logging.getLogger('whatsapp.Worker')
logging.basicConfig(filename='example.log', filemode='w', level=logging.DEBUG)


# Get credentials from file
def getCredentials(config):
    if os.path.isfile(config):
        f = open(config)
        
        phone = ""
        idx = ""
        pw = ""
        cc = ""
        
        try:
            for l in f:
                line = l.strip()
                if len(line) and line[0] not in ('#',';'):
                    
                    prep = line.split('#', 1)[0].split(';', 1)[0].split('=', 1)
                    
                    varname = prep[0].strip()
                    val = prep[1].strip()
                    
                    if varname == "phone":
                        phone = val
                    elif varname == "id":
                        idx = val
                    elif varname =="password":
                        pw =val
                    elif varname == "cc":
                        cc = val

            return [cc, phone, idx, pw]
        except:
            pass

    return 0
    

class Worker(e3.Worker): #, api.WAClient):
    '''Whatsapp worker'''

    def __init__(self, session, proxy, use_http=False, use_ipv6=False):
        '''class constructor'''
        e3.Worker.__init__(self, session)
        
        self.conversations = {}
        self.rconversations = {}
        self.credentials = None
        self.state = False
        
        self.connectionManager = YowsupConnectionManager()
        self.connectionManager.setAutoPong(False)
        self.signalsInterface = self.connectionManager.getSignalsInterface()
        self.methodsInterface = self.connectionManager.getMethodsInterface()
        
        
        self.signalsInterface.registerListener("auth_success", self.onAuthSuccess)
        self.signalsInterface.registerListener("auth_fail", self.onAuthFailed)
        self.signalsInterface.registerListener("message_received", self.onMessageReceived)
        
        self.signalsInterface.registerListener("group_messageReceived", self.onGroupMessageReceived)
        self.signalsInterface.registerListener("group_gotParticipants", self.onGroupGotPartecipants)
		#self.signalsInterface.registerListener("receipt_messageSent", self.onMessageSent)
        self.signalsInterface.registerListener("presence_updated", self.onPresenceUpdated)
        self.signalsInterface.registerListener("group_gotInfo", self.onGroupGotInfo)
		#self.signalsInterface.registerListener("disconnected", self.onDisconnected)
        

    """
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
    """
    
    def _check_if_contact_exist(self, mail):
        mail in self.session.contacts.contacts
        
    def _add_contact(self, mail, nick, status_, alias, blocked, msg="..."):
        self.session.contacts.contacts[mail] = e3.Contact(mail, mail, nick, msg, status_, alias, blocked)
        
        #self.methodsInterface.call("picture_get", (mail))
        #self.connectionManager.sendGetPicture (mail.encode('utf-8'))
        
    """
    def _add_group(self, name):
        pass

    def _add_contact_to_group(self, account, group):
        pass
    """
    
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

    # Whatsapp signals	
    def onPresenceUpdated(self, jid, lastSeen):
        formattedDate = datetime.datetime.fromtimestamp(long(time.time()) - lastSeen).strftime('%d-%m-%Y %H:%M')
        #self.onMessageReceived(0, jid, "LAST SEEN RESULT: %s"%formattedDate, long(time.time()), False)
        print "last seen " + jid + " " + str(formattedDate)
        self._add_contact(jid, jid, e3.status.ONLINE, jid, False, "last seen at " + str(formattedDate))
        
		
    def onAuthFailed(self, username, err):
        log.info("Login failed for "+username)
        print "Login failed for "+username
        self.state = False
        self.session.disconnected(_("Login failed"), False)
        
		
    def onAuthSuccess(self, username):
        log.info("Login succeeded for "+username)
        print "Login succeeded for "+username
        self.state = True
        
        self._handle_action_set_nick(username)
        self.methodsInterface.call("ready")
        self._add_contact("393471217796@s.whatsapp.net", "Davide Gessa", e3.status.ONLINE, "Davide Gessa", False, "uaz!")

            
        #time.sleep(1)
        self.session.login_succeed()
        self.session.contact_list_ready()
        
        #self._handle_action_set_nick(account)
        
        self.session.contacts.me.status = self.session.account.status
        #self.send_presence("available", account)
        
        
        # Your account
        #tmp_cont = e3.base.Contact(account, 1, account, account, e3.status.BUSY, '', True)
        #self.session.contacts.contacts[account] = tmp_cont		
        
            
    def onGroupGotPartecipants(self, group, parts):
        g = ""
        for part in parts:
            if not self._check_if_contact_exist (part):
                self._add_contact(part, part, e3.status.ONLINE, part, False, "")
            
        
    def onGroupGotInfo(self, info):
        print "infoooooooooooooooooooooooooooooooo"
        print info
        print "infoooooooooooooooooooooooooooooooo"
    
        
    def onGroupMessageReceived(self, msgId, fromAttribute, author, msgData, timestamp, wantsReceipt, pushName):
        print "You got a group message!"
        print "%s (%s, %s): %s" % (pushName, author, timestamp, msgData)
        print fromAttribute
        
        # Add the group
        if not self._check_if_contact_exist (fromAttribute):
            #print fromAttribute
            #self.methodsInterface.call ("group_getInfo", (fromAttribute))
            #self.methodsInterface.call ("group_getParticipants", (fromAttribute))
            self.connectionManager.sendGetParticipants (fromAttribute)
            #self.connectionManager.sendGetGroupInfo (fromAttribute)
            self._add_contact(fromAttribute, "Group chat", e3.status.ONLINE, "Group chat", False, "")
            
        # Add the single contact
        if not self._check_if_contact_exist (author):
            self._add_contact(author, pushName, e3.status.ONLINE, pushName, False, "")
            
            
        self._on_group_message({'id':msgId, 'from':{'jid':author, 'realname':pushName}, 'type':'chat', 'body':msgData}, fromAttribute)
        #TODO enable ack
        if wantsReceipt:
            self.methodsInterface.call("message_ack", (fromAttribute, msgId))
    
    
    def onMessageReceived(self, messageId, jid, messageContent, timestamp, wantsReceipt, pushName, isBroadcast):
        print "You got a message!"
        print "%s (%s, %s): %s" % (pushName, jid, timestamp, messageContent)
        
        if not self._check_if_contact_exist (jid):
            self._add_contact(jid, pushName, e3.status.ONLINE, pushName, False, "")
                
        self._on_message({'id':messageId, 'from':{'jid':jid, 'realname':pushName}, 'type':'chat', 'body':messageContent})
        #TODO enable ack
        if wantsReceipt:
            self.methodsInterface.call("message_ack", (jid, messageId))
			



    # Emesene events handler    
    #def _on_conversation_message_received(self, message):
    #    e3.Logger.log_message(self.session, participants, msgobj, sent, cid = cid)
        
    def _on_group_message(self, message, group):
        '''handle the reception of a group message'''
        if message['type'] not in ('chat'):
            log.error("Unhandled message: %s" % message)
            return
        if group in self.conversations:
            cid = self.conversations[group]
        else:   
            cid = time.time()
            self.conversations[group] = cid
            self.rconversations[cid] = [group]
            self.session.conv_first_action(cid, [group]) 
            
 
        body = message['body']
        account = message['from']['jid']
        realname = message['from']['realname']
                   
        if body is None:
            type_ = e3.Message.TYPE_TYPING
        else:
            type_ = e3.Message.TYPE_MESSAGE

        msgobj = e3.Message(type_, body, account, display_name=realname)
        # override font size!
        msgobj.style.size = self.session.config.i_font_size
        self.session.conv_message(cid, group, msgobj)
        # log message
        e3.Logger.log_message(self.session, None, msgobj, False)     
        
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
        
                    
    def _handle_action_login(self, account, password, status_):
        '''handle Action.ACTION_LOGIN'''
                
        self.session.login_started()
        
        self.credentials = getCredentials ("/home/dak/config.example")
        print self.credentials
        
        self.methodsInterface.call ("auth_login", (self.credentials[1], base64.b64decode(bytes(self.credentials[3].encode('utf-8'))))) #self.credentials[3]))

        while not self.state:
            time.sleep(0.5)        
        

    def _handle_action_logout(self):
        '''handle Action.ACTION_LOGOUT'''
        self.methodsInterface.call("disconnect")
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
        #self.set_name(nick)
        #self.send_presence()
        self.session.contacts.me.nick = nick
        self.session.nick_change_succeed(nick)
        
        #TODO handle whatsapp


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
        print "action_send_message "+str(message.type)+str(e3.Message.TYPE_MESSAGE)
        if message.type not in (e3.Message.TYPE_MESSAGE, e3.Message.TYPE_TYPING, e3.Message.TYPE_NUDGE):
            return

        print "send to " + str(cid) + str(self.rconversations)
        recipients = self.rconversations.get(cid, ())
        print recipients, self.rconversations, message.account
        for recipient in recipients:
            print "_handle_action_send_message " + recipient
            #print recipient.split('@')[0]
            #print message.body
            msgId = self.methodsInterface.call("message_send", (recipient, message.body.encode('utf-8'))) #recipient, message.body))
		    #self.sentCache[msgId] = [int(time.time()), message]


        e3.Logger.log_message(self.session, recipients, message, True)
