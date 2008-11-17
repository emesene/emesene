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

import protocol.Account
import protocol.Action as Action

class Account(protocol.Account):
    '''a class to handle the account'''

    def __init__(self, account, password, status, actions):
        '''constructor'''
        protocol.Account.__init__(self, account, password, status)
        self.actions = actions
        
        self.nick = account
        self.message = ''

    def add_action(self, id_, args=()):
        '''add an event to the session queue'''
        self.actions.put(Action(id_, args))

    def set_nick(self, nick):
        '''set the nick of our account to nick'''
        self.add_action(Action.ACTION_SET_NICK, (nick,))

    def set_personal_message(self, personal_message):
        '''set the personal message of our account to personal_message'''
        self.add_action(Action.ACTION_SET_MESSAGE, (personal_message,))

    def set_current_media(self, current_media):
        '''set the current media on our account to current_media'''
        self.add_action(Action.ACTION_SET_MESSAGE, (current_media,))

    def set_status(self, status):
        '''set the status to status, the status should be one of the
        constants on status.py, consider calling status.is_valid.
        Also you should convert it to the values on the library'''
        self.add_action(Action.ACTION_CHANGE_STATUS, (status,))

    # actions on other contacts

    def set_alias(self, account, alias):
        '''set the contact alias, give an empty alias to reset'''
        self.add_action(Action.ACTION_SET_CONTACT_ALIAS, 
            (account, alias))

    def block(self, account):
        '''block an user'''
        self.add_action(Action.ACTION_BLOCK_CONTACT, (account,))
    
    def unblock(self, account):
        '''unblock an user'''
        self.add_action(Action.ACTION_UNBLOCK_CONTACT, (account,))

    def remove(self, account):
        '''remove an user'''
        self.add_action(Action.ACTION_REMOVE_CONTACT, (account,))
    
    def add(self, account):
        '''add an user'''
        self.add_action(Action.ACTION_ADD_CONTACT, (account,))

    def move_to_group(self, account, src_gid, dest_gid):
        '''move a user from src_group to dest_group'''
        self.add_action(Action.ACTION_MOVE_TO_GROUP, (account, src_gid, 
            dest_gid))

    def add_to_group(self, account, gid):
        '''add an user to a group, return True on success'''
        self.add_action(Action.ACTION_ADD_TO_GROUP, (account, gid))
    
    def remove_from_group(self, account, gid):
        '''remove an user from a group'''
        self.add_action(sAction.ACTION_REMOVE_FROM_GROUP, (account, gid))

    # group stuff

    def add_group(self, name):
        '''add a group'''
        self.add_action(Action.ACTION_ADD_GROUP, (name,))

    def rename_group(self, gid, name):
        '''rename a group'''
        self.add_action(Action.ACTION_RENAME_GROUP, (gid, name))

    def remove_group(self, gid):
        '''remove a group'''
        self.add_action(Action.ACTION_REMOVE_GROUP, (gid,))

