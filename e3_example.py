import Queue

import e3
import e3.Worker as Worker
import e3.MsnSocket as MsnSocket

from protocol.base import status
from protocol.base import Event
from protocol.base import Action
from protocol.base import Session
import protocol.base.Account as Account

from protocol.base.ContactManager import ContactManager

# i will use the gobject main loop, but you can use what you want..
import gobject


class Example(object):
    '''a example object, you can do it on another way..'''

    def __init__(self, account, password, status):
        '''class constructor'''
        self.account = Account(account, password, status)
        self.session = Session(self.account)
        self.socket = MsnSocket('messenger.hotmail.com', 1863)
        self.worker = Worker(self.socket, self.session)

        hdrs = {}
        hdrs[Event.EVENT_LOGIN_SUCCEED] = self._handle_login_succeed
        hdrs[Event.EVENT_LOGIN_FAILED] = self._handle_login_failed
        hdrs[Event.EVENT_CONTACT_LIST_READY] = self._handle_contact_list_ready
        hdrs[Event.EVENT_CONV_FIRST_ACTION] = self._handle_conv_first_action
        hdrs[Event.EVENT_CONV_MESSAGE] = self._handle_conv_message
        hdrs[Event.EVENT_CONV_STARTED] = self._handle_conv_started

        self._handlers = hdrs

    def login(self):
        '''start the login process'''
        self.socket.start()
        self.worker.start()

        self.add_action(Action.ACTION_LOGIN, 
            (self.account.account, self.account.password, self.account.status))

    def add_action(self, id_, args=()):
        '''add an event to the session queue'''
        self.session.actions.put(Action(id_, args))

    def _handle_login_succeed(self, ):
        '''handle login succeed'''
        print 'we are in! :)'

    def _handle_login_failed(self, ):
        '''handle login failed'''
        print 'login failed :('

    def _handle_contact_list_ready(self, ):
        '''handle contact list ready'''
        for group in self.session.groups.values():
            # get a list of contact objects from a list of accounts
            contacts = self.session.contacts.get_contacts(group.contacts)
            for contact in contacts:
                print contact.account, 'in', group.name

        print 'contacts in no group'
        for contact in self.session.contacts.get_no_group():
            print contact.account

        # we start a conversation with someone, when the conversation starts
        # we will send a "hey you!" message
        self.start_conversation('luismarianoguerra@gmail.com')

    def _handle_conv_first_action(self, cid):
        '''handle'''
        account = self.session.account.account
        message = e3.Message(e3.Message.TYPE_MESSAGE, 'welcome', account)
        self.send_message(cid, message)

    def _handle_conv_started(self, cid):
        '''handle a new conversation created'''
        print '#' * 200
        account = self.session.account.account
        mymessage = e3.Message(e3.Message.TYPE_MESSAGE, 'hey you!', account)
        self.send_message(cid, mymessage)

    def _handle_conv_message(self, cid, sender, message):
        '''handle a message'''
        # when we receive a message, we return the same message and 
        # send a new one with a smile
        # it will also return the typing messages, so if you are typing
        # you will get a typing notification and a smile from nowere :P
        self.send_message(cid, message)
        account = self.session.account.account
        mymessage = e3.Message(e3.Message.TYPE_MESSAGE, ':)', account)
        self.send_message(cid, mymessage)

    def process(self):
        '''get events from the event Queue and process them'''
        try:
            event = self.session.events.get(False)

            if event.id_ in self._handlers:
                self._handlers[event.id_](*event.args)
        except Queue.Empty:
            pass

        return True

    def send_message(self, cid, message):
        '''send a common message'''
        account = self.session.account.account
        self.add_action(Action.ACTION_SEND_MESSAGE, (cid, message))

    def start_conversation(self, account):
        '''start a conversation with account'''
        self.add_action(Action.ACTION_NEW_CONVERSATION, (account,))

if __name__ == '__main__':
    gobject.threads_init()
    example = Example('xmxsxn@hotmail.com', 'contrasena', status.ONLINE) 
    example.login()

    gobject.timeout_add(500, example.process)
    gobject.MainLoop().run()
