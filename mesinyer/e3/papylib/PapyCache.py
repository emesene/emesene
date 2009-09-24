# -*- coding: utf-8 -*-
#
# papylib - an emesene extension for papyon
#
# Copyright (C) 2009 Orfeo (Otacon) <orfeo18@gmail.com>
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

import os
import base64

from e3.cache import *
import papyon

# TODO: this sucks, currently :)
CONFIG_PATH = os.path.expanduser(os.path.join('~', '.config', 'emesene2'))

class PapyCache:

    def __init__(self ,papyclient ,session):
        self._avatar_cache = AvatarCache(CONFIG_PATH, session.account.account)
        self._emoticon_cache = EmoticonCache(CONFIG_PATH, session.account.account)
        self.msn_object_store = papyclient.msn_object_store

    def parse(self, msn_object):
        if msn_object._type == papyon.p2p.MSNObjectType.DYNAMIC_DISPLAY_PICTURE:
            return self._avatar_cache.parse()
        if msn_object._type == papyon.p2p.MSNObjectType.DISPLAY_PICTURE:
            return self._avatar_cache.parse()
        elif msn_object._type == papyon.p2p.MSNObjectType.CUSTOM_EMOTICON:
            return self._emoticon_cache.parse()
        else:
            return None

    def list(self, msn_object):
        '''return a list of tuples (stamp, hash) of the elements on cache
        '''
        return self.parse(msn_object)

    def remove(self, msn_object):
        '''remove an item from cache
        return True on success False otherwise
        item -- the name of the image to remove
        '''
        if msn_object._type == papyon.p2p.MSNObjectType.DYNAMIC_DISPLAY_PICTURE:
            return self._avatar_cache.remove()
        if msn_object._type == papyon.p2p.MSNObjectType.DISPLAY_PICTURE:
            return self._avatar_cache.remove()
        elif msn_object._type == papyon.p2p.MSNObjectType.CUSTOM_EMOTICON:
            return self._emoticon_cache.remove()
        else:
            return None

    def get(self, msn_object):
        '''Checks if msn_object is in cache. If it's not in cache
        downloads it and returns the path. If there's no support
        in cache for this msnobject returns None.
        '''
        #Actually saves it in avatar cache...
        if msn_object._type == papyon.p2p.MSNObjectType.DYNAMIC_DISPLAY_PICTURE:
            if base64.b16encode(msn_object._data_sha) not in self._avatar_cache:
                cbcks = (self._avatar_downloaded, self._download_failed)
                self.msn_object_store.request(msn_object, cbcks)
            path = os.path.join(self._avatar_cache.path, base64.b16encode(msn_object._data_sha))
            return path

        elif msn_object._type == papyon.p2p.MSNObjectType.DISPLAY_PICTURE:
            if base64.b16encode(msn_object._data_sha) not in self._avatar_cache:
                cbcks = (self._avatar_downloaded, self._download_failed)
                self.msn_object_store.request(msn_object, cbcks)
            path = os.path.join(self._avatar_cache.path, base64.b16encode(msn_object._data_sha))
            return path
            
        elif msn_object._type == papyon.p2p.MSNObjectType.CUSTOM_EMOTICON:
            if base64.b16encode(msn_object._data_sha) not in self._emoticon_cache:
                cbcks = (self._emoticon_downloaded, self._download_failed)
                self.msn_object_store.request(msn_object, cbcks)
            path = os.path.join(self._avatar_cache.path, base64.b16encode(msn_object._data_sha))
            return path
        else:
            return None

    
    def _avatar_downloaded(self, msn_object, callback):
        '''this callback saves the avatar in /tmp folder
        then gives it to the caching system.
        '''
        image = open( "/tmp/" + base64.b16encode(msn_object._data_sha), 'w')
        image.write(msn_object._data.getvalue())
        image.flush()
        image.close()
        self._avatar_cache.insert(image.name)

    def _emoticon_downloaded(self, msn_object, callback):
        '''this callback saves the custom emoticon 
        in /tmp folder then gives it to the caching system
        '''
        image = open( "/tmp/" + base64.b16encode(msn_object._data_sha), 'w')
        image.write(msn_object._data.getvalue())
        image.flush()
        image.close()
        self._emoticon_cache.insert((msn_object._friendly,image.name))

    def _download_failed(self, reason):
        '''callback to handle failing of a download'''
        print reason
        

