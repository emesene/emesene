import e3

class ContactInformation(object):
    '''a window that displays information about a contact'''

    def __init__(self, session, account):
        '''constructor'''
        self.session = session
        self.account = account

    def fill_all(self):
        '''fill all the lists'''
        if self.session:
            self.fill_nicks()
            self.fill_status()
            self.fill_messages()

    def fill_nicks(self):
        '''fill the nick history (clear and refill if called another time)'''
        self.session.logger.get_nicks(self.account, 1000, self.on_nicks_ready)

    def fill_messages(self):
        '''fill the messages history (clear and refill if called another time)
        '''
        self.session.logger.get_messages(self.account, 1000,
            self.on_messages_ready)

    def fill_status(self):
        '''fill the status history (clear and refill if called another time)'''
        self.session.logger.get_status(self.account, 1000,
            self.on_status_ready)

    def fill_chats(self):
        '''fill the chats history (clear and refill if called another time)'''
        self.session.logger.get_chats(self.account,
            self.session.account.account, 1000, self.chats._on_chats_ready)

    def add_nick(self, stat, timestamp, nick):
        '''add a nick to the list of nicks'''
        raise NotImplementedError()

    def add_message(self, stat, timestamp, message):
        '''add a message to the list of message'''
        raise NotImplementedError()

    def add_status(self, stat, timestamp, status):
        '''add a status to the list of status'''
        raise NotImplementedError()

    def on_nicks_ready(self, results):
        '''called when the nick history is ready'''
        if not results:
            return

        for (stat, timestamp, nick) in results:
            self.add_nick(stat, timestamp, nick)

    def on_messages_ready(self, results):
        '''called when the message history is ready'''
        if not results:
            return

        for (stat, timestamp, message) in results:
            self.add_message(stat, timestamp, message)

    def on_status_ready(self, results):
        '''called when the status history is ready'''
        if not results:
            return

        for (stat, timestamp, stat_) in results:
            self.add_status(stat, timestamp, e3.status.STATUS.get(stat,
                'unknown'))

