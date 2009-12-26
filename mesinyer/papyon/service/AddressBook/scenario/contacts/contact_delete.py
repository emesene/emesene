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
from papyon.service.AddressBook.scenario.base import Scenario

from papyon.service.AddressBook.constants import *

__all__ = ['ContactDeleteScenario']

class ContactDeleteScenario(BaseScenario):
    def __init__(self, ab, callback, errback, contact_guid=''):
        """Deletes a contact from the address book.

            @param ab: the address book service
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
            @param contact_guid: the guid of the contact to delete"""
        BaseScenario.__init__(self, Scenario.TIMER, callback, errback)
        self.__ab = ab

        self.contact_guid = contact_guid

    def execute(self):
        self.__ab.ContactDelete(self._callback,
                                (self.__contact_delete_errback,),
                                self._scenario, self.contact_guid)

    def __contact_delete_errback(self, error_code):
        errcode = AddressBookError.UNKNOWN
        if error_code == 'ContactDoesNotExist':
            errcode = AddressBookError.CONTACT_DOES_NOT_EXIST
        self.errback(errcode)
