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
                use_http=None, session_id=None):
        '''constructor'''
        self.config = config
        self.config_dir = config_dir
        self.config_path = config_path
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
        self.config.get_or_set('last_logged_account', '')

        self.services = {}
        self.service2id = {}
        self._setup_services(session_id)

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
