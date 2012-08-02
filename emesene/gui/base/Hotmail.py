# -*- coding: utf-8 -*-

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
#
#    This file is taken from emesene1 and modified for
#    emesene2 by Andrea Stagi <stagi.andrea(at)gmail.com>

import os
import hashlib
from time import time
import tempfile

class Hotmail:
    ''' this class is responsible for the hotmail login '''
    def __init__(self, session):
        ''' constructor, saves some needed vars (papyon dependant)'''
        self.session = session
        self.user = self.session.account.account

        current_service = self.session.config.service
        if current_service != 'msn':
            return

        self.profile = self.session.get_profile()
        self.password = self.session.account.password
        self.MSPAuth = self.profile.profile['MSPAuth']

    def get_login_page(self):
        ''' creates the data needed for the hotmail login '''

        # WARNING: This depends on papyon!
        post_url, token = self.profile.request_mail_url()
        post_url += self.profile.profile['lang_preference']

        return 'http://emesene.github.com/emesene-pages/hotmail?&&'+post_url+'?&&'+token['token']
