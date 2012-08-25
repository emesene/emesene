# -*- coding: utf-8 -*-

#    This file is part of emesene.
#
#    emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    emesene is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with emesene; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os
import csv
import json
import time
import Queue
import shutil
import threading
import sqlite3.dbapi2 as sqlite

import status as pstatus

import logging
log = logging.getLogger('e3.base.Logger')  # oh snap!

import e3

class Account(object):
    '''a class to store account data'''

    def __init__(self, id_, id_account, account, status, nick='', message='',
        path='', cid=None):
        '''constructor'''
        self.id = id_
        self.id_account = id_account
        self.account = account
        self.status = status
        self.nick = nick
        self.message = message
        self.path = path
        self.cid = cid
        self.groups = []

    def equals(self, id_account, account, nick, message, path):
        '''return True if all the fields except the id and the status are
        equals
        '''
        if self.id_account == id_account and self.account == account and \
            self.nick == nick and self.message == message and self.path == path:
            return True

    def __str__(self):
        '''return a string representation of the object'''
        return "<account '%s'>" % (self.account,)

    @classmethod
    def from_contact(cls, contact):
        '''Creates a Account object from a Contact'''
        return cls(contact.cid, None, contact.account,
            contact.status, contact.nick, contact.message, contact.picture)


class Group(object):
    '''a class that represents a group of contacts'''

    def __init__(self, id_, name, gid, enabled):
        '''constructor'''
        self.id = id_
        self.name = name
        self.gid = gid
        self.enabled = enabled
        self.accounts = []

    def __str__(self):
        '''return a string representation of the object'''
        return "<group '%s'>" % (self.name,)


class Logger(object):
    '''a class to log activity on an IM'''

    COMMIT_LIMIT = 20

    EVENTS = ('nick change', 'status change', 'message change', 'image change',
        'message', 'message-error')

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

    CREATE_D_INFO = '''
        CREATE TABLE d_info
        (
          id_info INTEGER PRIMARY KEY,
          id_account INTEGER,
          nick TEXT,
          message TEXT,
          path TEXT
        );
    '''

    CREATE_D_ACCOUNT = '''
        CREATE TABLE d_account
        (
          id_account INTEGER PRIMARY KEY,
          account TEXT,
          cid TEXT,
          enabled INTEGER
        );
    '''

    # not a dimension used as cache
    CREATE_GROUP = '''
        CREATE TABLE t_group
        (
          id_group INTEGER PRIMARY KEY,
          name TEXT,
          gid TEXT,
          enabled INTEGER
        );
    '''

    # not a dimension used as cache
    CREATE_ACCOUNT_BY_GROUP = '''
        CREATE TABLE account_by_group
        (
          id_group INTEGER,
          id_account INTEGER,
          PRIMARY KEY(id_group, id_account)
        );
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
          id_time INTEGER,
          id_event INTEGER,
          id_src_info INTEGER,
          id_dest_info INTEGER,
          id_src_acc INTEGER,
          id_dest_acc INTEGER,
          cid INTEGER,

          status INTEGER,
          payload TEXT,
          tmstp FLOAT
        );
    '''

    CREATE_LAST_ACCOUNT = '''
        CREATE TABLE last_account
        (
          id_info INTEGER,
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

    INSERT_INFO = '''
        INSERT INTO d_info(id_info, id_account, nick, message, path)
        VALUES(NULL, ?, ?, ?, ?);
    '''

    INSERT_ACCOUNT = '''
        INSERT INTO d_account(id_account, account, cid, enabled)
        VALUES(NULL, ?, ?, ?);
    '''

    INSERT_GROUP = '''
        INSERT INTO t_group(id_group, name, gid, enabled) VALUES(NULL, ?, ?, ?);
    '''

    INSERT_EVENT = '''
        INSERT INTO d_event(id_event, name) VALUES(NULL, ?);
    '''

    INSERT_FACT_EVENT = '''
        INSERT INTO fact_event(id_time, id_event, id_src_info, id_dest_info,
            id_src_acc, id_dest_acc, status, payload, tmstp, cid)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    '''

    INSERT_LAST_ACCOUNT = '''
        INSERT INTO last_account(id_info, id_account, account, status, nick,
            message, path)
        VALUES(?, ?, ?, ?, ?, ?, ?);
    '''

    INSERT_ACCOUNT_BY_GROUP = '''
        INSERT INTO account_by_group(id_account, id_group)
        VALUES(?, ?);
    '''

    UPDATE_LAST_ACCOUNT = '''
        UPDATE last_account SET id_info=?, id_account=?, status=?, nick=?,
            message=?, path=?
        WHERE account=?;
    '''

    UPDATE_ACCOUNT = '''
        UPDATE d_account SET enabled=? WHERE id_account=?;
    '''

    UPDATE_GROUP = '''
        UPDATE t_group SET name=?, enabled=? WHERE id_group=?;
    '''

    SELECT_LAST_ACCOUNTS = '''
        SELECT id_info, id_account, account, status, nick, message, path
        FROM last_account
    '''

    SELECT_EVENTS = '''
        SELECT id_event, name FROM d_event;
    '''

    SELECT_GROUPS = '''
        SELECT id_group, name, gid, enabled from t_group;
    '''

    SELECT_ACCOUNT_EVENT = '''
        SELECT status, tmstp, payload from fact_event
        WHERE id_event=? and id_src_acc=?
        ORDER BY tmstp DESC LIMIT ?;
    '''

    SELECT_ACCOUNT_BY_GROUP = '''
        SELECT a.cid, a.account, g.gid
        FROM d_account a, t_group g, account_by_group b
        WHERE a.id_account = b.id_account AND
          g.id_group = b.id_group;
    '''

    DELETE_ACCOUNT_BY_GROUP = '''
        DELETE FROM account_by_group
        WHERE id_account=? AND id_group=?
    '''

    SELECT_SENT_MESSAGES = '''
        SELECT f.tmstp, f.payload
        FROM fact_event f
        WHERE f.id_event=? and f.id_src_acc=? and
            id_dest_acc=?
        ORDER BY tmstp DESC LIMIT ?;
    '''

    SELECT_CHATS = '''
        SELECT f.status, f.tmstp, f.payload, i.nick, a.account
        FROM fact_event f, d_info i, d_account a
        WHERE f.id_event=? and
            ((f.id_src_acc=? and id_dest_acc=?) or
            (f.id_dest_acc=? and id_src_acc=?)) and
            f.id_src_info = i.id_info and f.id_src_acc = a.id_account
        ORDER BY tmstp DESC LIMIT ?;
    '''

    SELECT_CHATS_BETWEEN = '''
        SELECT f.status, f.tmstp, f.payload, i.nick, a.account
        FROM fact_event f, d_info i, d_account a
        WHERE f.id_event=? and
            ((f.id_src_acc=? and id_dest_acc=?) or
            (f.id_dest_acc=? and id_src_acc=?)  or
            (f.id_src_acc<>? and f.cid in
                ( SELECT f.cid FROM fact_event f
                  WHERE f.id_event=?  and  ((f.id_src_acc=? and id_dest_acc=?)
                  or  (f.id_dest_acc=? and id_src_acc=?)) )
            )) and
            f.id_src_info = i.id_info and
            f.tmstp >= ? and f.tmstp <= ? and f.id_src_acc = a.id_account
        ORDER BY tmstp DESC LIMIT ?;
    '''

    SELECT_CHATS_KEYWORDS = '''
        SELECT f.status, f.tmstp, f.payload, i.nick, a.account
        FROM fact_event f, d_info i, d_account a
        WHERE f.id_event=? and
            ((f.id_src_acc=? and id_dest_acc=?) or
            (f.id_dest_acc=? and id_src_acc=?)  or
            (f.id_src_acc<>? and f.cid in
                ( SELECT f.cid FROM fact_event f
                  WHERE f.id_event=?  and  ((f.id_src_acc=? and id_dest_acc=?)
                  or  (f.id_dest_acc=? and id_src_acc=?)) )
            )) and
            f.id_src_info = i.id_info and
            f.payload like ? and
            f.tmstp >= ? and f.tmstp <= ? and f.id_src_acc = a.id_account
        ORDER BY tmstp DESC LIMIT ?;
    '''

    SELECT_NEW_FIELDS = '''
        SELECT cid FROM fact_event;
    '''

    DROP_FACT_EVENT = '''
        DROP TABLE fact_event;
    '''

    DROP_D_TIME = '''
        DROP TABLE d_time;
    '''

    def __init__(self, path, db_name="base.db"):
        '''constructor'''
        self.path = path
        self.db_name = db_name

        self.events = {}
        self.groups = {}
        self.accounts = {}

        full_path = os.path.join(path, db_name)

        if os.path.exists(full_path + "copy"):
            shutil.copy(full_path + "copy", full_path)

        self.connection = sqlite.connect(full_path)
        self.cursor = self.connection.cursor()

        if self.__need_clean():
            self.__clean()

        self.connection = sqlite.connect(full_path)
        self.cursor = self.connection.cursor()

        self._count = 0

        try:
            self._create()
        except sqlite.OperationalError:
            self._load_events()
            self._load_groups()
            self._load_accounts()
            self._load_account_by_group()

    def _create(self):
        '''create the database'''
        self.execute(Logger.CREATE_D_TIME)
        self.execute(Logger.CREATE_FACT_EVENT)
        self.execute(Logger.CREATE_D_INFO)
        self.execute(Logger.CREATE_D_EVENT)
        self.execute(Logger.CREATE_D_ACCOUNT)
        self.execute(Logger.CREATE_GROUP)
        self.execute(Logger.CREATE_ACCOUNT_BY_GROUP)
        self.execute(Logger.CREATE_LAST_ACCOUNT)

        for event in Logger.EVENTS:
            id_event = self.insert_event(event)
            self.events[event] = id_event

    def _load_accounts(self):
        '''load the accounts from the last_account table and store them in
        a dict'''
        self.execute(Logger.SELECT_LAST_ACCOUNTS)

        for (id_info, id_account, account, status, nick, message, path) in \
                self.cursor.fetchall():
            self.accounts[account] = Account(id_info, id_account, account,
                status, nick, message, path)

    def _load_events(self):
        '''load the events from the d_event table and store them in a dict'''
        self.execute(Logger.SELECT_EVENTS)

        for (id_event, event) in self.cursor.fetchall():
            self.events[event] = id_event

    def _load_account_by_group(self):
        '''load the groups from the d_event table and store them in a dict'''
        self.execute(Logger.SELECT_ACCOUNT_BY_GROUP)

        for (cid, account, gid) in self.cursor.fetchall():
            if gid in self.groups:
                self.groups[gid].accounts.append(account)
            else:
                log.debug(gid + ' not in self.groups')

            if account in self.accounts:
                self.accounts[account].groups.append(gid)
                self.accounts[account].cid = cid
            else:
                log.debug(account + ' not in self.accounts')

    def _load_groups(self):
        '''load the groups from the d_event table and store them in a dict'''
        self.execute(Logger.SELECT_GROUPS)

        for (id_, name, gid, enabled) in self.cursor.fetchall():
            self.groups[gid] = Group(id_, name, gid, enabled)

    def insert_time(self, year, month, day, wday, hour, minute, seconds):
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

    def insert_info(self, account, cid, status, nick, message, path):
        '''insert a row into the d_account table, returns the id'''

        exists = False

        if account in self.accounts:
            exists = True
            acc = self.accounts[account]

            if acc.equals(acc.id_account, account, nick, message, path) and \
                acc.id_account:
                return (acc.id, acc.id_account)

        id_account = self.insert_account(account, cid, True)

        self.execute(Logger.INSERT_INFO,
            (id_account, unicode(nick), unicode(message), unicode(path)))

        id_info = self.cursor.lastrowid
        self.accounts[account] = Account(id_info, id_account, account,
            status, nick, message, path)

        if exists:
            self.update_last_account(id_info, id_account, account, status,
                nick, message, path)
        else:
            self.insert_last_account(id_info, id_account, account, status,
                nick, message, path)

        self._stat()

        return (id_info, id_account)

    def insert_account(self, account, cid, enabled=True):
        '''insert a row into the d_event table, returns the id'''
        if account in self.accounts and self.accounts[account].id_account:
            return self.accounts[account].id_account

        self.execute(Logger.INSERT_ACCOUNT, (unicode(account), unicode(cid),
            int(enabled)))
        id_account = self.cursor.lastrowid

        self.accounts[account] = Account(0, id_account, account,
            0, account, '', '')

        self._stat()

        return id_account

    def insert_group(self, name, gid, enabled=True):
        '''insert a row into the t_group table, returns the id'''
        if gid in self.groups and self.groups[gid].id:
            return self.groups[gid].id

        self.execute(Logger.INSERT_GROUP, (unicode(name), unicode(gid),
            int(enabled)))
        id_ = self.cursor.lastrowid

        self.groups[gid] = Group(id_, name, gid, enabled)

        self._stat()

        return id_

    def insert_event(self, name):
        '''insert a row into the d_event table, returns the id'''
        if name in self.events:
            return self.events[name]

        self.execute(Logger.INSERT_EVENT, (unicode(name),))
        id_event = self.cursor.lastrowid

        self.events[name] = id_event

        self._stat()

        return id_event

    def insert_fact_event(self, id_time, id_event, id_src_info, id_dest_info,
            id_src_acc, id_dest_acc, status, payload, timestamp, cid):
        '''insert a row into the fact_event table, returns the id'''
        self.execute(Logger.INSERT_FACT_EVENT,
            (id_time, id_event, id_src_info, id_dest_info, id_src_acc,
                id_dest_acc, status, unicode(payload), timestamp, cid))

        self._stat()

        return self.cursor.lastrowid

    def insert_last_account(self, id_info, id_account, account, status, nick,
        message, path):
        '''insert a row into the d_account table, returns the id'''
        self.execute(Logger.INSERT_LAST_ACCOUNT,
            (id_info, id_account, unicode(account), status, unicode(nick),
                unicode(message), unicode(path)))

        self._stat()

    def update_last_account(self, id_info, id_account, account, status, nick,
        message, path):
        '''update a row into the last_account table'''
        self.execute(Logger.UPDATE_LAST_ACCOUNT,
            (id_info, id_account, status, unicode(nick), unicode(message),
                unicode(path), unicode(account)))

        self._stat()

    def update_group(self, id_, name, enabled=True):
        '''update a group based on the id, the gid is never updated'''
        self.execute(Logger.UPDATE_GROUP, (unicode(name), int(enabled), id_))

        self._stat()

    def update_account(self, id_, enabled=True):
        '''update a group based on the id, the gid is never updated'''
        self.execute(Logger.UPDATE_ACCOUNT, (int(enabled), id_))

        self._stat()

    def insert_account_by_group(self, id_account, id_group):
        '''insert the relation between an account and a group'''
        try:
            self.execute(Logger.INSERT_ACCOUNT_BY_GROUP,
                         (id_account, id_group))
        except sqlite.IntegrityError, e:
            log.error(str(e))

        self._stat()

    def delete_account_by_group(self, id_account, id_group):
        '''delete the relation between an account and a group'''
        self.execute(Logger.DELETE_ACCOUNT_BY_GROUP, (id_account, id_group))

        self._stat()

    def _stat(self):
        '''called internally each time a transaction is made, here we control
        how often a commit is made'''

        if self._count >= Logger.COMMIT_LIMIT:
            t1 = time.time()
            self.connection.commit()
            #log.info('commit ' + str(time.time() - t1))
            self._count = 0

        self._count += 1

    def _fetch_sorted(self):
        '''puts list from the query in the right order'''
        query_list = self.cursor.fetchall()
        query_list.reverse()

        return query_list

    def execute(self, query, args=()):
        '''execute the query with optional args'''
        self.cursor.execute(query, args)

    # utility methods

    def add_event(self, event, status, payload, src, dest=None, ext_time=None,
            id_time=None, cid=0):
        '''
        add an event on the fact and the dimensiones using
        the actual time
        '''

        id_event = self.insert_event(event)
        (id_src_info, id_src_acc) = self.insert_info(src.account, src.id,
            src.status, src.nick, src.message, src.path)

        if dest:
            (id_dest_info, id_dest_acc) = self.insert_info(dest.account,
                dest.id, dest.status, dest.nick, dest.message, dest.path)
        else:
            id_dest_info = None
            id_dest_acc = None

        if id_time is None:
            if ext_time:
                (year, month, day, hour, minute, seconds, wday, yday,
                 tm_isdst) = time.gmtime(ext_time)
                id_time = self.insert_time(year, month, day, wday,
                                           hour, minute, seconds)
            else:
                id_time = self.insert_time_now()

        timestamp = ext_time if ext_time else time.time()

        self.insert_fact_event(id_time, id_event, id_src_info, id_dest_info,
            id_src_acc, id_dest_acc, status, payload, timestamp, cid)
        self._stat()
        return id_time

    def close(self):
        '''call this method when you are closing the app'''
        self.connection.commit()
        self.cursor.close()
        self.connection.close()

    def get_event(self, account, event, limit):
        '''return the last # events of account, if event or account doesnt
        exist return None'''

        if account not in self.accounts:
            return None
        else:
            id_account = self.accounts[account].id_account

        id_event = self.events.get(event, None)

        if id_event is None:
            return None

        self.execute(Logger.SELECT_ACCOUNT_EVENT,
                     (id_event, id_account, limit))

        return self._fetch_sorted()

    def get_nicks(self, account, limit):
        '''return the last # nicks from account, where # is the limit value'''
        return self.get_event(account, 'nick change', limit)

    def get_messages(self, account, limit):
        '''return the last # messages from account, where # is the limit value
        '''
        return self.get_event(account, 'message change', limit)

    def get_status(self, account, limit):
        '''return the last # status from account, where # is the limit value
        '''
        return self.get_event(account, 'status change', limit)

    def get_images(self, account, limit):
        '''return the last # images from account, where # is the limit value
        '''
        return self.get_event(account, 'image change', limit)

    def get_sent_messages(self, src, dest, limit):
        '''return the last # sent from src to dest , where # is the limit value
        '''
        id_event = self.events.get('message', None)

        if src not in self.accounts or dest not in self.accounts:
            return None

        id_src = self.accounts[src].id_account
        id_dest = self.accounts[dest].id_account

        self.execute(Logger.SELECT_SENT_MESSAGES, (id_event, id_src, id_dest,
            limit))

        return self._fetch_sorted()

    def get_chats(self, src, dest, limit):
        '''return the last # sent from src to dest or from dest to src ,
        where # is the limit value
        '''
        id_event = self.events.get('message', None)

        if src not in self.accounts or dest not in self.accounts:
            return None

        id_src = self.accounts[src].id_account
        id_dest = self.accounts[dest].id_account

        self.execute(Logger.SELECT_CHATS, (id_event, id_src, id_dest, id_src,
            id_dest, limit))

        return self._fetch_sorted()

    def get_chats_between(self, src, dest, from_t, to_t, limit):
        '''return the last # sent from src to dest or from dest to src ,
        where # is the limit value
        '''
        id_event = self.events.get('message', None)

        if src not in self.accounts or dest not in self.accounts:
            return None

        id_src = self.accounts[src].id_account
        id_dest = self.accounts[dest].id_account

        self.execute(Logger.SELECT_CHATS_BETWEEN,
                     (id_event, id_src, id_dest, id_src, id_dest, id_dest,
                      id_event, id_src, id_dest, id_src, id_dest,
                      from_t, to_t, limit))

        return self._fetch_sorted()

    def get_chats_by_keyword(self, src, dest, from_t, to_t, keywords, limit):
        '''return the last # messages containing keywords sent from src to dest
        or from dest to src, where # is the limit value
        '''
        id_event = self.events.get('message', None)

        if src not in self.accounts or dest not in self.accounts:
            return None

        id_src = self.accounts[src].id_account
        id_dest = self.accounts[dest].id_account

        #FIXME: escape keywords??
        keywords = "%" + unicode(keywords, 'utf8') + "%"

        self.execute(Logger.SELECT_CHATS_KEYWORDS,
                     (id_event, id_src, id_dest, id_src, id_dest, id_dest,
                      id_event, id_src, id_dest, id_src, id_dest,
                      keywords, from_t, to_t, limit))

        return self._fetch_sorted()

    def add_groups(self, groups):
        '''add all groups to the database'''
        existing = set(self.groups.keys())
        to_include = set(groups.keys())
        new_groups = to_include.difference(existing)
        common = existing.intersection(to_include)
        removed = existing.difference(to_include)

        for gid in new_groups:
            group = groups[gid]
            self.insert_group(group.name, gid)

        for gid in removed:
            group = self.groups[gid]
            self.update_group(group.id, group.name, False)

    def add_contacts(self, accounts):
        '''add all contacts to the database'''
        existing = set(self.accounts.keys())
        to_include = set(accounts.keys())
        new_accounts = to_include.difference(existing)
        common = existing.intersection(to_include)
        removed = existing.difference(to_include)

        for acc in new_accounts:
            account = accounts[acc]
            cid = account.cid
            self.insert_info(acc, cid, pstatus.OFFLINE, '', '', '')

        for acc in removed:
            account = self.accounts[acc]
            self.update_account(account.id, False)

    def __clean(self):
        try:
            self.execute(Logger.DROP_FACT_EVENT)
            self.execute(Logger.DROP_D_TIME)
        except sqlite.OperationalError:
            pass

    def __need_clean(self):
        try:
            self.execute(Logger.SELECT_NEW_FIELDS)
            return False
        except sqlite.OperationalError:
            return True

    def add_contact_by_group(self, accounts, groups):
        '''add all the contacts, all the groups and the relations, also
        mark as disabled the accounts and groups that were removed and
        remove the accounts from groups of relations that were removed'''
        self.add_contacts(accounts)
        self.add_groups(groups)

        for (cid, account) in accounts.iteritems():
            local_account = self.accounts.get(account.account, None)

            if local_account is None:
                log.debug(account.account + ' not found in self.accounts')
                continue

            existing = set(local_account.groups)
            to_include = set(account.groups)
            new_groups = to_include.difference(existing)
            removed = existing.difference(to_include)

            for gid in new_groups:
                local_group = self.groups[gid]

                if gid not in local_account.groups:
                    self.insert_account_by_group(local_account.id_account,
                                                 local_group.id)

            for gid in removed:
                local_group = self.groups[gid]
                local_account.groups.remove(gid)
                self.delete_account_by_group(local_account.id_account,
                                             local_group.id)


class LoggerOutputProcess(threading.Thread):
    '''a process that processes the output calls from the logger thread'''

    def __init__(self):
        '''constructor'''
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.output = Queue.Queue()
        self._close = False

    def run(self):
        '''main method'''
        while True:
            if self._close:
                return

            try:
                action, result, callback = self.output.get(True)
                callback(result)
            except Queue.Empty:
                pass

    def close(self):
        self._close = True

    def put(self, *args):
        self.output.put(*args)


class LoggerProcess(threading.Thread):
    '''a process that exposes a thread safe api to log events of a session'''

    def __init__(self, path, db_name="base.db"):
        '''constructor'''
        threading.Thread.__init__(self)
        self.setDaemon(True)

        self.path = path
        self.db_name = db_name
        self.logger = None
        self.input = Queue.Queue()
        self.output = LoggerOutputProcess()

        self.actions = {}

    def run(self):
        '''main method'''
        data = None
        self.logger = Logger(self.path, self.db_name)
        self.output.start()

        self.actions['get_event'] = self.logger.get_event
        self.actions['get_nicks'] = self.logger.get_nicks
        self.actions['get_messages'] = self.logger.get_messages
        self.actions['get_status'] = self.logger.get_status
        self.actions['get_images'] = self.logger.get_images
        self.actions['get_sent_messages'] = self.logger.get_sent_messages
        self.actions['get_chats'] = self.logger.get_chats
        self.actions['get_chats_between'] = self.logger.get_chats_between
        self.actions['get_chats_by_keyword'] = self.logger.get_chats_by_keyword
        self.actions['add_groups'] = self.logger.add_groups
        self.actions['add_contacts'] = self.logger.add_contacts
        self.actions['add_contact_by_group'] = self.logger.add_contact_by_group

        while True:
            try:
                data = self.input.get(True)
                quit = self._process(data)

                if quit:
                    self.output.close()
                    self.logger.close()
                    return
            except Queue.Empty:
                pass

    def _process(self, data):
        '''process the received data'''
        action, args = data
        cid = 0

        if action == 'log':
            try:
                event, status, payload, src, dest, new_time, cid = args
            except:
                event, status, payload, src, dest, new_time = args
            self.logger.add_event(event, status, payload, src, dest, new_time,
                                  cid=cid)
        elif action == 'logs':
            id_time = None

            for event, status, payload, src, dest, cid in args:
                id_time = self.logger.add_event(event, status, payload, src,
                        dest, None, id_time, cid = cid)

        elif action == 'quit':
            return True
        elif action in self.actions:
            try:
                f_args = args[:-1]
                callback = args[-1]
                result = self.actions[action](*f_args)

                if callback:
                    self.output.put((action, result, callback))
            except Exception, e:
                log.error('error calling action %s on LoggerProcess: %s' %
                    (action, e))
        else:
            log.error('invalid action %s on LoggerProcess' % (action,))

        return False


    @property
    def input_size(self):
        return self.input.qsize()

    def log(self, event, status, payload, src, dest=None, new_time=None,
            cid=None):
        '''add an event to the log database'''
        self.input.put(('log', (event, status, payload, src, dest, new_time,
                                cid)))

    def logs(self, logs):
        '''add a group of events to the log database with the same time_od'''
        self.input.put(('logs', logs))

    def quit(self):
        '''stop the logger thread, and close the logger'''
        self.input.put(('quit', None))

    def get_event(self, account, event, limit, callback):
        '''return the last # events of account, if event or account doesnt
        exist return None'''
        self.input.put(('get_event', (account, event, limit, callback)))

    def get_nicks(self, account, limit, callback):
        '''return the last # nicks from account, where # is the limit value'''
        self.input.put(('get_nicks', (account, limit, callback)))

    def get_messages(self, account, limit, callback):
        '''return the last # messages from account, where # is the limit value
        '''
        self.input.put(('get_messages', (account, limit, callback)))

    def get_status(self, account, limit, callback):
        '''return the last # status from account, where # is the limit value
        '''
        self.input.put(('get_status', (account, limit, callback)))

    def get_images(self, account, limit, callback):
        '''return the last # images from account, where # is the limit value
        '''
        self.input.put(('get_images', (account, limit, callback)))

    def get_sent_messages(self, src, dest, limit, callback):
        '''return the last # sent from src to dest , where # is the limit value
        '''
        self.input.put(('get_sent_messages', (src, dest, limit, callback)))

    def get_chats(self, src, dest, limit, callback):
        '''return the last # sent from src to dest or from dest to src ,
        where # is the limit value
        '''
        self.input.put(('get_chats', (src, dest, limit, callback)))

    def get_chats_between(self, src, dest, from_t, to_t, limit, callback):
        '''return the last # sent from src to dest or from dest to src ,
        between two timestamps from_t and to_t, where # is the limit value
        '''
        self.input.put(('get_chats_between', (src, dest, from_t, to_t, limit,
                                              callback)))

    def get_chats_by_keyword(self, src, dest, from_t,
                             to_t, keywords, limit, callback):
        '''return the last # sent from src to dest or from dest to src ,
        between two timestamps from_t and to_t, containing keywords,
        where # is the limit value
        '''
        self.input.put(('get_chats_by_keyword', (src, dest, from_t, to_t,
                                                 keywords, limit, callback)))

    def add_groups(self, groups):
        '''add all groups to the database'''
        self.input.put(('add_groups', (groups, None)))

    def add_contacts(self, contacts):
        '''add all contacts to the database'''
        self.input.put(('add_contacts', (contacts, None)))

    def add_contact_by_group(self, contacts, groups):
        '''add all contacts, groups and relations to the database'''
        self.input.put(('add_contact_by_group', (contacts, groups, None)))

class ExporterCsv():
    NAME = 'Exporter CSV'
    DESCRIPTION = 'export logs as csv'
    AUTHOR = 'marianoguerra'
    WEBSITE = 'www.emesene.org'

    @classmethod
    def export(cls, results, handle):
        '''save the chats in results (from get_chats or get_chats_between) as
        csv to handle (file like object)

        the caller is responsible of closing the handle
        '''

        writer = csv.writer(handle)
        for stat, timestamp, message, nick, account in results:
            date_text = time.strftime('%c', time.gmtime(timestamp))
            writer.writerow((date_text, nick, message, account, stat, timestamp))

class ExporterJSON():
    NAME = 'Exporter JSON'
    DESCRIPTION = 'export logs as json'
    AUTHOR = 'marianoguerra'
    WEBSITE = 'www.emesene.org'

    @classmethod
    def export(cls, results, handle):
        '''save the chats in results (from get_chats or get_chats_between) as
        json to handle (file like object)

        the caller is responsible of closing the handle
        '''

        convs = []

        for stat, timestamp, message, nick, account in results:
            convs.append({
                "nick": nick,
                "message": message,
                "account": account,
                "stat": stat,
                "timestamp": timestamp
            })

        json.dump(convs, handle)

class ExporterHtml():
    NAME = 'Exporter Html'
    DESCRIPTION = 'export logs as html'
    AUTHOR = 'marianoguerra'
    WEBSITE = 'www.emesene.org'

    BASE_STYLE = """
html, body, div, span{
 margin: 0;
 padding: 0;
}

body{
 color: #333333;
 font-family: "Helvetica Neue",Helvetica,Arial,sans-serif;
 font-size: 14px;
 line-height: 20px;
}

.message{
 width: 78%;
 margin-left: 10%;
 margin-top: 1em;
 padding: 1%;
 border-radius: 4px;
}

.header, .body, .footer{
 width: 98%;
}

.header{
 font-size: small;
}

.footer{
 font-size: x-small;
 text-align: right;
 color: #555;
}

.nick{
 font-weight: bold;
}

.account{
 font-size: small;
 color: #555;
 float: right;
}
"""

    @classmethod
    def make_base_page(cls):
        '''return the basic page structure and the tag where you have to
        add the conversation'''
        html = e3.common.html

        convs = html.Div(class_="conversations")
        head = html.Head(html.Title("conversations"))

        page = html.Html(head, html.Body(convs))

        return page, head, convs

    @classmethod
    def make_message(cls, stat, timestamp, message, nick, account):
        html = e3.common.html

        div = html.Div
        span = html.Span
        date_text = time.strftime('[%c]', time.gmtime(timestamp))
        account_class = "account-" + str(hash(account))

        return div(
                div(
                    span(nick, class_="nick"),
                    span(account, class_="account"),
                    class_="header"),
                div(message, class_="body"),
                div(span(date_text, class_="date"), class_="footer"),

                class_="message " + account_class)


    @classmethod
    def export(cls, results, handle):
        '''save the chats in results (from get_chats or get_chats_between) as
        html to handle (file like object)

        the caller is responsible of closing the handle
        '''
        html = e3.common.html
        colors = {}

        def gen_color(account):
            hue = hash(account) % 256
            return "hsl(%d, 100%%, 90%%)" % hue

        def color_generator(account):
            color = colors.get(account, None)

            if color is None:
                color = gen_color(account)
                colors[account] = color

            return color

        page, head, body = cls.make_base_page()

        for stat, timestamp, message, nick, account in results:
            color_generator(account)
            body.append(cls.make_message(stat, timestamp, message, nick,
                account))

        styles = []
        for account, color in colors.items():
            account_class = ".account-" + str(hash(account))
            styles.append(account_class + "{background-color:" + color + "}")

        head.append(html.Style(cls.BASE_STYLE))
        head.append(html.Style("\n".join(styles)))

        handle.write(str(page))

class ExporterTxt():
    NAME = 'Exporter Txt'
    DESCRIPTION = 'export logs as simple text'
    AUTHOR = 'emesene team'
    WEBSITE = 'www.emesene.org'

    @staticmethod
    def export(results, handle):
        '''save the chats in results (from get_chats or get_chats_between) as txt
        to handle (file like object)

        the caller is responsible of closing the handle
        '''

        for stat, timestamp, message, nick, account in results:
            date_text = time.strftime('[%c]', time.gmtime(timestamp))
            handle.write("%s %s: %s\n" % (date_text, nick, message))

class ExporterXml():
    NAME = 'Exporter Xml'
    DESCRIPTION = 'export logs as xml data'
    AUTHOR = 'emesene team'
    WEBSITE = 'www.emesene.org'

    @staticmethod
    def export(results, handle):
        '''save the chats in results (from get_chats or get_chats_between) as xml
        to handle (file like object)

        the caller is responsible of closing the handle
        '''
        from xml.dom.minidom import Document

        doc = Document()
        doc.appendChild(doc.createProcessingInstruction("xml-stylesheet",
                                "type=\"text/css\" href=\"conversation.css\""))
        conversation = doc.createElement("conversation")
        doc.appendChild(conversation)

        for stat, timestamp, message, nick, account in results:

            timestamp_tag = doc.createElement("timestamp")
            date_text = time.strftime('[%c]', time.gmtime(timestamp))
            timestamp_text = doc.createTextNode(date_text)
            timestamp_tag.appendChild(timestamp_text)

            nick_tag = doc.createElement("nick")
            nick_text = doc.createTextNode(nick)
            nick_tag.appendChild(nick_text)
            timestamp_tag.appendChild(nick_tag)

            status_tag = doc.createElement("status")
            status_text = doc.createTextNode(str(stat))
            status_tag.appendChild(status_text)
            timestamp_tag.appendChild(status_tag)

            account_tag = doc.createElement("account")
            account_text = doc.createTextNode(account)
            account_tag.appendChild(account_text)
            timestamp_tag.appendChild(account_tag)

            message_tag = doc.createElement("message")
            message_text = doc.createTextNode(message)
            message_tag.appendChild(message_text)
            timestamp_tag.appendChild(message_tag)

            conversation.appendChild(timestamp_tag)

        handle.write(doc.toprettyxml(indent="  ",  encoding="UTF-8"))


def log_message(session, members, message, sent, error=False, cid=None):
    '''log a message, session is an e3.Session object, members is a list of
    members only used if sent is True, sent is True if we sent the message,
    False if we received the message. error is True if the message send
    failed'''

    if not session.config.get_or_set('b_log_enabled', True):
        return

    if message.type == e3.Message.TYPE_TYPING:
        return

    if error:
        event = 'message-error'
    else:
        event = 'message'

    if sent:
        contact = session.contacts.me
        status = contact.status
        src = e3.Logger.Account.from_contact(session.contacts.me)

        if message.type == e3.Message.TYPE_NUDGE:
            message.body = _("You just sent a nudge!")

        logs = []

        if len(members) == 1:
            member = members[0]
            dst = session.contacts.safe_get(members[0])

            dest = e3.Logger.Account.from_contact(dst)

            logs.append((event, status, message.body, src, dest, cid))

            session.logger.logs(logs)
        else:

            for dst_account in members:
                dst = session.contacts.safe_get(dst_account)

                dest = e3.Logger.Account.from_contact(dst)
                logs.append((event, status, message.body, src, dest, cid))

            session.logger.logs(logs)
    else:
        dest = e3.Logger.Account.from_contact(session.contacts.me)
        contact = session.contacts.get(message.account)

        if contact is None:
            src = e3.Contact(message.account)
            status = e3.status.OFFLINE
            display_name = message.account
        else:
            src = e3.Logger.Account.from_contact(contact)
            status = contact.status
            display_name = contact.display_name

        if message.type == e3.Message.TYPE_NUDGE:
            message.body = _("%s just sent you a nudge!" % display_name)

        session.log(event, status, message.body, src, dest, cid=cid)
