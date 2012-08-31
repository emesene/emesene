''' XMPP's session '''
# -*- coding: utf-8 -*-
#
# xmpp - an emesene extension for xmpp
#
# Copyright (C) 2009-2012 emesene
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

import socket

from Worker import Worker
from MailClients import *
import facebook

import e3

import logging
log = logging.getLogger('xmpp.Session')


class Session(e3.Session):
    '''a specialization of e3.Session'''
    NAME = 'XMPP Session'
    DESCRIPTION = 'Session to connect to the XMPP network'
    AUTHOR = 'Riccardo (c10ud)'
    WEBSITE = 'www.emesene.org'

    SERVICES = {
        "gtalk": {
            "host": "talk.google.com",
            "port": "5222"
        },
        "facebook": {
            "host": "chat.facebook.com",
            "port": "5222"
        },
        #"messenger": {
        #    "host": "xmpp.messenger.live.com",
        #    "port": "5222"
        #}
    }

    CAPABILITIES = [e3.Session.SERVICE_PROFILE_PICTURE,
                    e3.Session.SERVICE_CONTACT_NICK,
                    e3.Session.SERVICE_CONTACT_PM]

    def __init__(self, id_=None, account=None):
        '''constructor'''
        e3.Session.__init__(self, id_, account)
        self._is_facebook = False
        self.facebook_client = None
        self.mail_client = NullMail()

    def login(self, account, password, status, proxy, host, port,
              use_http=False, use_ipv6=False):
        '''start the login process'''
        self.account = e3.Account(account, password, status, host)

        if host == "talk.google.com":
            try:
                self.mail_client = IMAPMail(self, "imap.gmail.com", 993, account, password)
            except socket.error, sockerr:
                log.warn("couldn't connect to mail server " + str(sockerr))

            # gtalk allows to connect on port 80, it's not HTTP protocol but
            # the port is HTTP so it will pass through firewalls (yay!)
            if use_http:
                port = 80
        elif host == "chat.facebook.com":
            self._is_facebook = True
            self.mail_client = FacebookMail(self)

        self.mail_client.register_handler('mailcount', self.mail_count_changed)
        self.mail_client.register_handler('mailnew', self.mail_received)
        self.mail_client.register_handler('socialreq', self.social_request)

        self.__worker = Worker(self, proxy, use_http, use_ipv6)
        self.__worker.start()

        self.add_action(e3.Action.ACTION_LOGIN, (account, password, status,
            host, port))

    def start_mail_client(self):
        if self._is_facebook and self.config.get_or_set('b_fb_enable_integration', True):
            self.facebook_client = facebook.FacebookCLient(self, self.config.facebook_token)
            self.mail_client.facebook_client = self.facebook_client
        self.mail_client.start()

    def stop_mail_client(self):
        self.mail_client.stop()

    def get_mail_url(self):
        '''return the mail url for the service.
        if mail isn't supported returns None'''
        current_service = self.account.service
        if current_service == "talk.google.com":
            return "http://mail.google.com/"
        elif current_service == "chat.facebook.com":
            return "http://www.facebook.com/messages/"

        return None

    def send_message(self, cid, text, style=None, cedict=None, celist=None):
        '''send a common message'''
        if cedict is None:
            cedict = {}

        if celist is None:
            celist = []

        account = self.account.account
        message = e3.Message(e3.Message.TYPE_MESSAGE, text, account,
            style)
        self.add_action(e3.Action.ACTION_SEND_MESSAGE, (cid, message))

    def send_typing_notification(self, cid):
        '''send typing notification to contact'''
        ##FIXME: implement this
        pass

    def session_has_service(self, service):
        '''returns True if some service is supported, False otherwise'''
        if service not in self.CAPABILITIES:
            return False

        if self._is_facebook:
            return False

        return True

    def request_attention(self, cid):
        '''request the attention of the contact'''
        account = self.account.account
        message = e3.Message(e3.Message.TYPE_MESSAGE,
            '%s requests your attention' % (account, ), account)
        self.add_action(e3.Action.ACTION_SEND_MESSAGE, (cid, message))

    def activate_social_services(self, active):
        '''activates/deactivates social services if avariable in protocol'''
        if not self.facebook_client is None:
            self.facebook_client.set_token(self.config.facebook_token, active)

    def set_social_token(self, raw_token):
        '''store the social service token.
        raw_token is the raw uri to be processed internally'''
        def get_token(token_url):
            '''strips the access token from an url'''
            if token_url is None:
                return token_url

            if token_url.find("#access_token=") == -1:
                return None

            token_start = "#access_token="
            start_token = token_url.find(token_start) + len(token_start)
            end_token = token_url.find("&expires_in")
            return token_url[start_token:end_token]

        self.config.facebook_token = get_token(raw_token)
        #only activate service if we have an access token
        activate = bool(self.config.facebook_token is not None)
        self.activate_social_services(activate)
