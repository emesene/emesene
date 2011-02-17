#!/usr/bin/env python
'''Bot example using e3'''

# -*- coding: utf-8 -*-

#   This file is part of emesene.
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

import time
import Queue
# i will use the gobject main loop, but you can use what you want..
import gobject

import e3
from e3 import msn
from e3 import jabber

class Example(object):
    '''a example object, you can do it on another way..'''

    def __init__(self, account, password, status, proxy, use_http_method=False):
        '''class constructor'''
        self.session = msn.Session()
        #self.session = jabber.Session()
        signals = self.session.signals
        signals.login_succeed.subscribe(self.on_login_succeed)
        signals.login_failed.subscribe(self.on_login_failed)
        signals.contact_list_ready.subscribe( self.on_contact_list_ready)
        signals.conv_first_action.subscribe( self.on_conv_first_action)
        signals.conv_started.subscribe( self.on_conv_started)
        signals.conv_message.subscribe( self.on_conv_message)

        self.session.login(account, password, status,
            proxy, use_http_method)
        gobject.timeout_add(500, self.session.signals._handle_events)

        self.first_contact_list_ready = True

    def on_login_succeed(self):
        '''handle login succeed'''
        print 'we are in! :)'

    def on_login_failed(self, reason):
        '''handle login failed'''
        print 'login failed :(', reason

    def on_contact_list_ready(self):
        '''handle contact list ready'''
        # avoid the second contact list ready if the session uses cache
        if not self.first_contact_list_ready:
            return

        self.first_contact_list_ready = False

        for group in self.session.groups.values():
            # get a list of contact objects from a list of accounts
            contacts = self.session.contacts.get_contacts(group.contacts)
            for contact in contacts:
                print contact.account, 'in', group.name

        print 'contacts in no group'
        for contact in self.session.contacts.get_no_group():
            print contact.account

        # we start a conversation with someone
        cid = time.time()

        # put here a mail address that exists on your the contact list of the
        # account that is logged in
        self.session.new_conversation('luismarianoguerra@gmail.com', cid)
        self.session.send_message(cid, 'welcome')
        self.session.send_message(cid, ';)')
        self.session.request_attention(cid)

    def on_conv_first_action(self, cid, members):
        '''handle'''
        # we send this message the first time the other user interact with
        # us (that means, when he send us a message or a nudge)
        self.session.send_message(cid, 'finally!')

    def on_conv_started(self, cid):
        '''handle a new conversation created'''
        # we send this message when the conversation is stablished
        self.session.send_message(cid, 'hey you!')

    def on_conv_message(self, cid, sender, message):
        '''handle a message'''
        # when we receive a message, we return the same message and
        # send a new one with a smile
        # it will also return the typing messages, so if you are typing
        # you will get a typing notification and a smile from nowere :P
        self.session.send_message(cid, message.body)
        self.session.send_message(cid, ';)')

if __name__ == '__main__':
    gobject.threads_init()
    example = Example('xmxsxn@hotmail.com', 'secret',
        e3.status.ONLINE, None, False)

    gobject.MainLoop().run()
