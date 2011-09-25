'''base implementation of a login'''
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

import extension
import e3
import gui

import logging
log = logging.getLogger('gui.base.Conversation')

class LoginBase(object):
    '''a widget that contains all the components inside'''

    def __init__(self, config, config_dir, config_path, proxy=None,
                use_http=None, session_id=None, no_autologin=False):
        '''constructor'''
        self.config = config
        self.config_dir = config_dir
        self.config_path = config_path
        self.no_autologin = no_autologin
        # the id of the default extension that handles the session
        # used to select the default session on the preference dialog
        self.use_http = use_http
        self.session_id = session_id
        self.proxy = proxy or e3.Proxy()
        self.server_host = None
        self.server_port = None

        self.config.get_or_set('service', 'msn')
        self.remembers = self.config.get_or_set('d_remembers', {})
        self.config.get_or_set('d_user_service', {})
        self.status = self.config.get_or_set('d_status', {})
        account = self.config.get_or_set('last_logged_account', '')
        self._setup_account(account)

        self.services = {}
        self.service2id = {}
        self._setup_services(session_id)

    def _setup_account(self, account):
        #convert old configs to the new format
        if len(account.split('|')) == 1:
            config_keys = self.config.d_remembers.keys()
            for _account in config_keys:
                if len(_account.split('|')) != 1:
                    continue
                account_and_service = \
                    _account + '|' + \
                    self.config.d_user_service.get(_account, 'msn')
                if _account == account:
                    self.config.last_logged_account = account_and_service
                    account = account_and_service
                self.config.d_remembers[account_and_service] = \
                    self.config.d_remembers.get(_account)
                self.config.d_remembers.pop(_account, None)
                self.config.d_status[account_and_service] = \
                    self.config.d_status.get(_account)
                self.config.d_status.pop(_account, None)
                _value = self.config.d_accounts.get(_account)
                if _value:
                    self.config.d_accounts[account_and_service] = _value
                self.config.d_accounts.pop(_account, None)
            self.remembers = self.config.d_remembers
            self.status = self.config.d_status
        self.accounts = self.config.d_accounts

    def _setup_services(self, session_id):
        if session_id is not None:
            for ext_id, ext in extension.get_extensions('session').iteritems():
                for service_name, service_data in ext.SERVICES.iteritems():
                    self.services[service_name] = service_data
                    self.service2id[service_name] = ext_id

                if session_id == ext_id and self.config.service in ext.SERVICES:
                    self.server_host = ext.SERVICES[self.config.service]['host']
                    self.server_port = ext.SERVICES[self.config.service]['port']
                    break
            else:
                self.config.service = 'msn'
                self.server_host = 'messenger.hotmail.com'
                self.server_port = '1863'
        else:
            self.config.service = 'msn'
            self.server_host = 'messenger.hotmail.com'
            self.server_port = '1863'
