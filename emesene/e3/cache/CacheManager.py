'''a module to handle caches for users'''
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
from AvatarCache import AvatarCache
from EmoticonCache import EmoticonCache

class CacheManager(object):
    '''a cache manager class
    '''

    def __init__(self, base_path):
        '''constructor

        base_path -- the base directory where the caches will be created
        '''

        self.base_path = base_path

        self.avatars = {}
        self.emoticons = {}

    def get_avatar_cache(self, account):
        '''return an AvatarCache instance for account
        if account cache doesn't exist create it
        '''
        if account in self.avatars:
            return self.avatars[account]

        self.avatars[account] = AvatarCache(self.base_path, account)
        return self.avatars[account]

    def get_emoticon_cache(self, account):
        '''return an EmoticonCache instance for account
        if account cache doesn't exist create it
        '''
        if account in self.emoticons:
            return self.emoticons[account]

        self.emoticons[account] = EmoticonCache(self.base_path, account)
        return self.emoticons[account]

