# -*- coding: utf-8 -*-
#
# papylib - an emesene extension for papyon
#
# Copyright (C) 2009 Riccardo (C10uD) <c10ud.dev@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import papylib.Worker
import protocol.Account
import protocol.Message
import protocol.Session
from protocol.Action import Action

class Session(protocol.Session):
    '''a specialization of protocol.Session'''
    NAME = 'Papyon session'
    DESCRIPTION = 'MSN session with papyon library'
    AUTHOR = 'Riccardo (C10uD)'
    WEBSITE = 'www.emesene.org'

    def __init__(self, id_=None, account=None):
        '''constructor'''
        protocol.Session.__init__(self, id_, account)

    def login(self, account, password, status, proxy, use_http=False):
        '''start the login process'''
        self.account = protocol.Account(account, password, status)
        worker = papylib.Worker('emesene2', self, proxy, use_http)
        worker.start()

        self.add_action(Action.ACTION_LOGIN, (account, password, status))

    def send_message(self, cid, text, style=None):
        '''send a common message'''
        account = self.account.account
        message = protocol.Message(protocol.Message.TYPE_MESSAGE, text, account,
            style)
        self.add_action(Action.ACTION_SEND_MESSAGE, (cid, message))

    def request_attention(self, cid):
        '''request the attention of the contact'''
        account = self.account.account
        message = protocol.Message(protocol.Message.TYPE_NUDGE, None, account)
        self.add_action(Action.ACTION_SEND_MESSAGE, (cid, message))
