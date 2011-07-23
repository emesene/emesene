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
#
#    Module written by Andrea Stagi <stagi.andrea(at)gmail.com>
#

import imaplib
import time
from threading import Thread

class MailMessage(object):

    def __init__(self, name, address, subject, post_url, form_data):
        self._name = name
        self._subject = subject
        self._address = address
        self._post_url = post_url
        self._form_data = form_data

    @property
    def name(self):
        """The name of the person who sent the email"""
        return self._name

    @property
    def address(self):
        """Email address of the person who sent the email"""
        return self._address

    @property
    def subject(self):
        """Email subject"""
        return self._subject

    @property
    def post_url(self):
        """post url"""
        return self._post_url

    @property
    def form_data(self):
        """form url"""
        return self._form_data

class MailClient(Thread):

    def __init__(self, username, password):
        Thread.__init__(self)
        self._username = username
        self._password = password
        self._handlers = {}
        self._onrun = True
        self._used_times = 5

    def register_handler(self, name, callback):
        self._handlers[name] = callback

    def on_run(self):
        pass

    def on_initialize(self):
        pass

    def on_end(self):
        pass

    def run(self):
        self.on_initialize()
        while self._onrun:
            if not self._used_times == 0:
                self._used_times -= 1
                time.sleep(1)
                continue
            self.on_run()
            self._used_times = 5
        self.on_end()

    def update_counter(self):
        pass

    def new_mails(self):
        pass

    def stop(self):
        self._onrun = False


class NullMail(MailClient):

    def __init__(self, username, password):
        MailClient.__init__(self, username, password)

    def run(self):
        pass


class GMail(MailClient):

    def __init__(self, username, password):
        MailClient.__init__(self, username, password)
        self._imap_server = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        self._count = 0

    def on_run(self):
        old_count, new_count = self.update_counter()
        if old_count < new_count:
            self._handlers["mailcount"](new_count, old_count)
            mail = self.new_mails()
            self._handlers["mailnew"](mail)

    def on_initialize(self):
        self._imap_server.login(self._username, self._password)
        old_count, new_count = self.update_counter()
        self._handlers["mailcount"](new_count, old_count)

    def on_end(self):
        pass

    def update_counter(self):
        old_count = self._count
        self._imap_server.select('INBOX')
        status, response = self._imap_server.status('INBOX', "(UNSEEN)")
        self._count = int(response[0].split()[2].strip(').,]'))
        return (old_count, self._count)

    def new_mails(self):
        status, email_ids = self._imap_server.search(None, '(UNSEEN)')
        e_id = email_ids[0].split()[-1]
        _, address = self._imap_server.fetch(e_id, '(body[header.fields (From)])')
        _, subject = self._imap_server.fetch(e_id, '(body[header.fields (Subject)])')
        address = address[0][1][6:]
        subject = subject[0][1][9:]
        address = address[address.find("<") + 1 : address.find(">")]
        self._imap_server.store(email_ids[0].split()[0],'-FLAGS','\Seen')
        return MailMessage("", address, subject, "", "")

    def stop(self):
        self._onrun = False

