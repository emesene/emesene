from Worker import Worker

import e3

import logging

log = logging.getLogger('WebQQ.Session')

class Session(e3.Session):
    '''a specialization of e3.Session'''
    NAME = 'WebQQ Session'
    DESCRIPTION = 'Session to connect to the WebQQ network'
    AUTHOR = 'Xiang Wang (Devil Wang)'
    WEBSITE = 'www.emesene.org'

    SERVICES = {
        "webqq": {
            "host": "web.qq.com",
            "port": "80"
        },
    }

    def __init__(self, id_=None, account=None):
        '''constructor'''
        e3.Session.__init__(self, id_, account)

    def login(self, account, password, status, proxy, host, port , use_http=False, use_ipv6=False):
        '''start the login process'''

        self.account = e3.Account(account, password, status, host)

        self.__worker = Worker('emesene2', self, proxy, use_http)
        self.__worker.start()

        self.add_action(e3.Action.ACTION_LOGIN, (account, password, status,
            host, port))

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

    def session_has_service(self, service):
        '''returns True if some service is supported, False otherwise'''
        if service in [Session.SERVICE_CONTACT_MANAGING,
                        Session.SERVICE_CONTACT_BLOCK,
                        Session.SERVICE_CONTACT_ALIAS,
                        Session.SERVICE_GROUP_MANAGING,
                        Session.SERVICE_CONTACT_INVITE,
                        Session.SERVICE_CALLS,
                        Session.SERVICE_FILETRANSFER]:
            return False
        else:
            return True

    def request_attention(self, cid):
        '''request the attention of the contact'''
        self.__worker.send_buddy_nudge(cid)
