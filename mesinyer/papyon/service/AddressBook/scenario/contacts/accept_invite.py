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
from messenger_contact_add import MessengerContactAddScenario
from update_memberships import UpdateMembershipsScenario

from papyon.service.AddressBook.constants import *
from papyon.profile import NetworkID, Membership

__all__ = ['AcceptInviteScenario']

class AcceptInviteScenario(BaseScenario):
    def __init__(self, ab, sharing, callback, errback,
                 account='',
                 memberships=Membership.NONE,
                 network=NetworkID.MSN,
                 state='Accepted'):
        """Accepts an invitation.

            @param ab: the address book service
            @param sharing: the membership service
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        BaseScenario.__init__(self, Scenario.CONTACT_MSGR_API, callback, errback)
        self.__ab = ab
        self.__sharing = sharing

        self.add_to_contact_list = True

        self.account = account
        self.memberships = memberships
        self.network = network
        self.state = state

    def execute(self):
        if self.add_to_contact_list and not (self.memberships & Membership.FORWARD):
            self.__add_messenger_contact()
        else:
            new_membership = self.memberships | Membership.ALLOW
            self.__update_memberships(None, new_membership)

    def __add_messenger_contact(self):
        am = MessengerContactAddScenario(self.__ab,
                 (self.__add_contact_callback,),
                 self._errback,
                 self.account,
                 self.network)
        am()

    def __update_memberships(self, contact, new_membership):
        um = UpdateMembershipsScenario(self.__sharing,
                (self.__update_memberships_callback, contact),
                self._errback,
                self._scenario,
                self.account,
                self.network,
                self.state,
                self.memberships,
                new_membership)
        um()

    def __add_contact_callback(self, contact, memberships):
        memberships &= ~Membership.PENDING
        memberships |= Membership.REVERSE
        self.callback(contact, memberships)

    def __update_memberships_callback(self, memberships, contact):
        memberships &= ~Membership.PENDING
        memberships |= Membership.REVERSE
        self.callback(contact, memberships)
