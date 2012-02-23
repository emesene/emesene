import socket

from Worker import Worker
from MailClients import *
import e3

import logging
log = logging.getLogger('jabber.Session')

class Session(e3.Session):
    '''a specialization of e3.Session'''
    NAME = 'Jabber session'
    DESCRIPTION = 'Session to connect to the Jabber network'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    SERVICES = {
        "gtalk": {
            "host": "talk.google.com",
            "port": "5223"
        },
        "facebook": {
            "host": "chat.facebook.com",
            "port": "5222"
        }
    }

    def __init__(self, id_=None, account=None):
        '''constructor'''
        e3.Session.__init__(self, id_, account)
        self.mail_client = NullMail()

    def login(self, account, password, status, proxy, host, port, use_http=False):
        '''start the login process'''
        self.account = e3.Account(account, password, status, host)

        if host == "talk.google.com":
            try:
                self.mail_client = IMAPMail(self, "imap.gmail.com", 993, account, password)
            except socket.error, sockerr:
                log.warn("couldn't connect to mail server " + str(sockerr))
                
            # gtalk allows to connect on port 80, it's not HTTP protocol but
            # the port is HTTP so it will pass through firewalls (yay!)
            if use_http:
                port = 80
        elif host == "chat.facebook.com":
            try:
                self.mail_client = FacebookMail(self)
            except socket.error, sockerr:
                log.warn("couldn't connect to mail server " + str(sockerr))

        self.mail_client.register_handler('mailcount', self.mail_count_changed)
        self.mail_client.register_handler('mailnew', self.mail_received)
        self.mail_client.register_handler('socialreq', self.social_request)

        self.__worker = Worker('emesene2', self, proxy, use_http)
        self.__worker.start()

        self.add_action(e3.Action.ACTION_LOGIN, (account, password, status,
            host, port))

    def start_mail_client(self):
        self.mail_client.start()
        
    def stop_mail_client(self):
        self.mail_client.stop()

    def send_message(self, cid, text, style=None, cedict=None, celist=None):
        '''send a common message'''
        if cedict is None:
            cedict = {}

        if celist is None:
            celist = []

        account = self.account.account
        message = e3.Message(e3.Message.TYPE_MESSAGE, text, account,
            style)
        self.add_action(e3.Action.ACTION_SEND_MESSAGE, (cid, message))

    def send_typing_notification(self, cid):
        '''send typing notification to contact'''
        ##FIXME: implement this
        pass

    def request_attention(self, cid):
        '''request the attention of the contact'''
        account = self.account.account
        message = e3.Message(e3.Message.TYPE_MESSAGE,
            '%s requests your attention' % (account, ), account)
        self.add_action(e3.Action.ACTION_SEND_MESSAGE, (cid, message))
