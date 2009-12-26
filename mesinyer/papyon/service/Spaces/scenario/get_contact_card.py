# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Youness Alaoui <kakaroto@users.sourceforge.net>
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
from papyon.service.Spaces.scenario.base import BaseScenario

__all__ = ['GetContactCardScenario']

class GetContactCardScenario(BaseScenario):
    def __init__(self, ccard, contact, callback, errback):
        """Accepts an invitation.

            @param ccard: the contactcard service
            @param contact: the contact to fetch his CCard
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        BaseScenario.__init__(self, callback, errback)
        self.__ccard = ccard
        self.__contact = contact

    def execute(self):
        self.__ccard.GetXmlFeed((self.__get_xml_feed_callback,),
                          (self.__get_xml_feed_errback,), 
                          self.__contact)
        pass
            
    def __get_xml_feed_callback(self, ccard):
        callback = self._callback
        callback[0](ccard, *callback[1:])

    def __get_xml_feed_errback(self, error_code):
        errback = self._errback[0]
        args = self._errback[1:]
        errback(error_code, *args)
