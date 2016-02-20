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

__all__ = ['ContactUpdatePropertiesScenario']

class ContactUpdatePropertiesScenario(BaseScenario):
    def __init__(self, ab, callback, errback, contact_guid='',
                 contact_properties={}):
        """Updates a contact properties

            @param ab: the address book service
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
            @param contact_guid: the guid of the contact to update"""
        BaseScenario.__init__(self, Scenario.CONTACT_SAVE, callback, errback)
        self.__ab = ab

        self.contact_guid = contact_guid
        self.contact_properties = contact_properties
        self.enable_allow_list_management = False

    def execute(self):
        self.__ab.ContactUpdate(self._callback, self._errback,
                                self._scenario, self.contact_guid,
                                self.contact_properties,
                                self.enable_allow_list_management)
