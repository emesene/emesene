# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Johann Prieur <johann.prieur@gmail.com>
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
from base import *

from papyon.util.async import *

__all__ = ['GetStoredProfileScenario']

class GetStoredProfileScenario(BaseScenario):
    def __init__(self, storage, callback, dp_callback, errback, cid=''):
        """Gets the roaming profile stored on the server

            @param storage: the storage service
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)            
        """
        BaseScenario.__init__(self, 'Initial', callback, errback)
        self.__storage = storage
        self.__dp_callback = dp_callback

        self.cid = cid

    def execute(self):
        self.__storage.GetProfile((self.__get_profile_callback,), self._errback,
                                  self._scenario, self.cid,
                                  True, True, True, True, True, True,
                                  True, True, True, True, True)

    def __get_profile_callback(self, profile_rid, expression_profile_rid,
                               display_name, personal_msg, user_tile_url,
                               photo_rid, photo_mime_type, photo_data_size,
                               photo_url):
        run(self._callback, profile_rid, expression_profile_rid,
                display_name, personal_msg, photo_rid)

        if photo_rid is not None:
            self.__storage.get_display_picture(self.__dp_callback,
                                               self._errback,
                                               photo_url, user_tile_url)
