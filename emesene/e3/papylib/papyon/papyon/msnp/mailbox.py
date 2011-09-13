# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2008 Alen Bou-Haidar <alencool@gmail.com>
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


import gobject

__all__ = ['Mailbox', 'MailMessage']

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

class Mailbox(gobject.GObject):
    """Mailbox information of the User connecting to the service

        @undocumented: __gsignals__, __gproperties__, do_get_property"""

    __gsignals__ = {
            "new-mail-received" : (gobject.SIGNAL_RUN_FIRST,
                                  gobject.TYPE_NONE,
                                  (object,)),
            "unread-mail-count-changed" : (gobject.SIGNAL_RUN_FIRST,
                                  gobject.TYPE_NONE,
                                  (gobject.TYPE_UINT, bool)),
            }

    __gproperties__ = {
            "unread-mail-count": (gobject.TYPE_UINT,
                "Inbox Unread",
                "Number of unread mail in the users inbox",
                0, gobject.G_MAXUINT, 0,
                gobject.PARAM_READABLE),
            }

    def __init__(self, ns_client):
        gobject.GObject.__init__(self)
        self._ns_client = ns_client
        self._unread_mail_count = 0

    @property
    def unread_mail_count(self):
        """Number of unread mail in the users inbox
            @rtype: integer"""
        return self._unread_mail_count

    def request_compose_mail_url(self, contact, callback):
        self._ns_client.send_url_request(('COMPOSE', contact.account), callback)            

    def request_inbox_url(self, callback):
        self._ns_client.send_url_request(('INBOX',), callback)

    def _unread_mail_increased(self, delta):
        self._unread_mail_count += delta
        self.emit("unread-mail-count-changed", self._unread_mail_count, False)
        self.notify("unread-mail-count")

    def _unread_mail_decreased(self, delta):
        if self._unread_mail_count > 0:
            self._unread_mail_count -= delta
            self.emit("unread-mail-count-changed", self._unread_mail_count, False)
            self.notify("unread-mail-count")

    def _initial_set(self, unread_number):
        if unread_number > 0:
            self._unread_mail_count = unread_number
            self.emit("unread-mail-count-changed", unread_number, True)
            self.notify("unread-mail-count")

    def _new_mail(self, name, address, subject, post_url, form_data):
        mail = MailMessage(name, address, subject, post_url, form_data)
        self.emit("new-mail-received", mail)

    def do_get_property(self, pspec):
        name = pspec.name.lower().replace("-", "_")
        return getattr(self, name)
gobject.type_register(Mailbox)
