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
import base64

import logging
log = logging.getLogger('gui.base.Conversation')

class LoginBase(object):
    '''a widget that contains all the components inside'''

    def __init__(self, callback, on_preferences_changed, config, config_dir,
                config_path, proxy=None, use_http=None, session_id=None,
                no_autologin=False):
        '''constructor'''

        self.callback = callback
        self.on_preferences_changed = on_preferences_changed
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
                    self.service2id[service_name] = (ext_id, ext)

                if session_id == ext_id and self.config.service in ext.SERVICES:
                    self.server_host = ext.SERVICES[self.config.service]['host']
                    self.server_port = ext.SERVICES[self.config.service]['port']
            else:
                self.config.service = 'msn'
                self.server_host = 'messenger.hotmail.com'
                self.server_port = '1863'
        else:
            self.config.service = 'msn'
            self.server_host = 'messenger.hotmail.com'
            self.server_port = '1863'

    def config_account(self, account, service, remember_account, remember_password,
                         auto_login):
        '''
        modify the config for the current account before login
        '''

        account_and_session = account.account + '|' + service

        if auto_login or remember_account or remember_password:
            self.status[account_and_session] = account.status
            self.config.last_logged_account = account_and_session

        if auto_login:#+1 account,+1 password,+1 autologin =  3
            self.accounts[account_and_session] = base64.b64encode(account.password)
            self.remembers[account_and_session] = 3

        elif remember_password:#+1 account,+1 password = 2
            self.accounts[account_and_session] = base64.b64encode(account.password)
            self.remembers[account_and_session] = 2

        elif remember_account:#+1 account = 1
            self.accounts[account_and_session] = ''
            self.remembers[account_and_session] = 1

        else:#means i have logged with nothing checked
            self.config.last_logged_account = ''

        self.config.save(self.config_path)

    def update_service(self, service):
        '''Update current service if found in service list'''
        if service in self.services:
            service_data = self.services[service]
            self.server_host = service_data['host']
            self.server_port = service_data['port']
            self.config.service = service
            self.session_id = self.service2id[service][0]

    def current_avatar_path(self, email):
        '''return the avatar for the current service'''
        return self.config_dir.join(
                        self.server_host, email,
                        'avatars', 'last')

    def decode_password(self, email):
        '''return password or "" if not found'''
        return base64.b64decode(self.accounts.get(email, ""))
