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

    def __init__(self, session):

        self.session = session
        self.user = self.session.account.account

        current_service = self.session.config.service
        if current_service != 'msn':
            return

        self.profile = self.session.get_profile()
        self.password = self.session.account.password
        self.MSPAuth = self.profile['MSPAuth']

    def _get_login_page(self, message_url=None, post_url=None, id='2'):
        if post_url is None:
            if self.user.split('@')[1] == 'msn.com':
                post_url = 'https://msnia.login.live.com/ppsecure/md5auth.srf?lc=' + self.profile['lang_preference']
            else:
                post_url = 'https://login.live.com/ppsecure/md5auth.srf?lc=' + self.profile['lang_preference']

        if message_url is None:
            message_url = "/cgi-bin/HoTMaiL"

        sl = str(int(time()) - int(self.profile['LoginTime']))
        auth = self.MSPAuth
        sid = self.profile['sid']
        cred =  hashlib.md5(auth + sl + self.password).hexdigest()

        template_data = {
            'id': id,
            'site': post_url,
            'login': self.user.split('@')[0],
            'email': self.user,
            'sid': sid,
            'kv': '',
            'sl': sl,
            'url': message_url,
            'auth': auth,
            'creds': cred
        }

        return self._parse_template(template_data)

    def _parse_template(self, data):
        hotmlog_file = open(os.path.join(os.getcwd(), 'data','hotmlog.htm'))
        hotmlog = hotmlog_file.read()
        hotmlog_file.close()
        for key in data:
            hotmlog = hotmlog.replace('$'+key, data[key])

        name_suffix = hashlib.md5(self.password+self.user).hexdigest() + ".html"

        file_ = tempfile.mkstemp(suffix = name_suffix)[1]

        tmp_file = open(file_, 'w')
        tmp_file.write(hotmlog)
        tmp_file.close()

        return 'file:///' + file_
