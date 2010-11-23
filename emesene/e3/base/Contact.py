'''a module that defines a contact object'''
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

import status

class Contact(object):
    '''a class that represent a contact'''

    def __init__(self, account, identifier=None, nick='', message=None,
        _status=status.OFFLINE, alias='', blocked=False, cid=None):
        '''class contructor'''
        self.account = account
        self.identifier = identifier or '0'
        self.nick = nick or self.account
        # message is the personal message or status message, as you may
        # call it
        self.message = message or ''
        self.media = ''
        self.status = _status
        self.alias = alias
        self.blocked = blocked
        self.picture = ''
        self.groups = []
        self.cid = cid

        # extra atributes (use contact.attrs.get("attr", "default"))
        self.attrs = {}

    def dict(self):
        '''return a dict representing the object'''
        return dict(account = self.account,
          identifier = self.identifier,
          nick = self.nick,
          message = self.message,
          media = self.media,
          status = self.status,
          alias = self.alias,
          blocked = self.blocked,
          groups = self.groups)

    def _get_display_name(self):
        '''return the alias if exist, if not the nick if not empty, if not
        the mail'''

        return self.alias or self.nick or self.account

    display_name = property(fget=_get_display_name)

    def _get_status_string(self):
        '''return a string representation of the status'''
        return status.STATUS.get(self.status, '?')

    status_string = property(fget=_get_status_string)

    def __repr__(self):
        '''return a string representation of the object'''
        return "<contact account='%s' nick='%s' message='%s' status='%s'>" \
            % (self.account, self.nick, self.message, self.status)
