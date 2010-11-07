# -*- coding: utf-8 -*-
#
# papylib - an emesene extension for papyon
#
# Copyright (C) 2009 Riccardo (C10uD) <c10ud.dev@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
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

import e3
from Worker import Worker

import extension

AUTHOR_LIST = ['Riccardo (C10uD)', 'Orfeo (Otacon)', 'Stefano (cando)']

@extension.implements('session')
class Session(e3.Session):
    '''a specialization of e3.base.Session'''
    NAME = 'Papyon session'
    DESCRIPTION = 'MSN session (papyon)'
    AUTHOR = ", ".join(AUTHOR_LIST)
    WEBSITE = 'www.emesene.org'

    SERVICES = {
        "msn": {
            "host": "messenger.hotmail.com",
            "port": "1863"
        }
    }

    def __init__(self, id_=None, account=None):
        '''constructor'''
        e3.Session.__init__(self, id_, account)

    def login(self, account, password, status, proxy, host, port, use_http=False):
        '''start the login process'''
        worker = Worker('emesene2', self, proxy, use_http)
        worker.start()

        # msn password must have 16 chars max.
        password = password[:16]

        self.account = e3.Account(account, password, status, host)

        self.add_action(e3.Action.ACTION_LOGIN, (account, password, status,
            host, port))

    def send_message(self, cid, text, style=None, cedict=None, celist=None):
        '''send a common message'''
        if cedict is None:
            cedict = {}

        if celist is None:
            celist = []

        account = self.account.account
        message = e3.Message(e3.Message.TYPE_MESSAGE, text, account,
            style)
        self.add_action(e3.Action.ACTION_SEND_MESSAGE, (cid, message, cedict, celist))

    def request_attention(self, cid):
        '''request the attention of the contact'''
        account = self.account.account
        message = e3.Message(e3.Message.TYPE_NUDGE, None, account)
        self.add_action(e3.Action.ACTION_SEND_MESSAGE, (cid, message))

    def conversation_invite(self, cid, account):
        '''invite a contact to a conversation'''
        self.add_action(e3.Action.ACTION_CONV_INVITE, (cid, account))

    def filetransfer_invite(self, cid, account, filename, completepath):
        '''send a file to the first user of the conversation'''
        self.add_action(e3.Action.ACTION_FT_INVITE, (cid, account, filename, completepath))

    def call_invite(self, cid, account):
        '''try to start a call with the first user of the conversation'''
        self.add_action(e3.Action.ACTION_CALL_INVITE, (cid, account))

