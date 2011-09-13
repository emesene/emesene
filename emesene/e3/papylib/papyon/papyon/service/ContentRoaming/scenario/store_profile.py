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

__all__ = ['StoreProfileScenario']

class StoreProfileScenario(BaseScenario):
    def __init__(self, storage, callback, errback, 
                 cid, profile_id, expression_profile_id, display_picture_id,
                 display_name='', personal_message='', display_picture=''):
        """Updates the roaming profile stored on the server

            @param storage: the storage service
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)            
        """
        BaseScenario.__init__(self, 'RoamingIdentityChanged', callback, errback)
        self.__storage = storage

        self.__cid = cid
        self.__profile_id = profile_id
        self.__expression_profile_id = expression_profile_id
        self.__display_picture_id = display_picture_id

        self.display_name = display_name
        self.personal_message = personal_message
        self.display_picture = display_picture

    def execute(self):
        self.__storage.UpdateProfile((self.__update_profile_callback,),
                                     self._errback, self._scenario,
                                     self.__profile_id, self.display_name,
                                     self.personal_message, 0)

    def __update_profile_callback(self):
        if not self.display_picture or not self.__display_picture_id:
            run(self._callback)
        elif not self.__cid:
            self.__delete_relationship_profile_callback()
        else:
            self.__storage.DeleteRelationships(
                (self.__delete_relationship_profile_callback,),
                self._errback,
                self._scenario,
                self.__display_picture_id,
                self.__cid, None)

    def __delete_relationship_profile_callback(self):
        if not self.__expression_profile_id:
            self.__delete_relationship_expression_callback()
        else:
            self.__storage.DeleteRelationships(
                    (self.__delete_relationship_expression_callback,),
                    self._errback, self._scenario, self.__display_picture_id,
                    None, self.__expression_profile_id)

    def __delete_relationship_expression_callback(self):
        # FIXME : add support for dp name
        self.__storage.CreateDocument(
            (self.__create_document_callback,), self._errback,
            self._scenario, self.__cid,
            "roaming", self.display_picture[0],
            self.display_picture[1].encode('base64'))
        
    def __create_document_callback(self, document_rid):
        self.__storage.CreateRelationships(self._callback, self._errback,
            self._scenario, self.__expression_profile_id, document_rid)
