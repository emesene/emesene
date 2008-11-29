# -*- coding: utf-8 -*-
'''a module that defines a session object'''

#   This file is part of emesene.
#
#    Emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
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

# TODO: move all the MSN specific code to a subclass on e3

import os
import Queue

from protocol.Event import Event
from protocol.Action import Action
import protocol.ContactManager
import protocol.Config
import protocol.Logger
import protocol.ConfigDir

import e3

class Session(object):
    
    def __init__(self, id_, account=None):
        self.id_ = id_
        self._account = None
        self.contacts = None
        self.logger = None
        self.extras = {}

        self.events = Queue.Queue()
        self.actions = Queue.Queue()

        if account is not None:
            self.account = account

        self.groups = {}

        self.config = protocol.Config.Config()
        self.config_dir = protocol.ConfigDir.ConfigDir('emesene2')
        # set the base dir of the config to the base dir plus the account

    def _set_account(self, account):
        '''set the value of account'''
        self._account = account
        self.contacts = protocol.ContactManager(self._account.account)
        self.config_dir.base_dir = os.path.join(
            self.config_dir.base_dir, self._account.account)
        self.logger = protocol.Logger.LoggerProcess(self.config_dir.join('log'))

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
        self.config.save(self.config_dir.join('config'))

    def load_config(self):
        '''load the config of the session'''
        # load the global configuration
        self.config.load(os.path.join(self.config_dir.default_base_dir,
            'config'))
        # load the account configuration
        self.config.load(self.config_dir.join('config'))

    def create_config(self):
        '''create all the dirs and files for configuration'''
        self.config_dir.create('')

    def new_conversation(self, account, cid):
        '''start a new conversation with account'''
        self.add_action(Action.ACTION_NEW_CONVERSATION, (account, cid))

    def close_conversation(self, cid):
        '''close a conversation identified by cid'''
        self.add_action(Action.ACTION_CLOSE_CONVERSATION, (cid,))

    def quit(self):
        '''close the worker and socket threads'''
        self.add_action(Action.ACTION_QUIT, ())

    def login(self, core, account, password, status):
        '''start the login process'''
        socket = e3.MsnSocket('messenger.hotmail.com', 1863, dest_type='NS')
        worker = e3.Worker('emesene2', socket, self, e3.MsnSocket)
        socket.start()
        worker.start()

        self.account = e3.Account(account, password, status)
        # TODO: get rid of core!
        self.protocol = core

        self.add_action(Action.ACTION_LOGIN, 
            (account, password, status))
        
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

    def set_picture(self, picture_name):
        '''set the picture of the session to the picture with picture_name as
        name'''
        self.add_action(Action.ACTION_SET_PICTURE, (picture_name,))
    
    def set_preferences(self, preferences):
        '''set the preferences of the session to preferences, that is a 
        dict containing key:value pairs where the keys are the preference name
        and value is the new value of that preference'''
        self.add_action(Action.ACTION_SET_PREFERENCE, (preferences,))

    def send_message(self, cid, text):
        '''send a common message'''
        account = self.account.account
        message = e3.Message(e3.Message.TYPE_MESSAGE, text, account)
        self.add_action(Action.ACTION_SEND_MESSAGE, (cid, message))

