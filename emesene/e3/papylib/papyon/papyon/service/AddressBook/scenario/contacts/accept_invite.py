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
from update_memberships import UpdateMembershipsScenario

from papyon.profile import NetworkID, Membership

__all__ = ['AcceptInviteScenario']

class AcceptInviteScenario(BaseScenario):
    def __init__(self, sharing, callback, errback,
                 account='',
                 memberships=Membership.NONE,
                 network=NetworkID.MSN):
        """Accepts an invitation.

            @param sharing: the membership service
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
            @param account: str
            @param memberships: int
            @param network: int
        """
        BaseScenario.__init__(self, Scenario.CONTACT_MSGR_API, callback, errback)
        self.__sharing = sharing
        self.account = account
        self.memberships = memberships
        self.network = network

    def execute(self):
        new_membership = self.memberships
        new_membership |= Membership.ALLOW | Membership.REVERSE
        new_membership &= ~Membership.PENDING
        um = UpdateMembershipsScenario(self.__sharing,
                (self.__update_memberships_callback,),
                self._errback,
                self._scenario,
                self.account,
                self.network,
                'Accepted',
                self.memberships,
                new_membership)
        um()

    def __update_memberships_callback(self, memberships):
        self.callback(memberships)
