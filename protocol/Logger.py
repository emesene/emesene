import time
import Queue
import threading
import sqlite3.dbapi2 as sqlite

class Account(object):
    '''a class to store account data'''

    def __init__(self, id_, account, status, nick, message, path):
        '''constructor'''
        self.id = id_
        self.account = account
        self.status = status
        self.nick = nick
        self.message = message
        self.path = path

    def equals(self, account, status, nick, message, path):
        '''return True if all the fields except the id are equals'''
        if self.account == account and self.status == status and \
            self.nick == nick and self.message == message and self.path == path:
            return True

    def __str__(self):
        '''return a string representation of the object'''
        return "<account '%s'>" % (self.account,)

class Logger(object):
    '''a class to log activity on an IM'''

    COMMIT_LIMIT = 20

    EVENTS = ('nick change', 'status change', 'message change', 'image change',
        'message')

    CREATE_D_TIME = '''
        CREATE TABLE d_time
        (
          id_time INTEGER PRIMARY KEY,
          year INTEGER,
          month INTEGER,
          day INTEGER,
          wday INTEGER,
          hour INTEGER,
          minute INTEGER,
          seconds INTEGER
        );
    '''

    CREATE_D_ACCOUNT = '''
        CREATE TABLE d_account
        (
          id_account INTEGER PRIMARY KEY,
          account TEXT,
          status INTEGER,
          nick TEXT,
          message TEXT,
          path TEXT
        );
    '''

    INDEX_ACCOUNT = '''
        CREATE INDEX account_index ON d_account(account);
    '''

    CREATE_D_EVENT = '''
        CREATE TABLE d_event
        (
          id_event INTEGER PRIMARY KEY,
          name TEXT
        );
    '''

    CREATE_FACT_EVENT = '''
        CREATE TABLE fact_event
        (
          id_time INTEGER PRIMARY KEY,
          id_event INTEGER,
          id_src_acc INTEGER,
          id_dest_acc INTEGER,
          
          payload TEXT,
          tmstp FLOAT
        );
    '''

    CREATE_LAST_ACCOUNT = '''
        CREATE TABLE last_account
        (
          id_account INTEGER,
          account TEXT,
          status INTEGER,
          nick TEXT,
          message TEXT,
          path TEXT
        );
    '''

    INSERT_TIME = '''
        INSERT INTO d_time(id_time, year, month, day, wday, hour, minute,
        seconds) VALUES(NULL, ?, ?, ?, ?, ?, ?, ?);
    '''

    INSERT_ACCOUNT = '''
        INSERT INTO d_account(id_account, account, status, nick, message, path) 
        VALUES(NULL, ?, ?, ?, ?, ?);
    '''

    INSERT_EVENT = '''
        INSERT INTO d_event(id_event, name) VALUES(NULL, ?);
    '''

    INSERT_FACT_EVENT = '''
        INSERT INTO fact_event(id_time, id_event, id_src_acc, id_dest_acc, 
            payload, tmstp) 
        VALUES(?, ?, ?, ?, ?, ?);
    '''

    INSERT_LAST_ACCOUNT = '''
        INSERT INTO last_account(id_account, account, status, nick, message, 
            path) 
        VALUES(?, ?, ?, ?, ?, ?);
    '''

    UPDATE_LAST_ACCOUNT = '''
        UPDATE last_account SET id_account=?, status=?, nick=?, message=?, 
            path=? 
        WHERE account=?;
    '''

    SELECT_LAST_ACCOUNTS = '''
        SELECT id_account, account, status, nick, message, path 
        FROM last_account
    '''

    SELECT_EVENTS = '''
        SELECT id_event, name FROM d_event;
    '''

    SELECT_ACCOUNT_EVENT = '''
        SELECT tmstp, payload from fact_event, d_account 
        WHERE id_event=? and id_src_acc=id_account and account=? 
        ORDER BY tmstp LIMIT ?;
    '''

    SELECT_SENT_MESSAGES = '''
        SELECT f.tmstp, f.payload 
        FROM fact_event f, d_account s, d_account d
        WHERE f.id_event=? and f.id_src_acc=s.id_account and 
            id_dest_acc=d.id_account and 
            s.account=? and d.account=? 
        ORDER BY tmstp LIMIT ?;
    '''

    SELECT_CHATS = '''
        SELECT f.tmstp, f.payload, f.id_src_acc 
        FROM fact_event f, d_account s, d_account d
        WHERE f.id_event=? and f.id_src_acc=s.id_account and 
            id_dest_acc=d.id_account and 
            ((s.account=? and d.account=?) 
                or (d.account=? or d.account=?)
            )
        ORDER BY tmstp LIMIT ?;
    '''

    def __init__(self, path):
        '''constructor'''
        self.path = path

        self.accounts = {}
        self.events = {}

        self.connection = sqlite.connect(path)
        self.cursor = self.connection.cursor()

        self._count = 0

        try:
            self._create()
        except sqlite.OperationalError:
            self._load_events()
            self._load_accounts()

    def _create(self):
        '''create the database'''
        self.execute(Logger.CREATE_D_TIME)
        self.execute(Logger.CREATE_D_ACCOUNT)
        self.execute(Logger.CREATE_D_EVENT)
        self.execute(Logger.CREATE_FACT_EVENT)
        self.execute(Logger.CREATE_LAST_ACCOUNT)
        self.execute(Logger.INDEX_ACCOUNT)

        for event in Logger.EVENTS:
            id_event = self.insert_event(event)
            self.events[event] = id_event

    def _load_accounts(self):
        '''load the accounts from the last_account table and store them in
        a dict'''
        self.execute(Logger.SELECT_LAST_ACCOUNTS)

        for (id_account, account, status, nick, message, path) in \
                self.cursor.fetchall():
            self.accounts[account] = Account(id_account, account, status, nick,
                message, path)

    def _load_events(self):
        '''load the events from the d_event table and store them in a dict'''
        self.execute(Logger.SELECT_EVENTS)

        for (id_event, event) in self.cursor.fetchall():
            self.events[event] = id_event

    def insert_time(self, year, month, day, wday, hour, minute,
            seconds):
        '''insert a row into the d_time table, returns the id'''
        self.execute(Logger.INSERT_TIME, 
            (year, month, day, wday, hour, minute, seconds))

        self._stat()

        return self.cursor.lastrowid

    def insert_time_now(self):
        '''insert a row into the d_time table with the time information of 
        this moment, returns the id'''
        (year, month, day, hour, minute, seconds, wday, yday, tm_isdst) = \
            time.gmtime()

        return self.insert_time(year, month, day, wday, hour, minute, 
            seconds)

    def insert_account(self, account, status, nick, message, path): 
        '''insert a row into the d_account table, returns the id'''

        exists = False

        if account in self.accounts:
            exists = True
            acc = self.accounts[account]
            if acc.equals(account, status, nick, message, path):
                return acc.id

        self.execute(Logger.INSERT_ACCOUNT,
            (unicode(account), status, unicode(nick), unicode(message), 
                unicode(path)))

        id_account = self.cursor.lastrowid
        self.accounts[account] = Account(id_account, account, status, nick,
            message, path)

        if exists:
            self.update_last_account(id_account, account, status, nick, message,
                path)
        else:
            self.insert_last_account(id_account, account, status, nick, message,
                path)

        self._stat()

        return id_account 

    def insert_event(self, name):
        '''insert a row into the d_event table, returns the id'''
        if name in self.events:
            return self.events[name]

        self.execute(Logger.INSERT_EVENT, (unicode(name),))
        id_event = self.cursor.lastrowid

        self.events[name] = id_event

        self._stat()

        return id_event

    def insert_fact_event(self, id_time, id_event, id_src_acc, id_dest_acc,
            payload, timestamp):
        '''insert a row into the fact_event table, returns the id'''
        self.execute(Logger.INSERT_FACT_EVENT, 
            (id_time, id_event, id_src_acc, id_dest_acc, unicode(payload),
            timestamp))

        self._stat()

        return self.cursor.lastrowid

    def insert_last_account(self, id_account, account, status, nick, message, 
            path):
        '''insert a row into the d_account table, returns the id'''
        self.execute(Logger.INSERT_LAST_ACCOUNT,
            (id_account, unicode(account), status, unicode(nick), 
                unicode(message), unicode(path)))

        self._stat()

    def update_last_account(self, id_account, account, status, nick, message,
            path):
        '''update a row into the last_account table'''
        self.execute(Logger.UPDATE_LAST_ACCOUNT,
            (id_account, status, unicode(nick), unicode(message), 
                unicode(path), unicode(account)))

        self._stat()

    def _stat(self):
        '''called internally each time a transaction is made, here we control
        how often a commit is made'''

        if self._count >= Logger.COMMIT_LIMIT:
            t1 = time.time()
            self.connection.commit()
            print 'commit', time.time() - t1
            self._count = 0

        self._count += 1

    def execute(self, query, args=()):
        '''execute the query with optional args'''
        #print query, args
        self.cursor.execute(query, args)

    # utility methods

    def add_event(self, event, payload, src, dest=None):
        '''add an event on the fact and the dimensiones using the actual time'''
        id_event = self.insert_event(event)
        id_src = self.insert_account(src.account, src.status, src.nick, 
            src.message, src.path)

        if dest:
            id_dest = self.insert_account(dest.account, dest.status, dest.nick, 
                dest.message, dest.path)
        else:
            id_dest = None

        id_time = self.insert_time_now()
        timestamp = time.time()

        self.insert_fact_event(id_time, id_event, id_src, id_dest, payload, 
            timestamp)

    def close(self):
        '''call this method when you are closing the app'''
        self.connection.commit()
        self.cursor.close()
        self.connection.close()

    def get_event(self, account, event, limit=10):
        '''return the last # events of account, if event or account doesnt 
        exist return None'''

        id_event = self.events.get(event, None)

        if account is None or id_event is None:
            return None

        self.execute(Logger.SELECT_ACCOUNT_EVENT, (id_event, account, 
            limit))

        return [(x[0], x[1]) for x in self.cursor.fetchall()]

    def get_nicks(self, account, limit=10):
        '''return the last # nicks from account, where # is the limit value'''
        return self.get_event(account, 'nick change', limit)

    def get_messages(self, account, limit=10):
        '''return the last # messages from account, where # is the limit value
        '''
        return self.get_event(account, 'message change', limit)

    def get_status(self, account, limit=10):
        '''return the last # status from account, where # is the limit value
        '''
        return self.get_event(account, 'status change', limit)

    def get_images(self, account, limit=10):
        '''return the last # images from account, where # is the limit value
        '''
        return self.get_event(account, 'image change', limit)

    def get_sent_messages(self, src, dest, limit=10):
        '''return the last # sent from src to dest , where # is the limit value
        '''
        id_event = self.events.get('message', None)

        if src is None or dest is None or id_event is None:
            return None

        self.execute(Logger.SELECT_SENT_MESSAGES, (id_event, 
            src, dest, limit))

        return [(x[0], x[1]) for x in self.cursor.fetchall()]

    def get_chats(self, src, dest, limit=10):
        '''return the last # sent from src to dest or from dest to src , 
        where # is the limit value
        '''
        id_event = self.events.get('message', None)

        if src is None or dest is None or id_event is None:
            return None

        self.execute(Logger.SELECT_CHATS, (id_event, src, dest, dest, src, 
            limit))

        return [(x[0], x[1], x[2]) for x in self.cursor.fetchall()]

class LoggerProcess(threading.Thread):
    '''a process that exposes a thread safe api to log events of a session'''

    def __init__(self, path):
        '''constructor'''
        threading.Thread.__init__(self)
        self.setDaemon(True)

        self.path = path
        self.logger = None
        self.input = Queue.Queue()
        self.output = Queue.Queue()

        self.actions = {}

    def run(self):
        '''main method'''
        data = None
        self.logger = Logger(self.path)

        self.actions['get_event'] = self.logger.get_event
        self.actions['get_nicks'] = self.logger.get_nicks
        self.actions['get_messages'] = self.logger.get_messages
        self.actions['get_status'] = self.logger.get_status
        self.actions['get_images'] = self.logger.get_images
        self.actions['get_sent_messages'] = self.logger.get_sent_messages
        self.actions['get_chats'] = self.logger.get_chats

        while True:
            try:
                data = self.input.get(True)
                quit = self._process(data)

                if quit:
                    self.logger.close()
                    print 'closing logger thread'
                    break

            except Queue.Empty:
                pass

    def _process(self, data):
        '''process the received data'''
        (action, args) = data

        if action == 'log':
            (event, payload, src, dest) = args
            self.logger.add_event(event, payload, src, dest)
        elif action == 'quit':
            return True
        else:
            if action in self.actions:

                try:
                    self.output.put((action, self.actions[action](*args)))
                except:
                    print 'error calling action', action, 'on LoggerProcess'
        
        return False

    def log(self, event, payload, src, dest=None):
        '''add an event to the log database'''
        self.input.put(('log', (event, payload, src, dest)))

    def quit(self):
        '''stop the logger thread, and close the logger'''
        self.input.put(('quit', None))

    def get_event(self, account, event, limit=10):
        '''return the last # events of account, if event or account doesnt 
        exist return None'''
        self.input.put(('get_event', (account, event, limit)))

    def get_nicks(self, account, limit=10):
        '''return the last # nicks from account, where # is the limit value'''
        self.input.put(('get_nicks', (account, limit)))

    def get_messages(self, account, limit=10):
        '''return the last # messages from account, where # is the limit value
        '''
        self.input.put(('get_message', (account, limit)))

    def get_status(self, account, limit=10):
        '''return the last # status from account, where # is the limit value
        '''
        self.input.put(('get_status', (account, limit)))

    def get_images(self, account, limit=10):
        '''return the last # images from account, where # is the limit value
        '''
        self.input.put(('get_images', (account, limit)))

    def get_sent_messages(self, src, dest, limit=10):
        '''return the last # sent from src to dest , where # is the limit value
        '''
        self.input.put(('get_sent_messages', (src, dest, limit)))

    def get_chats(self, src, dest, limit=10):
        '''return the last # sent from src to dest or from dest to src , 
        where # is the limit value
        '''
        self.input.put(('get_chats', (src, dest, limit)))

def test():
    '''test the logger class'''
    import os
    import random
    import string

    import status
    
    logger = Logger(os.path.expanduser('~/logger_test.db'))

    accounts = {}

    def get_full_account():
        '''returns a full account object'''
        acc = get_account()
        if acc in accounts:
            return accounts[acc]

        stat = get_status()
        nick = get_text()
        message = get_text()
        path = get_text()

        account = Account(0, acc, stat, nick, message, path)

        accounts[acc] = account

        return account

    def get_account():
        '''return a random account'''
        domains = ('hotmail.com', 'live.com', 'gmail.com')
        users = ('bob', 'melinda', 'steve', 'linus', 'bill')
    
        return '@'.join((random.choice(users), random.choice(domains)))

    def get_status():
        '''return a random status'''
        return random.choice(status.ORDERED)

    def get_event():
        '''returns a random event'''
        return random.choice(Logger.EVENTS)

    def get_text():
        '''returns a random text'''
        return ''.join(random.choice(string.letters) for x in \
                range(random.randint(8, 128)))

    def get_payload(event):
        '''returns a random payload that is useful for the event'''
        if event == 'status change':
            return get_status()
        else:
            return get_text()

    def modify_account(event, payload, account):
        '''modify the field of an account accordint to the event'''
        if event == 'nick change':
            accounts[account.account].nick = payload
        elif event == 'message change':
            accounts[account.account].message = payload
        elif event == 'image change':
            accounts[account.account].path = payload
        elif event == 'status change':
            accounts[account.account].status = payload

    while True:
        #time.sleep(random.randint(1, 4))

        event = get_event()
        payload = get_payload(event)
        src = get_full_account()
        dest = get_full_account()

        modify_account(event, payload, src)

        if event != 'message':
            dest = None

        t1 = time.time()
        logger.add_event(event, payload, src, dest)

        if event == 'message':
            print time.time() - t1, event, 'from', src, 'to', dest, ':', payload
        else:
            print time.time() - t1, event, 'from', src, ':', payload

if __name__ == '__main__':
    test()
