# -*- coding: utf-8 -*-
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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

"""Mailbox event interfaces

The interfaces defined in this module allow receiving notification events about
the mailbox."""

from papyon.event import BaseEventInterface

__all__ = ["MailboxEventInterface"]

class MailboxEventInterface(BaseEventInterface):
    """interfaces allowing the user to get notified about events from the Inbox.
    """

    def __init__(self, client):
        BaseEventInterface.__init__(self, client)

    def on_mailbox_unread_mail_count_changed(self, unread_mail_count, 
                                                   initial=False):
        """The number of unread mail messages"""
        pass

    def on_mailbox_new_mail_received(self, mail_message):
        """New mail message notification"""
        pass
