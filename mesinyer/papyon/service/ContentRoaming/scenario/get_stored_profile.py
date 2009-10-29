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

from papyon.service.ContentRoaming.constants import *

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
        self.__storage.GetProfile((self.__get_profile_callback,),
                                  (self.__get_profile_errback,),
                                  self._scenario, self.cid,
                                  True, True, True, True, True, True, 
                                  True, True, True, True, True)

    def __get_profile_callback(self, profile_rid, expression_profile_rid, 
                               display_name, personal_msg, photo_rid, 
                               photo_mime_type, photo_data_size, photo_url):
        callback = self._callback
        callback[0](profile_rid, expression_profile_rid, display_name, 
            personal_msg, photo_rid, *callback[1:])

        if photo_rid is not None:
            self.__storage.get_display_picture(photo_url, 
                               (self.__get_display_picture_callback,),
                               (self.__get_display_picture_errback,))

    def __get_profile_errback(self, error_code):
        errcode = ContentRoamingError.UNKNOWN
        errback = self._errback[0]
        args = self._errback[1:]
        errback(errcode, *args)

    def __get_display_picture_callback(self, type, data):
        callback = self.__dp_callback
        callback[0](type, data, *callback[1:])

    def __get_display_picture_errback(self, error_code):
        # TODO : adapt this to the transport way of handling errors
        errcode = ContentRoamingError.UNKNOWN
        errback = self._errback[0]
        args = self._errback[1:]
        errback(errcode, *args)

