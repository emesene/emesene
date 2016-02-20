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

from papyon.service.description.AB.constants import ContactEmailType
from papyon.profile import ContactType, NetworkID

__all__ = ['MessengerContactAddScenario']

class MessengerContactAddScenario(BaseScenario):
    def __init__(self, ab, callback, errback,
                 account='',
                 network_id=NetworkID.MSN,
                 contact_type=ContactType.REGULAR,
                 contact_info={},
                 invite_display_name='',
                 invite_message=''):
        """Adds a messenger contact and updates the address book.

            @param ab: the address book service
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)"""
        BaseScenario.__init__(self, Scenario.CONTACT_SAVE, callback, errback)

        self._ab = ab

        self.account = account
        self.network_id = network_id

        self.contact_type = contact_type
        self.contact_info = contact_info

        self.invite_display_name = invite_display_name
        self.invite_message = invite_message
        self.auto_manage_allow_list = True

    def execute(self):
        invite_info = { 'display_name' : self.invite_display_name,
                        'invite_message' : self.invite_message }

        if self.network_id == NetworkID.MSN:
            self.contact_info['passport_name'] = self.account
            self.contact_info['contact_type'] = self.contact_type
            self.contact_info['is_messenger_user'] = True
        elif self.network_id == NetworkID.EXTERNAL:
            self.contact_info.setdefault('email', {})[ContactEmailType.EXTERNAL] = self.account
            self.contact_info['capability'] = self.network_id
        else:
            raise NotImplementedError("Network ID '%s' is not implemented" %
                    self.network_id)

        self._ab.ContactAdd(self._callback,
                            self._errback,
                            self._scenario,
                            self.contact_info,
                            invite_info,
                            self.auto_manage_allow_list)
