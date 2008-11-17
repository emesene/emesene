# -*- coding: utf-8 -*-
'''a module that defines an account object'''

#   This file is part of emesene.
#
#    Emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
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

class Account(object):
    '''a class to handle the account'''
    
    def __init__(self, account, password, status):
        self.account = account
        self.password = password
        self.status = status

    def set_nick(self, nick):
        '''set the nick of our account to nick'''
        raise NotImplementedError("This method isn't implemented")

    def set_personal_message(self, personal_message):
        '''set the personal message of our account to personal_message'''
        raise NotImplementedError("This method isn't implemented")

    def set_current_media(self, current_media):
        '''set the current media on our account to current_media'''
        raise NotImplementedError("This method isn't implemented")

    def set_status(self, status):
        '''set the status to status, the status should be one of the
        constants on status.py, consider calling status.is_valid.
        Also you should convert it to the values on the library'''
        raise NotImplementedError("This method isn't implemented")

    # actions on other contacts

    def set_alias(self, account, alias):
        '''set the contact alias, give an empty alias to reset'''
        raise NotImplementedError("This method isn't implemented")

    def block(self, account):
        '''block an user'''
        raise NotImplementedError("This method isn't implemented")
    
    def unblock(self, account):
        '''unblock an user'''
        raise NotImplementedError("This method isn't implemented")

    def remove(self, account):
        '''remove an user'''
        raise NotImplementedError("This method isn't implemented")
    
    def add(self, account):
        '''add an user'''
        raise NotImplementedError("This method isn't implemented")

    def move_to_group(self, account, src_group, dest_group):
        '''move a user from src_group to dest_group'''
        raise NotImplementedError("This method isn't implemented")

    def add_to_group(self, account, group):
        '''add an user to a group, return True on success'''
        raise NotImplementedError("This method isn't implemented")
    
    def remove_from_group(self, account, group):
        '''remove an user from a group'''
        raise NotImplementedError("This method isn't implemented")

    # group stuff

    def add_group(self, name):
        '''add a group'''
        raise NotImplementedError("This method isn't implemented")

    def rename_group(self, gid, name):
        '''rename a group'''
        raise NotImplementedError("This method isn't implemented")

    def remove_group(self, gid):
        '''remove a group'''
        raise NotImplementedError("This method isn't implemented")

