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

import Hotmail
import Desktop
import webbrowser

class MailManager:

    def __init__(self, session):
        self.session = session

    def open_in_browser(self):
        Desktop.open(self._get_mail_url())

    def open_in_default_client(self):
        webbrowser.open("mailto:")

    def _get_mail_url(self):
        current_service = self.session.account.service
        if current_service == "talk.google.com":
            return "http://mail.google.com/"
        elif current_service == "chat.facebook.com":
            return "http://www.facebook.com/messages/"
        else:
            hotmail = Hotmail.Hotmail(self.session)
            return hotmail.get_login_page()
