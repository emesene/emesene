# -*- coding: utf-8 -*-
#
# papylib - an emesene extension for papyon
#
# Copyright (C) 2009-2010 Riccardo (C10uD) <c10ud.dev@gmail.com>
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
from papyon.profile import Membership

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

    CAPABILITIES = [e3.Session.SERVICE_CONTACT_MANAGING,
                    e3.Session.SERVICE_CONTACT_ALIAS,
                    e3.Session.SERVICE_CONTACT_BLOCK,
                    e3.Session.SERVICE_CONTACT_INVITE,
                    e3.Session.SERVICE_GROUP_MANAGING,
                    e3.Session.SERVICE_FILETRANSFER,
                    e3.Session.SERVICE_PROFILE_PICTURE,
                    e3.Session.SERVICE_STATUS,
                    e3.Session.SERVICE_CONTACT_NICK,
                    e3.Session.SERVICE_CONTACT_PM,
                    e3.Session.SERVICE_ENDPOINTS]

    def __init__(self, id_=None, account=None):
        '''constructor'''
        e3.Session.__init__(self, id_, account)

    def load_config(self):
        '''load the config of the session'''
        e3.Session.load_config(self)

        self.__worker.profile.end_point_name = self.config.get_or_set("s_papylib_endpoint_name", "emesene")
        # keepalive conversations...or not
        b_keepalive = self.config.get_or_set("b_papylib_keepalive", False)
        self.__worker.keepalive_conversations = b_keepalive
        # disconnect other endpoints...or not
        b_dc_ep = self.config.get_or_set("b_papylib_disconnect_ep", False)
        if b_dc_ep:
            self.add_action(e3.Action.ACTION_DISCONNECT_OTHER_ENDPOINTS)
        # we fire the event for every endpoint because otherwise we lose
        # endpoints that were present before we logged in
        for endp in self.__worker.profile.end_points.values():
            self.__worker._on_profile_end_point_added(endp)

    def login(self, account, password, status, proxy, host, port,
              use_http=False, use_ipv6=False):
        '''start the login process'''
        self.__worker = Worker(self, proxy, use_http, use_ipv6)
        self.__worker.start()

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

    def send_typing_notification(self, cid):
        '''send typing notification to contact'''
        account = self.account.account
        message = e3.Message(e3.Message.TYPE_TYPING, None, account)
        self.add_action(e3.Action.ACTION_SEND_MESSAGE, (cid, message))

    def request_attention(self, cid):
        '''request the attention of the contact'''
        account = self.account.account
        message = e3.Message(e3.Message.TYPE_NUDGE, None, account)
        self.add_action(e3.Action.ACTION_SEND_MESSAGE, (cid, message))

    def conversation_invite(self, cid, account):
        '''invite a contact to a conversation'''
        self.add_action(e3.Action.ACTION_CONV_INVITE, (cid, account))

    def filetransfer_invite(self, cid, account, filename, completepath, preview_data):
        '''send a file to the first user of the conversation'''
        self.add_action(e3.Action.ACTION_FT_INVITE, (cid, account, filename, completepath, preview_data))

    def call_invite(self, cid, account, a_v_both, surface_other, surface_self):
        '''try to start a call with the first user of the conversation'''
        self.add_action(e3.Action.ACTION_CALL_INVITE, (cid, account, a_v_both, surface_other, surface_self))

    def get_worker(self):
        return self.__worker

    def get_profile(self):
        return self.__worker.profile

    # methods for the privacy tab
    def get_blocked_contacts(self):
        '''return a list containing the contacts in the address book with the
        BLOCK flag set'''
        contacts = self.__worker.address_book.contacts
        return [c.account for c in contacts if (Membership.BLOCK & c.memberships) and \
                ((Membership.FORWARD & c.memberships) or (Membership.REVERSE & c.memberships))]
    
    def get_allowed_contacts(self):
        '''return a list containing the contacts in the address book with the
        ALLOW flag set'''
        contacts = self.__worker.address_book.contacts
        return [c.account for c in contacts if (Membership.ALLOW & c.memberships) and \
                ((Membership.REVERSE & c.memberships) or (Membership.FORWARD & c.memberships))]

    def is_only_reverse(self, account):
        '''return True if the contact has set the REVERSE flag and not the
        FORWARD flag; otherwise False.
        This means, contacts that are not in your contact list but they do have
        you'''
        contacts = self.__worker.address_book.contacts.search_by('account', account)

        if len(contacts) == 0:
            return False

        return (Membership.REVERSE & contacts[0].memberships) and \
                not (Membership.FORWARD & contacts[0].memberships)
        
    def is_only_forward(self, account):
        '''return True if the contact has set the FORWARD flag and not the
        REVERSE flag; otherwise False.
        This means, contacts that are in your contact list but they don't have
        you'''
        contacts = self.__worker.address_book.contacts.search_by('account', account)

        if len(contacts) == 0:
            return False
        
        return (Membership.FORWARD & contacts[0].memberships) and \
                not (Membership.REVERSE & contacts[0].memberships)

    def is_forward(self, account):
        '''return True if the contact has set the FORWARD flag; otherwise False'''
        contacts = self.__worker.address_book.contacts.search_by('account', account)

        if len(contacts) == 0:
            return False
            
        return (Membership.FORWARD & contacts[0].memberships)

    def disconnect_endpoint(self, ep_id):
        '''disconnects a single endpoint from msn'''
        self.add_action(e3.Action.ACTION_DISCONNECT_ENDPOINT, (ep_id,))
