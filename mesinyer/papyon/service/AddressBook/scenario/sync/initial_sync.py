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
from papyon.service.AddressBook.constants import *

__all__ = ['InitialSyncScenario']

class InitialSyncScenario(BaseScenario):
    def __init__(self, address_book, membership, callback, errback, account=''):
        """Synchronizes the membership content when logging in.

            @param membership: the address book service
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        BaseScenario.__init__(self, 'Initial', callback, errback)
        self.__membership = membership
        self.__address_book = address_book

        self.__membership_response = None
        self.__ab_response = None
        self.__creating_ab = False

        self.__account = account

    def execute(self):
        self.__address_book.FindAll((self.__ab_findall_callback,),
                                    (self.__ab_findall_errback,),
                                    self._scenario, False)
        self.__membership.FindMembership((self.__membership_findall_callback,),
                                         (self.__membership_findall_errback,),
                                         self._scenario, ['Messenger'],
                                         False)

    def __membership_findall_callback(self, result):
        self.__membership_response = result
        self.__sync_callback()

    def __ab_findall_callback(self, result):
        self.__ab_response = result
        self.__sync_callback()

    def __membership_findall_errback(self, error_code):
        self.__sync_errback(error_code)

    def __ab_findall_errback(self, error_code):
        self.__sync_errback(error_code)

    def __sync_callback(self):
        if self.__membership_response is not None and \
           self.__ab_response is not None:
            self.callback(self.__ab_response, self.__membership_response)
            self.__membership_response = None
            self.__ab_response = None

    def __sync_errback(self, error_code):
        if error_code == 'ABDoesNotExist':
            if not self.__creating_ab:
                self.__creating_ab = True
                self.__address_book.Add((self.__ab_add_callback,),
                                        (self.__ab_add_errback,),
                                        self._scenario,
                                        self.__account)
            return
        self.errback(AddressBookError.UNKNOWN)

    def __ab_add_callback(self, *args):
        self.__creating_ab = False
        self.execute()

    def __ab_add_errback(self, error_code):
        self.__creating_ab = False
        if error_code == 'ABAlreadyExists':
            self.execute()
            return
        self.errback(AddressBookError.UNKNOWN)

