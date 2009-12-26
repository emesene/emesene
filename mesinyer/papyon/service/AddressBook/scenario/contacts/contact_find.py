# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Collabora Ltd.
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

__all__ = ['FindContactScenario']

class FindContactScenario(BaseScenario):
    """Scenario used to find a contact in the address book"""

    def __init__(self, ab, callback, errback, scenario, id=''):
        """Updates contact memberships.

           @type scenario: L{Scenario<papyon.service.AddressBook.scenario.base.Scenario>}
           @type account: account name of the contact to find
        """
        BaseScenario.__init__(self, scenario, callback, errback)
        self.__ab = ab

        self.id = id

    def execute(self):
        self.__ab.FindAll((self.__find_all_callback, self.id),
                         (self.__find_all_errback, self.id),
                         self._scenario, True)

    def __find_all_callback(self, address_book_delta, id):
        found_contact = None
        contacts = address_book_delta.contacts
        for contact in contacts:
            if contact.Id == id:
                found_contact = contact
                break
        self.callback(found_contact)

    def __find_all_errback(self, error_code, id):
        errcode = AddressBookError.UNKNOWN
        if error_code == 'FullSyncRequired':
            self.__ab.FindAll((self.__find_all_callback, id),
                              (self.__find_all_errback, id),
                              self._scenario, False)
            return
        self.errback(errcode)
