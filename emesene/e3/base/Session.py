# -*- coding: utf-8 -*-
'''a module that defines a session object'''

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
import time
import Queue

from Worker import EVENTS
from Event import Event
from Action import Action

import e3
import Logger
from ContactManager import ContactManager

class Session(object):
    NAME = 'Base session'
    DESCRIPTION = '''This is a base session implementation,
    other classes inherit from this one'''
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, id_=None, account=None):
        self.id_ = id_

        if self.id_ is None:
            self.id_ = time.time()

        self._account = None
        self.contacts = None
        self.logger = None
        self.conversations = None
        self.extras = {}

        self.events = Queue.Queue()
        self.actions = Queue.Queue()

        if account is not None:
            self.account = account

        self.groups = {}

        self.config = e3.common.Config()
        self.config_dir = e3.common.ConfigDir('emesene2')
        # set the base dir of the config to the base dir plus the account
        self.signals = e3.common.Signals(EVENTS, self.events)

    def _set_account(self, account):
        '''set the value of account'''
        self._account = account
        self.contacts = ContactManager(self._account.account)

        self.config_dir.base_dir = os.path.join(
            self.config_dir.base_dir, self._account.service, self._account.account)
        self.config_dir.add_path("config", "config", False)
        self.config_dir.add_path("avatars", "avatars")
        self.config_dir.add_path("cached_avatars", "cached_avatars")
        self.config_dir.add_path("last_avatar", os.path.join("avatars", "last"), False)
        self.config_dir.add_path("log", "log")
        self.logger = Logger.LoggerProcess(self.config_dir.get_path('log'))
        self.logger.start()

    def _get_account(self):
        '''return the value of account'''
        return self._account

    account = property(fset=_set_account, fget=_get_account)

    def add_event(self, id_, *args):
        '''add an event to the events queue'''
        self.events.put(Event(id_, *args))

    def add_action(self, id_, *args):
        '''add an action to the action queue'''
        self.actions.put(Action(id_, *args))

    def save_config(self):
        '''save the config of the session'''
        config_path = self.config_dir.get_path('config')

        if config_path:
            try:
                self.config.save(config_path)
            except:
                print "Error on save configuration"

    def load_config(self):
        '''load the config of the session'''
        # load the global configuration
        self.config.load(os.path.join(self.config_dir.default_base_dir,
            'config'))
        # load the account configuration
        self.config.load(self.config_dir.get_path('config'))

    def new_conversation(self, account, cid):
        '''start a new conversation with account'''
        self.add_action(Action.ACTION_NEW_CONVERSATION, (account, cid))

    def close_conversation(self, cid):
        '''close a conversation identified by cid'''
        self.add_action(Action.ACTION_CLOSE_CONVERSATION, (cid,))

    def conversation_invite(self, cid, account):
        '''invite a contact to aconversation identified by cid'''
        self.add_action(Action.ACTION_CONV_INVITE, (cid, account))

    def quit(self):
        '''close the worker and socket threads'''
        self.add_action(Action.ACTION_QUIT, ())

    def login(self, account, password, status, proxy, host, port, use_http=False):
        '''start the login process'''
        raise NotImplementedError('Not implemented')

    def logout(self):
        '''close the session'''
        self.add_action(Action.ACTION_LOGOUT, ())

    def set_status(self, status):
        '''change the status of the session'''
        self.add_action(Action.ACTION_CHANGE_STATUS, (status,))

    def add_contact(self, account):
        '''add the contact to our contact list'''
        self.add_action(Action.ACTION_ADD_CONTACT, (account,))

    def remove_contact(self, account):
        '''remove the contact from our contact list'''
        self.add_action(Action.ACTION_REMOVE_CONTACT, (account,))

    def reject_contact(self, account):
        '''reject a contact that added us'''
        self.add_action(Action.ACTION_REJECT_CONTACT, (account,))

    def block(self, account):
        '''block the contact'''
        self.add_action(Action.ACTION_BLOCK_CONTACT, (account,))

    def unblock(self, account):
        '''block the contact'''
        self.add_action(Action.ACTION_UNBLOCK_CONTACT, (account,))

    def set_alias(self, account, alias):
        '''set the alias of a contact'''
        self.add_action(Action.ACTION_SET_CONTACT_ALIAS,
            (account, alias))

    def add_to_group(self, account, gid):
        '''add a contact to a group'''
        self.add_action(Action.ACTION_ADD_TO_GROUP, (account, gid))

    def remove_from_group(self, account, gid):
        '''remove a contact from a group'''
        self.add_action(Action.ACTION_REMOVE_FROM_GROUP,
            (account, gid))

    def move_to_group(self, account, src_gid, dest_gid):
        '''remove a contact from the group identified by src_gid and add it
        to dest_gid'''
        self.add_action(Action.ACTION_MOVE_TO_GROUP, (account,
            src_gid, dest_gid))

    def add_group(self, name):
        '''add a group '''
        self.add_action(Action.ACTION_ADD_GROUP, (name,))

    def remove_group(self, gid):
        '''remove the group identified by gid'''
        self.add_action(Action.ACTION_REMOVE_GROUP, (gid,))

    def rename_group(self, gid, name):
        '''rename the group identified by gid with the new name'''
        self.add_action(Action.ACTION_RENAME_GROUP, (gid, name))

    def set_nick(self, nick):
        '''set the nick of the session'''
        self.add_action(Action.ACTION_SET_NICK, (nick,))

    def set_message(self, message):
        '''set the message of the session'''
        self.add_action(Action.ACTION_SET_MESSAGE, (message,))

    def set_media(self, message):
        '''set the message of the session'''
        self.add_action(Action.ACTION_SET_MEDIA, (message,))

    def set_picture(self, picture_name):
        '''set the picture of the session to the picture with picture_name as
        name'''
        self.add_action(Action.ACTION_SET_PICTURE, (picture_name,))

    def set_preferences(self, preferences):
        '''set the preferences of the session to preferences, that is a
        dict containing key:value pairs where the keys are the preference name
        and value is the new value of that preference'''
        self.add_action(Action.ACTION_SET_PREFERENCES, (preferences,))

    def send_message(self, cid, text, style=None):
        '''send a common message'''
        raise NotImplementedError('Not implemented')

    def request_attention(self, cid):
        '''request the attention of the contact'''
        raise NotImplementedError('Not implemented')

    def accept_filetransfer(self, transfer):
        self.add_action(Action.ACTION_FT_ACCEPT, (transfer,))

    def reject_filetransfer(self, transfer):
        self.add_action(Action.ACTION_FT_REJECT, (transfer,))

    def cancel_filetransfer(self, transfer):
        self.add_action(Action.ACTION_FT_CANCEL, (transfer,))

    def accept_call(self, call):
        self.add_action(Action.ACTION_CALL_ACCEPT, (call,))

    def reject_call(self, call):
        self.add_action(Action.ACTION_CALL_REJECT, (call,))

    def cancel_call(self, call):
        self.add_action(Action.ACTION_CALL_CANCEL, (call,))

for event_name in EVENTS:
    fname = event_name.replace(" ", "_")
    ename = "EVENT_%s" % fname.upper()
    event = getattr(Event, ename)

    def make_cb(event):
        '''avoid being bitten by the lambda/closure bug'''
        return lambda self, *args: Session.add_event(self, event, *args)

    if event is None:
        raise Exception("Event %s not found fixme right now" % ename)

    if getattr(Session, fname, None) is not None:
        raise Exception("function collision %s fixme right now" % fname)

    setattr(Session, fname, make_cb(event))

