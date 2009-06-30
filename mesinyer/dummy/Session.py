import Worker
import protocol.Account
import protocol.Message
import protocol.Session
from protocol.Action import Action

class Session(protocol.Session):
    '''a specialization of protocol.Session'''
    NAME = 'Dummy session'
    DESCRIPTION = 'Session to test the client (no connection)'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, id_=None, account=None):
        '''constructor'''
        protocol.Session.__init__(self, id_, account)

    def login(self, account, password, status, proxy, use_http=False):
        '''start the login process'''
        self.account = protocol.Account(account, password, status)
        worker = Worker.Worker('emesene2', self, proxy, use_http)
        worker.start()

        self.add_action(Action.ACTION_LOGIN, (account, password, status))

    def send_message(self, cid, text, style=None):
        '''send a common message'''
        account = self.account.account
        message = protocol.Message(protocol.Message.TYPE_MESSAGE, text, account,
            style)
        self.add_action(Action.ACTION_SEND_MESSAGE, (cid, message))

    def request_attention(self, cid):
        '''request the attention of the contact'''
        account = self.account.account
        message = protocol.Message(protocol.Message.TYPE_MESSAGE, 
            '%s requests your attention' % (account, ), account)
        self.add_action(Action.ACTION_SEND_MESSAGE, (cid, message))
