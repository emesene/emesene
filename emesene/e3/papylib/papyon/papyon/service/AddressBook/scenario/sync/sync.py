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
from papyon.service.AddressBook.scenario.base import BaseScenario

__all__ = ['SyncScenario']

class SyncScenario(BaseScenario):
    def __init__(self, address_book, sharing, callback, errback,
                 delta_only=False):
        """Synchronizes the membership content when logging in.

            @param address_book: the address book service
            @param sharing: the sharging service
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        BaseScenario.__init__(self, 'Initial', callback, errback)
        self.__address_book = address_book
        self.__sharing = sharing

        self.__membership_response = None
        self.__ab_response = None

        self.__delta_only = delta_only

    def execute(self):
        self.__address_book.FindAll((self.__ab_findall_callback,),
                                    self._errback, self._scenario, self.__delta_only)
        self.__sharing.FindMembership((self.__membership_findall_callback,),
                                      self._errback, self._scenario,
                                      ['Messenger'], self.__delta_only)

    def __membership_findall_callback(self, result):
        self.__membership_response = result
        self.__sync_callback()

    def __ab_findall_callback(self, result=None):
        self.__ab_response = result
        self.__sync_callback()

    def __sync_callback(self):
        if self.__membership_response is not None and \
           self.__ab_response is not None:
            self.callback(self.__ab_response, self.__membership_response)
            self.__membership_response = None
            self.__ab_response = None
