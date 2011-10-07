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
import e3
from e3.hotmail.Hotmail import Hotmail

import time
import logging
log = logging.getLogger('gui.base.MainWindowBase')

class MainWindowBase(object):
    '''a widget that contains all the components inside'''

    def __init__(self, session, on_new_conversation, on_close,
                on_disconnect_cb):
        '''class constructor'''

        self.session = session
        self.on_new_conversation = on_new_conversation
        self.on_close = on_close
        self.on_disconnect_cb = on_disconnect_cb

        self.__hotmail = Hotmail(self.session)
        self.session.signals.mail_count_changed.subscribe(self._on_mail_count_changed)

    def on_mail_click(self):
        self.__hotmail.openInBrowser()

    def on_new_conversation_requested(self, account):
        '''Slot called when the user doubleclicks
        an entry in the contact list'''
        cid = time.time()
        self.on_new_conversation(cid, [account], False)
        #this calls the e3 Handler
        self.session.new_conversation(account, cid)

    def _on_mail_count_changed(self, count):
        pass

    def on_disconnect(self):
        '''callback called when the disconnect option is selected'''
        self.session.signals.mail_count_changed.unsubscribe(
            self._on_mail_count_changed)

