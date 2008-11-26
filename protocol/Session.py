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

import os
import Queue

from protocol.Event import Event
import ContactManager
import Config
import Logger
import ConfigDir

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

        self.config = Config.Config()
        self.config_dir = ConfigDir.ConfigDir('emesene2')
        # set the base dir of the config to the base dir plus the account


    def _set_account(self, account):
        '''set the value of account'''
        self._account = account
        self.contacts = ContactManager.ContactManager(self._account.account)
        self.config_dir.base_dir = os.path.join(
            self.config_dir.base_dir, self._account.account)
        self.logger = Logger.LoggerProcess(self.config_dir.join('log'))

    def _get_account(self):
        '''return the value of account'''
        return self._account

    account = property(fset=_set_account, fget=_get_account)

    def add_event(self, id_, *args):
        '''add an event to the events queue'''
        self.events.put(Event(id_, *args))

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

