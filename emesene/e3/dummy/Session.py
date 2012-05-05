import Worker
import e3
import extension
import gobject

class Session(e3.Session):
    '''a specialization of e3.Session'''
    NAME = 'Dummy session'
    DESCRIPTION = 'Session to test the client (no connection)'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    SERVICES = {
        "dummy": {
            "host": "dummy.server.com",
            "port": "1337"
        }
    }

    def __init__(self, id_=None, account=None):
        '''constructor'''
        e3.Session.__init__(self, id_, account)

    def login(self, account, password, status, proxy, host, port, use_http=False):
        '''start the login process'''
        self.account = e3.Account(account, password, status, host)
        worker = Worker.Worker('emesene2', self, proxy, use_http)
        worker.start()

        self.add_action(e3.Action.ACTION_LOGIN, (account, password, status))

        #test pending contact dialog
        gobject.timeout_add(300, self._test_pending_contacts)

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

    def _test_pending_contacts(self):
        tmp_cont = e3.base.Contact("test1@test.com", 1,
            "test1", "test1nick",
            e3.status.BUSY, '',
            True)
        self.contacts.pending["test1@test.com"] = tmp_cont

        tmp_cont = e3.base.Contact("test2@test.com", 2,
            "test2", "test2nick",
            e3.status.ONLINE, '',
            True)
        self.contacts.pending["test2@test.com"] = tmp_cont

        return False

    def send_typing_notification(self, cid):
        '''send typing notification to contact'''
        pass

    def request_attention(self, cid):
        '''request the attention of the contact'''
        account = self.account.account
        message = e3.Message(e3.Message.TYPE_NUDGE,
            '%s requests your attention' % (account, ), account)
        self.add_action(e3.Action.ACTION_SEND_MESSAGE, (cid, message))

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

        return True

extension.implements(Session, 'session')
