'''base implementation of a main window'''
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

import MailManager
import time
import logging
log = logging.getLogger('gui.base.MainWindowBase')

class MainWindowBase(object):
    '''a widget that contains all the components inside'''

    def __init__(self, session, on_new_conversation):
        '''class constructor'''

        self.session = session
        self.on_new_conversation = on_new_conversation

        self._mail = MailManager.MailManager(self.session)
        self.session.signals.mail_count_changed.subscribe(self._on_mail_count_changed)
        self.session.signals.social_request.subscribe(self._on_social_request)
        self.session.signals.broken_profile.subscribe(self._on_broken_profile)

    def on_mail_click(self):
        if self.session.config.b_open_mail_in_desktop:
            self._mail.open_in_default_client()
        else:
            self._mail.open_in_browser()

    def on_new_conversation_requested(self, account):
        '''Slot called when the user doubleclicks
        an entry in the contact list'''
        cid = time.time()
        self.on_new_conversation(cid, [account], False)
        #this calls the e3 Handler
        self.session.new_conversation(account, cid)

    def _on_mail_count_changed(self, count):
        '''update ui widget with new email count'''
        pass

    def _on_social_request(self, conn_url):
        pass

    def _on_broken_profile(self):
        '''called when a person has a broken profile'''
        dialog = extension.get_default('dialog')
        dialog.broken_profile(self.session.close)

    def on_disconnect(self):
        '''callback called when the disconnect option is selected'''
        self.session.signals.mail_count_changed.unsubscribe(
            self._on_mail_count_changed)
        self.session.signals.broken_profile.unsubscribe(self._on_broken_profile)
        self.session.signals.social_request.unsubscribe(self._on_social_request)
