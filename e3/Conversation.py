import Queue
import threading

import protocol.base.Action as Action
import protocol.base.Event as Event
import MsnSocket
import MsnMessage

class Conversation(threading.Thread):
    '''a thread that handles a conversation'''
    (STATUS_PENDING, STATUS_CONNECTED, STATUS_ESTABLISHED, STATUS_CLOSED,
    STATUS_ERROR) = range(5)

    def __init__(self, session, cid, host, port, account, session_id, 
        auth_id=None):
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
        self.socket = MsnSocket.MsnSocket(host, port)

        self.status = Conversation.STATUS_PENDING

        self.pending_invites = []
        # indicates if the first action made by the user to justify opening
        # a new conversation has been made or not
        self.first_action = False

        # this queue receives a Command object
        self.command_queue = Queue.Queue()

        self._handlers = {}
        self.members = []
        self._set_handlers()

    def _set_handlers(self):
        '''set the handlers for the commands'''
        self._handlers['MSG'] = self._on_message
        self._handlers['USR'] = self._on_usr
        self._handlers['IRO'] = self._on_iro
        self._handlers['JOI'] = self._on_join
        self._handlers['ANS'] = self._on_answer
        self._handlers['BYE'] = self._on_bye

    def _process(self, message):
        '''process a command and call the respective handler'''
        print '<c<', message
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
                self._process(data)
            except Queue.Empty:
                pass

            try:
                cmd = self.command_queue.get(True, 0.1)
                self.socket.send_command(cmd.command, cmd.params, cmd.payload)
            except Queue.Empty:
                pass

    def _on_message(self, command):
        '''handle the message'''
        message = MsnMessage.Message.parse(command)
        # TODO: nudge and file transfer invitations goes here too
        if (message.type == MsnMessage.Message.TYPE_MESSAGE or \
            message.type == MsnMessage.Message.TYPE_NUDGE) and \
            not self.first_action:
            self.first_action = True
            self.session.add_event(Event.EVENT_CONV_FIRST_ACTION, self.cid)

        if message.type == MsnMessage.Message.TYPE_MESSAGE or \
                message.type == MsnMessage.Message.TYPE_TYPING or \
                message.type == MsnMessage.Message.TYPE_NUDGE:
            self.session.add_event(Event.EVENT_CONV_MESSAGE, 
                self.cid, message.account, message)
        
    def _on_usr(self, message):
        '''handle the message'''
        if message.param_num_is(0, 'OK'):
            self.status = Conversation.STATUS_ESTABLISHED
            self.session.add_event(Event.EVENT_CONV_STARTED, self.cid)

            for account in self.pending_invites:
                self.socket.send_command('CAL', (account,))

    def _on_iro(self, message):
        '''handle the message
        IRO 1 1 1 luismarianoguerra@gmail.com marianoguerra. 1342472230'''

        (unk1, unk2, account, nick, unk3) = message.params

        self.session.add_event(Event.EVENT_CONV_CONTACT_JOINED, self.cid, 
            account)

        if len(self.members) == 1:
            self.session.add_event(Event.EVENT_CONV_GROUP_STARTED, self.cid)

        self.members.append(account)

    def _on_join(self, message):
        '''handle the message'''
        account = message.tid

        self.session.add_event(Event.EVENT_CONV_CONTACT_JOINED, self.cid, 
            account)

        if len(self.members) == 1:
            self.session.add_event(Event.EVENT_CONV_GROUP_STARTED, self.cid)

        self.members.append(account)

    def _on_answer(self, message):
        '''handle the message'''
        if message.param_num_is(0, 'OK'):
            self.status = Conversation.STATUS_ESTABLISHED
            self.session.add_event(Event.EVENT_CONV_STARTED, self.cid)

    def _on_bye(self, message):
        '''handle the message'''
        account = message.tid.replace('\r\n', '')
        self.session.add_event(Event.EVENT_CONV_CONTACT_LEFT, self.cid, 
            account)

        self.members.remove(account)

        if len(self.members) == 1:
            self.session.add_event(Event.EVENT_CONV_GROUP_ENDED, self.cid)

    def _on_unknown_command(self, message):
        '''handle the unknown commands'''
        print 'unknown command:', str(message)

    # action handlers

    def invite(self, account):
        '''invite a contact to the conversation'''
        if self.status != Conversation.STATUS_ESTABLISHED:
            self.pending_invites.append(account)
        else:
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
        self.socket.send_command('MSG', ('A',), message.format())
