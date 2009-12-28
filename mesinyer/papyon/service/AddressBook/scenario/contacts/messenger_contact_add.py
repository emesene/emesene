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
from contact_find import FindContactScenario

from papyon.service.AddressBook.constants import *
from papyon.service.description.AB.constants import ContactEmailType
from papyon.profile import ContactType, Membership, NetworkID

__all__ = ['MessengerContactAddScenario']

class MessengerContactAddScenario(BaseScenario):
    def __init__(self, ab, callback, errback,
                 account='',
                 network_id=NetworkID.MSN,
                 memberships=Membership.NONE,
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
        self.memberships = memberships

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
            self.errback(AddressBookError.UNKNOWN)
            return

        self._ab.ContactAdd((self.__contact_add_callback,),
                            (self.__contact_add_errback,),
                            self._scenario,
                            self.contact_info,
                            invite_info,
                            self.auto_manage_allow_list)

    def __contact_add_callback(self, contact_guid):
        self.memberships |= Membership.FORWARD

        # ContactAdd automatically added the contact to the allow list if
        # it wasn't already allowed or blocked
        allowed_or_blocked = self.memberships & (Membership.BLOCK | Membership.ALLOW)
        if self.auto_manage_allow_list and not allowed_or_blocked:
            self.memberships |= Membership.ALLOW

        fc = FindContactScenario(self._ab,
                (self.__find_contact_callback,),
                self._errback,
                self._scenario)
        fc.id = contact_guid
        fc()

    def __find_contact_callback(self, contact):
        self.callback(contact, self.memberships)

    def __contact_add_errback(self, error_code):
        errcode = AddressBookError.UNKNOWN
        if error_code == 'ContactAlreadyExists':
            errcode = AddressBookError.CONTACT_ALREADY_EXISTS
        elif error_code in ('BadEmailArgument', 'InvalidPassportUser'):
            errcode = AddressBookError.INVALID_CONTACT_ADDRESS
        elif error_code == 'RequestLimitReached':
            errcode = AddressBookError.LIMIT_REACHED
        self.errback(errcode)
