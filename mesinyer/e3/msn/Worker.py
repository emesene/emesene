'''a thread that handles the connection with the main server'''

import os
import time
import Queue
import urllib
import httplib
import urlparse
import threading

import e3
import mbi
import p2p
import msgs
import common
import challenge
import Requester
import XmlManager
import Conversation
from MsnSocket import MsnSocket
from MsnHttpSocket import MsnHttpSocket

from XmlParser import SSoParser
from UbxParser import UbxParser

import logging
log = logging.getLogger('msn.Worker')

STATUS_MAP = {}
STATUS_MAP[e3.status.BUSY] = 'BSY'
STATUS_MAP[e3.status.AWAY] = 'AWY'
STATUS_MAP[e3.status.IDLE] = 'IDL'
STATUS_MAP[e3.status.ONLINE] = 'NLN'
STATUS_MAP[e3.status.OFFLINE] = 'HDN'

STATUS_MAP_REVERSE = {}
STATUS_MAP_REVERSE['BSY'] = e3.status.BUSY
STATUS_MAP_REVERSE['AWY'] = e3.status.AWAY
STATUS_MAP_REVERSE['BRB'] = e3.status.AWAY
STATUS_MAP_REVERSE['PHN'] = e3.status.AWAY
STATUS_MAP_REVERSE['LUN'] = e3.status.AWAY
STATUS_MAP_REVERSE['IDL'] = e3.status.IDLE
STATUS_MAP_REVERSE['NLN'] = e3.status.ONLINE
STATUS_MAP_REVERSE['HDN'] = e3.status.OFFLINE

CLIENT_ID = 0x4     # ink
CLIENT_ID |= 0x20    # multi-packet MIME messages
CLIENT_ID |= 0x8000  # winks
CLIENT_ID |= 0x40000 # voice clips
CLIENT_ID |= 0x50000000 | 0x2  # msnc5 + reset capabilities

KNOWN_UNHANDLED_RESPONSES = ['PRP', 'BLP', 'CHG', 'QRY', 'GCF', 'UUX']

class Worker(e3.Worker):
    '''this class represent an object that waits for commands from the queue
    of a socket, process them and add it as events to its own queue'''

    NOTIFICATION_DELAY = 60

    def __init__(self, app_name, session, proxy=None, use_http=False):
        '''class constructor'''
        e3.Worker.__init__(self, app_name, session)

        self.host = None
        self.port = None

        if proxy is None:
            self.proxy = e3.Proxy()
        else:
            self.proxy = proxy
        self.use_http = use_http

        self.socket = self._get_socket()
        self.socket.start()

        self.in_login = False
        # the class used to create the conversation sockets, since sockets
        # or http method can be used

        self.last_ping_response = 0.0

        self._login_handlers = None
        self._common_handlers = None
        self.start_time = None
        self._set_handlers()

        self.conversations = {}
        self.transfers = {}
        # contains the tid when the switchboard was requested as key and the
        # account that should be invited when we get the switchboard as value
        self.pending_conversations = {}
        # this list contains all the conversation ids that are not still
        # opened, it is used to store pending messages to be sent when
        # the conversation is ready to send messages
        self.pending_cids = []
        # contains a pending cid as key and a list of messages as value
        self.pending_messages = {}

        self.p2p = Queue.Queue() # p2p manager input queue

        self.msg_manager = msgs.Manager(session) # msg manager
        self.msg_manager.start()

    def _get_socket(self, host=None, port=None):
        '''return a socket according to the proxy settings'''
        if host is None:
            host = self.host

        if port is None:
            port = self.port

        if self.proxy.use_proxy or self.use_http:
            socket = MsnHttpSocket(host, port, dest_type='NS', proxy=self.proxy)
        else:
            socket = MsnSocket(host, port)
        return socket

    def _set_handlers(self):
        '''set a dict with the action id as key and the handler as value'''
        # login message handlers

        login_handlers = {}

        login_handlers['VER'] = self._on_version
        login_handlers['CVR'] = self._on_client_version
        login_handlers['XFR'] = self._on_transfer
        login_handlers['USR'] = self._on_user
        login_handlers['SBS'] = self._on_sbs
        login_handlers['MSG'] = self._on_login_message

        self._login_handlers = login_handlers

        # common message handlers

        common_handlers = {}

        common_handlers['ILN'] = self._on_initial_status_change
        common_handlers['UBX'] = self._on_information_change
        common_handlers['CHL'] = self._on_challenge
        common_handlers['NLN'] = self._on_online_change
        common_handlers['FLN'] = self._on_offline_change
        common_handlers['RNG'] = self._on_conversation_invitation
        common_handlers['ADL'] = self._on_add
        common_handlers['RML'] = self._on_remove
        common_handlers['XFR'] = self._on_conversation_transfer
        common_handlers['MSG'] = self._on_server_message
        common_handlers['NOT'] = self._on_notification
        common_handlers['OUT'] = self._on_server_disconnection
        common_handlers['QNG'] = self._on_ping_response
        common_handlers['RNG'] = self._on_conversation_request

        self._common_handlers = common_handlers


    def run(self):
        '''main method, block waiting for data, process it, and send data back
        to the socket or add a new event to the socket depending on the data'''
        data = None

        while True:
            try:
                data = self.socket.output.get(True, 0.1)

                if type(data) == int and data == 0:
                    self.session.add_event(e3.Event.EVENT_ERROR,
                        'Connection closed')
                    log.debug('Worker connection closed')
                    break

                self._process(data)
                continue
            except Queue.Empty:
                pass

            try:
                cmd = self.command_queue.get(True, 0.1)
                self.socket.send_command(cmd.command, cmd.params, cmd.payload)
            except Queue.Empty:
                pass

            if self.in_login:
                continue

            try:
                action = self.session.actions.get(True, 0.1)

                if action.id_ == e3.Action.ACTION_QUIT:
                    log.debug('closing thread')
                    self.socket.input.put('quit')
                    self.session.logger.quit()
                    self.msg_manager.quit()

                    for (cid, conversation) in self.conversations.iteritems():
                        conversation.command_queue.put('quit')

                    for (pid, transfer) in self.transfers.iteritems():
                        transfer.add_action(e3.Action.ACTION_QUIT)

                    break

                self._process_action(action)
            except Queue.Empty:
                pass

    def _process(self, message):
        '''process the data'''
        log.debug('<<< ' + str(message))

        if self.in_login:
            self._process_login(message)
        else:
            self._process_normal(message)

    def _process_login(self, message):
        '''handle the messages on the login stage'''
        handler = self._login_handlers.get(message.command, None)

        if handler:
            handler(message)
        else:
            self._on_unknown_command(message)

    def _process_normal(self, message):
        '''handle the messages on normal connection'''
        handler = self._common_handlers.get(message.command, None)

        if handler:
            handler(message)
        else:
            self._on_unknown_command(message)

    def do_passport_identification(self):
        '''do the passport identification and get our passport id'''
        hash_ = self.session.extras['hash'].split()[-1]
        template = XmlManager.get('passport',
            self.session.account.account, self.session.account.password)

        if '@msn.com' not in self.session.account.account:
            server = "login.live.com"
            url = "/RST.srf"
        else:
            server = "msnia.login.live.com"
            url = "/pp550/RST.srf"

        #create the headers
        headers = { \
          'Accept' :  'text/*',
          'User-Agent' : 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)',
          'Host' : server,
          'Content-Length' : str(len(template)),
          'Connection' : 'Keep-Alive',
          'Cache-Control' : 'no-cache'
        }

        succeeded = False

        for i in range(5):
            response = None

            # send the SOAP request
            for i in range(3):
                try:

                    conn = httplib.HTTPSConnection(server, 443)
                    conn.request('POST', url, template, headers)
                    response = conn.getresponse()
                    break
                except Exception, exception:
                    pass

            if response:
                data = response.read()
                log.debug(data)
            else:
                self.session.add_event(e3.Event.EVENT_LOGIN_FAILED,
                 'Can\'t connect to HTTPS server: ' + str(exception))
                self._on_login_failed()

            if data.find('<faultcode>psf:Redirect</faultcode>') > 0:
                url = urlparse.urlparse(data.split('<psf:redirectUrl>')\
                    [1].split('</psf:redirectUrl>')[0])

                server = url[1]
                url = url[2]
            else:
                succeeded = True
                break

        if not succeeded:
            self.session.add_event(e3.Event.EVENT_LOGIN_FAILED,
                'Too many redirections')
            self._on_login_failed()

        # try to get the ticket from the received data
        self.session.extras.update(SSoParser(data).tokens)
        if 'messengerclear.live.com' not in self.session.extras:
            # try to get the faultstring
            try:
                faultstring = data.split('<faultstring>')\
                    [1].split('</faultstring>')[0]
            except IndexError, exception:
                faultstring = str(exception)

            self.session.add_event(e3.Event.EVENT_LOGIN_FAILED, faultstring)
            self._on_login_failed()
            return False

        self.session.extras['mbiblob'] = mbi.encrypt(
               self.session.extras['messengerclear.live.com']['secret'], hash_)

        return True

    def _set_status(self, stat):
        '''set our status'''
        if stat not in STATUS_MAP:
            return

        self.session.account.status = stat
        self.session.contacts.me.status = stat
        self.socket.send_command('CHG', (STATUS_MAP[stat], str(CLIENT_ID), '0'))
        self.session.add_event(e3.Event.EVENT_STATUS_CHANGE_SUCCEED, stat)

        # log the status
        contact = self.session.contacts.me
        account = e3.Logger.Account.from_contact(contact)
        account.status = stat

        self.session.logger.log('status change', stat, str(stat), account)

    def _start_from_cache(self):
        '''try to send the adl with the data from cache'''
        logger = self.session.logger.logger

        if len(logger.accounts) < 2:
            return False

        # thread madness I should be careful to not modify accounts while
        # iterating
        for (account, contact) in logger.accounts.items():
            new_contact = e3.Contact(account, contact.cid,
                contact.nick, contact.message)
            new_contact.groups = contact.groups[:]
            self.session.contacts.contacts[account] = new_contact

        for (gid, group) in logger.groups.iteritems():
            new_group = e3.Group(group.name, gid)
            new_group.contacts = group.accounts[:]
            self.session.groups[gid] = new_group

        nick = my_account = self.session.account.account
        account_info = logger.accounts.get(my_account, None)

        if account_info:
            if account_info.nick:
                nick = account_info.nick
            else:
                nick = my_account

        nick = nick.decode('utf-8', 'replace').encode('utf-8')
        self.socket.send_command('PRP', ('MFN', urllib.quote(nick)))
        self.session.add_event(e3.Event.EVENT_NICK_CHANGE_SUCCEED, nick)
        self.socket.send_command('BLP', ('BL',))

        for adl in self.session.contacts.get_adls():
            self.socket.send_command('ADL', payload=adl)

        self.session.add_event(e3.Event.EVENT_CONTACT_LIST_READY)

        return True

    def _on_version(self, message):
        '''handle version'''
        self.socket.send_command('CVR',
            ('0x0c0a', 'winnt', '5.1', 'i386', 'MSNMSGR', '8.1.0178',
            'msmsgs', self.session.account.account))

    def _on_client_version(self, message):
        '''handle client version'''
        self.socket.send_command('USR', ('SSO', 'I',
            self.session.account.account))

    def _on_transfer(self, message):
        '''handle server transfer'''
        if message.param_num_is(0, 'NS') and \
            message.param_num_exists(1):

            try:
                (host, port) = message.params[1].split(':')
            except ValueError:
                self.session.add_event(e3.Event.EVENT_LOGIN_FAILED,
                    'invalid XFR command')
                self._on_login_failed()

            self.socket = self._get_socket(host, int(port))
            self.socket.start()
            self.socket.send_command('VER', ('MSNP15', 'CVR0'))
        else:
            self.session.add_event(e3.Event.EVENT_LOGIN_FAILED,
                'invalid XFR command')
            self._on_login_failed()

    def _on_user(self, message):
        '''handle user response'''
        if message.param_num_is(0, 'SSO'):
            hash_ = ' '.join(message.params[2:])
            self.session.extras['hash'] = urllib.unquote(hash_)
            succeed = self.do_passport_identification()

            # if returned a tuple with a signal, we return it
            if not succeed:
                return

            passport_id = self.session.extras['messengerclear.live.com']\
                                          ['security'].replace("&amp;" , "&")
            self.session.extras['passport id'] = passport_id

            try:
                self.session.extras['MSPProf'] = passport_id.split('&p=')[1]
                ticket = passport_id.split('&p=')[0][2:]
                param = passport_id.split('&p=')[1]
                self.session.extras['t'] = ticket
                self.session.extras['p'] = param
            except IndexError:
                self.session.add_event(e3.Event.EVENT_LOGIN_FAILED,
                    'Incorrect passport id')
                self._on_login_failed()

            # we introduce ourselves again
            self.socket.send_command('USR', ('SSO', 'S', \
                passport_id, self.session.extras['mbiblob']))
        elif message.param_num_is(0, 'OK'):
            pass

    def _on_sbs(self, message):
        '''handle (or dont) the sbs message'''
        pass

    def _on_login_failed(self):
        '''called when the login process fails, do cleanup here'''
        self.session.logger.quit()

    def _on_login_message(self, message):
        '''handle server message on login'''
        for line in message.payload.split('\r\n'):
            if line:
                (key, value) = line.split(': ')
                self.session.extras[key] = value

        self.session.load_config()
        self.session.create_config()

        self.session.add_event(e3.Event.EVENT_LOGIN_SUCCEED)
        self.in_login = False
        self._set_status(self.session.account.status)
        started_from_cache = self._start_from_cache()
        Requester.Membership(self.session, self.command_queue,
            True, started_from_cache).start()

    def _on_initial_status_change(self, message):
        '''handle the first status change of the contacts, that means
        the status of the contacts that were connected before our connection'''

        param_length = len(message.params)
        (status_, email, one, nick) = message.params[:4]
        msnobj = None

        if param_length == 5:
            msnobj = urllib.unquote(message.params[4])

        email.lower()
        status_ = STATUS_MAP_REVERSE[status_]
        nick = urllib.unquote(nick)
        nick = nick.decode('utf-8', 'replace').encode('utf-8')

        contact = self.session.contacts.contacts.get(email, None)

        if not contact:
            return

        account = contact.account
        old_status = contact.status
        old_nick = contact.nick
        contact.status = status_
        contact.nick = nick
        contact.attrs['msnobj'] = msnobj
        contact.attrs['CID'] = cid

        log_account = e3.Logger.Account.from_contact(contact)

        if old_status != status_:
            self.session.add_event(e3.Event.EVENT_CONTACT_ATTR_CHANGED, account,
                'status', old_status)
            self.session.logger.log('status change', status_, str(status_),
                log_account)

        if old_nick != nick:
            self.session.add_event(e3.Event.EVENT_CONTACT_ATTR_CHANGED, account,
                'nick', old_nick)
            self.session.logger.log('nick change', status_, nick,
                log_account)

    def _on_information_change(self, message):
        '''handle the change of the information of a contact (personal
        message)'''
        if int(message.params[0]) == 0:
            return

        account = message.tid
        contact = self.session.contacts.contacts.get(account, None)

        if not contact:
            return

        parsed = UbxParser(message.payload)
        old_message = contact.message
        old_media = contact.media
        contact.message = parsed.psm
        contact.media = parsed.current_media

        if old_message == contact.message and \
            old_media == contact.media:
            return

        if old_message != contact.message:
            self.session.add_event(e3.Event.EVENT_CONTACT_ATTR_CHANGED, account,
                'message', old_message)
            self.session.logger.log('message change', contact.status,
                contact.message, e3.Logger.Account.from_contact(contact))

        if old_media == contact.media:
            self.session.add_event(e3.Event.EVENT_CONTACT_ATTR_CHANGED, account,
                'media', old_media)
            # TODO: log the media change

    def _on_challenge(self, message):
        '''handle the challenge sent by the server'''
        out = challenge.do_challenge(message.params[0][:-2])
        self.socket.send_command('QRY', (challenge._PRODUCT_ID,) , out)

    def _on_online_change(self, message):
        '''handle the status change of a contact that comes from offline'''
        status_ = STATUS_MAP_REVERSE[message.tid]
        account = message.params[0].lower()
        nick = message.params[2]
        params_length = len(message.params)

        nick = urllib.unquote(nick)
        nick = nick.decode('utf-8', 'replace').encode('utf-8')

        contact = self.session.contacts.contacts.get(account, None)

        if not contact:
            return

        old_status = contact.status
        contact.status = status_
        old_nick = contact.nick
        contact.nick = nick

        if params_length == 4:
            msnobj = urllib.unquote(message.params[3])
            contact.attrs['CID'] = int(message.params[2])

        log_account = e3.Logger.Account.from_contact(contact)

        if old_status != status_:
            change_type = 'status'

            if old_status == e3.status.OFFLINE:
                change_type = 'online'

            do_notify = (self.start_time + Worker.NOTIFICATION_DELAY) < \
                    time.time()

            self.session.add_event(e3.Event.EVENT_CONTACT_ATTR_CHANGED, account,
                change_type, old_status, do_notify)
            self.session.logger.log('status change', status_, str(status_),
                log_account)

        if old_nick != nick:
            self.session.add_event(e3.Event.EVENT_CONTACT_ATTR_CHANGED, account,
                'nick', old_nick)
            self.session.logger.log('nick change', status_, nick,
                log_account)

        # TODO: here we should check the old and the new msnobj and request the
        # new image if needed

    def _on_offline_change(self, message):
        '''handle the disconnection of a contact'''
        account = message.tid
        contact = self.session.contacts.contacts.get(account, None)

        if not contact:
            log.warning('account: %s not found on contact list' % account)
            return

        old_status = contact.status
        contact.status = e3.status.OFFLINE

        if old_status != contact.status:
            self.session.add_event(e3.Event.EVENT_CONTACT_ATTR_CHANGED, account,
                'offline', old_status)
            self.session.logger.log('status change', e3.status.OFFLINE,
                str(e3.status.OFFLINE),
                e3.Logger.Account.from_contact(contact))

    def _on_conversation_invitation(self, message):
        '''handle the invitation to start a conversation'''
        pass

    def _on_add(self, message):
        '''handle a message that informs us about someone that added us'''
        pass

    def _on_remove(self, message):
        '''handle a message that informs us about someone that removed us'''
        pass

    def _on_conversation_transfer(self, message):
        '''handle a message that inform us that we must start a new switchboard
        with a server'''
        # XFR 10
        # SB 207.46.27.178:1863 CKI 212949295.5321588.019445 U
        # messenger.msn.com 1

        if len(message.params) == 6:
            (sb_, chost, cki, session_id, unk, server) = message.params
        else:
            (sb_, chost, cki, session_id, unk, server, one) = message.params

        (host, port) = chost.split(':')
        account, cid = self.pending_conversations[int(message.tid)]
        messages = self.pending_messages[cid]

        del self.pending_conversations[int(message.tid)]
        del self.pending_messages[cid]

        if cid in self.pending_cids:
            self.pending_cids.remove(cid)

        if cid not in self.conversations:
            con = Conversation.Conversation(self.session, cid,
                host, int(port), account, session_id, self.p2p, self.proxy)
            self.conversations[cid] = con
            con.send_presentation()
            con.invite(account)
            con.start()
        else:
            con = self.conversations[cid]
            con.reconnect(host, int(port), session_id)

        # send all the pending messages
        for message in messages:
            con.send_message(message)

    def _on_server_message(self, message):
        '''handle a server message when we are not on the login stage'''
        self.msg_manager.put(msgs.Manager.ACTION_MSG_RECEIVED, message)

    def _on_notification(self, message):
        '''handle a notification message'''
        log.debug('server notification: ' + message.payload)

    def _on_server_disconnection(self, message):
        '''handle the message that inform us that we were disconnected from
        the server'''
        # TODO: translate the reasons to meaninful messages
        self.session.add_event(e3.Event.EVENT_DISCONNECTED, message.tid)

    def _on_ping_response(self, message):
        '''handle the response from the PNG command'''
        self.last_ping_response = time.time()

    def _on_conversation_request(self, message):
        '''handle a conversation request, example
        RNG 1581441881 64.4.37.33:1863 CKI 252199185.167235214
        eltuza@gmail.com tuza U messenger.msn.com'''
        session_id = message.tid
        (chost, auth_type, auth_id, user, username, unk, server, unk2) = \
        message.params

        (host, port) = chost.split(':')

        cid = time.time()
        con = Conversation.Conversation(self.session, cid,
            host, int(port), user, session_id, self.p2p, auth_id)
        self.conversations[cid] = con
        con.answer()
        con.start()

    def _on_unknown_command(self, message):
        '''handle the unknown commands'''
        if message.command not in KNOWN_UNHANDLED_RESPONSES:
            log.warning('unknown command: ' + str(message))

    # action handlers
    def _handle_action_add_contact(self, account):
        '''handle e3.Action.ACTION_ADD_CONTACT
        '''
        Requester.AddContact(self.session, account, self.command_queue).start()

    def _handle_action_add_group(self, name):
        '''handle e3.Action.ACTION_ADD_GROUP
        '''
        Requester.AddGroup(self.session, name, self.command_queue).start()

    def _handle_action_add_to_group(self, account, gid):
        '''handle e3.Action.ACTION_ADD_TO_GROUP
        '''
        contact = self.session.contacts.get(account)

        if contact is None:
            return

        Requester.AddToGroup(self.session, contact.identifier, contact.account,
            gid, self.command_queue).start()

    def _handle_action_block_contact(self, account):
        '''handle e3.Action.ACTION_BLOCK_CONTACT
        '''
        Requester.BlockContact(self.session, account, self.command_queue)\
            .start()

    def _handle_action_unblock_contact(self, account):
        '''handle e3.Action.ACTION_UNBLOCK_CONTACT
        '''
        Requester.UnblockContact(self.session, account, self.command_queue)\
            .start()

    def _handle_action_change_status(self, status_):
        '''handle e3.Action.ACTION_CHANGE_STATUS
        '''
        self._set_status(status_)

    def _handle_action_login(self, account, password, status_, host, port):
        '''handle e3.Action.ACTION_LOGIN
        '''
        self.session.account.account = account
        self.session.account.password = password
        self.session.account.status = status_

        self.host = host
        self.port = port

        self.socket.send_command('VER', ('MSNP15', 'CVR0'))
        self.session.add_event(e3.Event.EVENT_LOGIN_STARTED)
        self.in_login = True
        self.start_time = time.time()

    def _handle_action_logout(self):
        '''handle e3.Action.ACTION_LOGOUT
        '''
        pass

    def _handle_action_move_to_group(self, account, src_gid, dest_gid):
        '''handle e3.Action.ACTION_MOVE_TO_GROUP
        '''
        contact = self.session.contacts.get(account)

        if contact is None:
            return

        Requester.MoveContact(self.session, contact.identifier, contact.account,
            src_gid, dest_gid, self.command_queue).start()

    def _handle_action_remove_contact(self, account):
        '''handle e3.Action.ACTION_REMOVE_CONTACT
        '''
        contact = self.session.contacts.get(account)

        if contact is None:
            return

        Requester.RemoveContact(self.session, contact.identifier, account, \
            self.command_queue).start()

    def _handle_action_reject_contact(self, account):
        '''handle e3.Action.ACTION_REJECT_CONTACT
        '''
        Requester.RemovePendingContact(self.session, account).start()

    def _handle_action_remove_from_group(self, account, gid):
        '''handle e3.Action.ACTION_REMOVE_FROM_GROUP
        '''
        contact = self.session.contacts.get(account)

        if contact is None:
            return

        Requester.RemoveFromGroup(self.session, contact.identifier,
            contact.account, gid, self.command_queue).start()

    def _handle_action_remove_group(self, gid):
        '''handle e3.Action.ACTION_REMOVE_GROUP
        '''
        Requester.RemoveGroup(self.session, gid, self.command_queue).start()

    def _handle_action_rename_group(self, gid, name):
        '''handle e3.Action.ACTION_RENAME_GROUP
        '''
        Requester.RenameGroup(self.session, gid, name,
            self.command_queue).start()

    def _handle_action_set_contact_alias(self, account, alias):
        '''handle e3.Action.ACTION_SET_CONTACT_ALIAS
        '''
        contact = self.session.contacts.get(account)

        if contact is None:
            return

        Requester.ChangeAlias(self.session, contact.identifier, account, \
            alias, self.command_queue).start()

    def _handle_action_set_message(self, message):
        '''handle e3.Action.ACTION_SET_MESSAGE
        '''
        self.socket.send_command('UUX', payload='<Data><PSM>' + \
            common.escape(message) + '</PSM><CurrentMedia></CurrentMedia>' + \
            '<MachineGuid></MachineGuid></Data>')
        self.session.add_event(e3.Event.EVENT_MESSAGE_CHANGE_SUCCEED, message)
        self.session.contacts.me.message = message

        # log the change
        contact = self.session.contacts.me
        account = e3.Logger.Account.from_contact(contact)

        self.session.logger.log('message change', contact.status, message,
            account)
        Requester.SetProfile(self.session, contact.nick, message).start()

    def _handle_action_set_nick(self, nick):
        '''handle e3.Action.ACTION_SET_NICK
        '''
        contact = self.session.contacts.me
        message = contact.message
        account = e3.Logger.Account.from_contact(contact)
        account.nick = nick

        Requester.ChangeNick(self.session, nick, account,
            self.command_queue).start()
        Requester.SetProfile(self.session, nick, message).start()

    def _handle_action_set_picture(self, picture_name):
        '''handle e3.Action.ACTION_SET_PICTURE
        '''
        print 'TODO: implement set picture: ', picture_name
        self.session.contacts.me.picture = picture_name
        self.session.add_event(e3.Event.EVENT_PICTURE_CHANGE_SUCCEED,
                self.session.account.account, picture_name)

    def _handle_action_set_preferences(self, preferences):
        '''handle e3.Action.ACTION_SET_PREFERENCES
        '''
        pass

    def _handle_action_new_conversation(self, account, cid):
        '''handle e3.Action.ACTION_NEW_CONVERSATION
        '''
        self.pending_conversations[self.socket.tid] = (account, cid)
        self.pending_cids.append(cid)
        self.pending_messages[cid] = []
        self.socket.send_command('XFR', ('SB',))

    def _handle_action_close_conversation(self, cid):
        '''handle e3.Action.ACTION_CLOSE_CONVERSATION
        '''
        if cid in self.conversations:
            self.conversations[cid].command_queue.put('quit')
            del self.conversations[cid]
        else:
            log.warning('conversation %s not found' % cid)

    def _handle_action_conv_invite(self, cid, account):
        '''handle e3.Action.ACTION_CONV_INVITE
        '''
        if cid in self.conversations:
            self.conversations[cid].invite(account)
        else:
            log.warning('conversation %s not found' % cid)

    def _handle_action_send_message(self, cid, message):
        '''handle e3.Action.ACTION_SEND_MESSAGE
        cid is the conversation id, message is a MsnMessage object
        '''
        if cid not in self.conversations:
            if cid in self.pending_cids:
                self.pending_messages[cid].append(message)
            else:
                self.session.add_event(e3.Event.EVENT_ERROR,
                    'invalid conversation id')
        else:
            conversation = self.conversations[cid]

            if conversation.status == Conversation.Conversation.STATUS_CLOSED:
                conversation.status = Conversation.Conversation.STATUS_PENDING
                self._handle_action_new_conversation(None, conversation.cid)

            conversation.send_message(message)
