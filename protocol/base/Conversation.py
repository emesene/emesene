# -*- coding: utf-8 -*-
'''a module that defines a conversation object'''

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

class Conversation(object):
    '''this class represents an abstract form of a conversation, independent
    of the protocol, it holds all the basic information of a conversation
    and define some empty methods that will be defined by the protocol
    implementation'''

    def __init__(self, account, members=None):
        '''constructor, account is an Contact object that holds the 
        information of the local account, members is a dict
        with the account id as key and a Contact object as value'''

        self.account = account
        if members is None:
            self.members = []
        else:
            self.members = members
