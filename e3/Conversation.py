import Queue
import threading

import MsnMessage
import p2p.Manager
import protocol.Contact
import protocol.Action as Action
import protocol.Logger as Logger
from protocol.Event import Event

class Conversation(threading.Thread):
    '''a thread that handles a conversation'''
    (STATUS_PENDING, STATUS_CONNECTED, STATUS_ESTABLISHED, STATUS_CLOSED,
    STATUS_ERROR) = range(5)

    def __init__(self, session, cid, MsnSocket, host, port, account, 
        session_id, p2p_input, auth_id=None):
        '''class constructor, create a socket and connect it to the specified
        server'''
        threading.Thread.__init__(self)
        self.setDaemon(True)

        self.cid = cid
        self.host = host
        self.port = port
        self.session = session
        self.account = account
        self.auth_id = auth_id
        self.session_id = session_id
        self.socket = MsnSocket(host, port)

        self.status = Conversation.STATUS_PENDING
        self.started = False
        # the last account to leave the conversation 
        self.last_member = None

        self.pending_invites = []
        # indicates if the first action made by the user to justify opening
        # a new conversation has been made or not
        self.first_action = False

        self.p2p_input = p2p_input

        # this queue receives a Command object
        self.command_queue = Queue.Queue()

        self._handlers = {}
        self.members = []
        # messages that are requested to be sent before we are ready to do it
        # are stored here and sent when we stablish the conversation
        self.pending_messages = []
        # a dict that contains the tid where the message was sent and the
        # message, when we receive an ack, we emit the message send succeed
        # and remove it from the dict, if we get a NAK we remove it and emit
        # the message send failed.
        self.sent_messages = {}
        self._set_handlers()

    def _set_handlers(self):
        '''set the handlers for the commands'''
        self._handlers['MSG'] = self._on_message
        self._handlers['USR'] = self._on_usr
        self._handlers['IRO'] = self._on_iro
        self._handlers['JOI'] = self._on_join
        self._handlers['ANS'] = self._on_answer
        self._handlers['BYE'] = self._on_bye
        self._handlers['ACK'] = self._on_message_send_succeed
        self._handlers['NAK'] = self._on_message_send_failed

    def _process(self, message):
        '''process a command and call the respective handler'''
        #print '<c<', message
        handler = self._handlers.get(message.command, None)

        if handler:
            handler(message)
        else:
            self._on_unknown_command(message)

    def run(self):
        '''the main method of the thread'''
        self.socket.start()
        data = None

        while True:
            try:
                data = self.socket.output.get(True, 0.1)

                if type(data) == int and data == 0:
                    self._close()
                    break
                else:
                    self._process(data)
            except Queue.Empty:
                pass

            try:
                cmd = self.command_queue.get(True, 0.1)

                if cmd == 'quit':
                    self._close()
                    break

                self.socket.send_command(cmd.command, cmd.params, cmd.payload)
            except Queue.Empty:
                pass

    def _close(self):
        '''set all the attributes to reflect a closed conversation
        caution: it doesn't stop the main thread'''
        print 'closing conversation', self.cid
        self.status = Conversation.STATUS_CLOSED
        self.started = False
        self.socket.quit()

    def _on_message(self, command):
        '''handle the message'''
        message = MsnMessage.Message.parse(command)
        # TODO: nudge and file transfer invitations goes here too
        if (message.type == MsnMessage.Message.TYPE_MESSAGE or \
            message.type == MsnMessage.Message.TYPE_NUDGE) and \
            not self.first_action:
            self.first_action = True
            self.session.add_event(Event.EVENT_CONV_FIRST_ACTION, self.cid,
                self.members[:])

        if message.type == MsnMessage.Message.TYPE_MESSAGE or \
                message.type == MsnMessage.Message.TYPE_TYPING or \
                message.type == MsnMessage.Message.TYPE_NUDGE:
            self.session.add_event(Event.EVENT_CONV_MESSAGE, 
                self.cid, message.account, message)

            # log the message
            if message.type != MsnMessage.Message.TYPE_TYPING:
                contact = self.session.contacts.get(message.account)

                if contact is None:
                    contact = protocol.Contact(message.account)

                src =  Logger.Account(contact.attrs.get('CID', None), None, 
                    contact.account, contact.status, contact.nick, 
                    contact.message, contact.picture)

                dst = self.session.contacts.me

                dest =  Logger.Account(dst.attrs.get('CID', None), None, 
                    dst.account, dst.status, dst.nick, dst.message, dst.picture)

                # we remove the content type part since it's always equal
                msgstr = message.format().split('\r\n', 1)[1]
                # remove the Content-type, X-MMS-IM-Format and TypingUser 
                # XXX WHAT THE HELL
                msgstr = msgstr.replace('Content-Type: ', '')
                msgstr = msgstr.replace('X-MMS-IM-Format: ', '')
                msgstr = msgstr.replace('TypingUser: ', '')

                self.session.logger.log('message', contact.status, msgstr, 
                    src, dest)
        elif message.type == MsnMessage.Message.TYPE_P2P and \
                message.dest == self.account and \
                len(self.members) == 0:
            self.p2p_input.put((p2p.Manager.ACTION_INPUT,
                self.members[0], message))
        
    def _on_usr(self, message):
        '''handle the message'''
        if message.param_num_is(0, 'OK'):
            self.status = Conversation.STATUS_ESTABLISHED

            for account in self.pending_invites:
                self.socket.send_command('CAL', (account,))

            self.pending_invites = []

    def _on_iro(self, message):
        '''handle the message
        IRO 1 1 1 luismarianoguerra@gmail.com marianoguerra. 1342472230'''

        (unk1, unk2, account, nick, unk3) = message.params

        self._check_if_started()

        self.session.add_event(Event.EVENT_CONV_CONTACT_JOINED, self.cid, 
            account)

        if len(self.members) == 1:
            self.session.add_event(Event.EVENT_CONV_GROUP_STARTED, self.cid)
        else:
            self.p2p_input.put((p2p.Manager.ACTION_REGISTER, self.cid))

        self.members.append(account)

    def _on_join(self, message):
        '''handle the message'''
        account = message.tid
        
        self._check_if_started()

        self.session.add_event(Event.EVENT_CONV_CONTACT_JOINED, self.cid, 
            account)

        if len(self.members) == 1:
            self.session.add_event(Event.EVENT_CONV_GROUP_STARTED, self.cid)
        else:
            self.p2p_input.put((p2p.Manager.ACTION_REGISTER, self.cid))

        self.members.append(account)

    def _on_answer(self, message):
        '''handle the message'''
        if message.param_num_is(0, 'OK'):
            self.status = Conversation.STATUS_ESTABLISHED
            self.session.add_event(Event.EVENT_CONV_STARTED, self.cid)

    def _on_bye(self, message):
        '''handle the bye message'''
        account = message.tid.replace('\r\n', '')
        self.session.add_event(Event.EVENT_CONV_CONTACT_LEFT, self.cid, 
            account)

        self.members.remove(account)

        if len(self.members) == 1:
            self.session.add_event(Event.EVENT_CONV_GROUP_ENDED, self.cid)
        elif len(self.members) == 0:
            self._close()
            self.last_member = account
            self.p2p_input.put((p2p.Manager.ACTION_UNREGISTER, self.cid))

    def _on_message_send_succeed(self, command):
        '''handle the acknowledge of a message'''
        tid = int(command.tid)
        if tid in self.sent_messages:
            message = self.sent_messages[tid]
            del self.sent_messages[tid]
            self.session.add_event(Event.EVENT_CONV_MESSAGE_SEND_SUCCEED,
                self.cid, message)

    def _on_message_send_failed(self, command):
        '''handle a message that inform us that a message could not be sent'''
        tid = int(command.tid)
        if tid in self.sent_messages:
            message = self.sent_messages[tid]
            del self.sent_messages[tid]
            self.session.add_event(Event.EVENT_CONV_MESSAGE_SEND_FAILED,
                self.cid, message)
            self._log_message(message, True)

    def _on_unknown_command(self, message):
        '''handle the unknown commands'''
        print 'unknown command:', str(message)

    def _check_if_started(self):
        '''check if the conversation has already been started, if not,
        send an event to inform that we are ready to chat.
         Send the pending messages if there are some.
        '''

        if not self.started:
            self.session.add_event(Event.EVENT_CONV_STARTED, self.cid)
            self.started = True

            if len(self.pending_messages) > 0:
                for message in self.pending_messages:
                    self.send_message(message)

                self.pending_messages = []

    def add_transfer(self, transfer):
        '''add a transfer to the list of active transfers on this conversation
        '''
        self.transfers[transfer.pid] = transfer

    def reconnect(self, MsnSocket, host, port, session_id):
        '''restablish connection with the switchboard server'''
        self.host = host
        self.port = port
        self.session_id = session_id
        self.socket.quit()
        self.socket = MsnSocket(host, port)
        self.send_presentation()

        if len(self.members) == 0 and self.last_member:
            self.invite(self.last_member)
            self.last_member = None
        else:
            print 'reinviting members', self.members
            members = self.members
            self.members = []
            while len(self.members):
                member = self.members.pop()
                self.invite(member)

        self.socket.start()

    def invite(self, account):
        '''invite a contact to the conversation'''
        if self.status != Conversation.STATUS_ESTABLISHED:
            self.pending_invites.append(account)
        else:
            print 'sending CAL', account
            self.socket.send_command('CAL', (account,))

    def answer(self):
        '''answer a request from the server'''
        self.socket.send_command('ANS', (self.session.account.account, 
            self.auth_id, self.session_id))

    def send_presentation(self):
        '''send a presentation of ourselves'''
        self.socket.send_command('USR', (self.session.account.account, 
            self.session_id))

    def send_message(self, message):
        '''send a message to the conversation'''
        if not self.started:
            self.pending_messages.append(message)
        else:
            self.sent_messages[self.socket.tid] = message
            # TODO: change that A when applies
            self.socket.send_command('MSG', ('A',), message.format())
            self._log_message(message)

    def _log_message(self, message, error=False):
            # log the message
            contact = self.session.contacts.me
            src =  Logger.Account(contact.attrs.get('CID', None), None, 
                contact.account, contact.status, contact.nick, contact.message,
                contact.picture)

            # we remove the content type part since it's always equal
            msgstr = message.format().split('\r\n', 1)[1]
            # remove the Content-type, X-MMS-IM-Format and TypingUser 
            msgstr = msgstr.replace('Content-Type: ', '')
            msgstr = msgstr.replace('X-MMS-IM-Format: ', '')
            msgstr = msgstr.replace('TypingUser: ', '')

            if error:
                event = 'message-error'
            else:
                event = 'message'

            for dst_account in self.members:
                dst = self.session.contacts.get(dst_account)

                if dst is None:
                    dst = protocol.Contact(message.account)

                dest =  Logger.Account(dst.attrs.get('CID', None), None, 
                    dst.account, dst.status, dst.nick, dst.message, dst.picture)

                self.session.logger.log(event, contact.status, msgstr, 
                    src, dest)

