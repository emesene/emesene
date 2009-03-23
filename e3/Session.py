import e3
import protocol.Session
from protocol.Action import Action

class Session(protocol.Session):
    '''a specialization of protocol.Session'''
    NAME = 'MSN session'
    DESCRIPTION = 'Session to connect to the MSN network'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, id_=None, account=None):
        '''constructor'''
        protocol.Session.__init__(self, id_, account)

    def login(self, account, password, status, proxy, use_http=False):
        '''start the login process'''
        socket = e3.MsnSocket('messenger.hotmail.com', 1863, dest_type='NS')
        worker = e3.Worker('emesene2', socket, self, e3.MsnSocket)
        socket.start()
        worker.start()

        self.account = e3.Account(account, password, status)

        self.add_action(Action.ACTION_LOGIN, (account, password, status))

    def send_message(self, cid, text, style=None):
        '''send a common message'''
        account = self.account.account
        message = e3.Message(e3.Message.TYPE_MESSAGE, text, account, style)
        self.add_action(Action.ACTION_SEND_MESSAGE, (cid, message))

    def request_attention(self, cid):
        '''send a nudge message'''
        account = self.account.account
        message = e3.Message(e3.Message.TYPE_NUDGE, None, account)
        self.add_action(Action.ACTION_SEND_MESSAGE, (cid, message))
