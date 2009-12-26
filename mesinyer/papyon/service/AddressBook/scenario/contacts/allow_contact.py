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
from papyon.service.AddressBook.scenario.base import Scenario
from update_memberships import UpdateMembershipsScenario

from papyon.profile import Membership
from papyon.profile import NetworkID

__all__ = ['AllowContactScenario']

class AllowContactScenario(BaseScenario):
    def __init__(self, sharing, callback, errback, account='',
                 network=NetworkID.MSN, membership=Membership.NONE,
                 state='Accepted'):
        """Allows a contact.

            @param sharing: the membership service
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        BaseScenario.__init__(self, Scenario.BLOCK_UNBLOCK, callback, errback)
        self.__sharing = sharing

        self.account = account
        self.network = network
        self.membership = membership
        self.state = state

    def execute(self):
        new_membership = self.membership | Membership.ALLOW
        um = UpdateMembershipsScenario(self.__sharing,
                                       self._callback,
                                       self._errback,
                                       self._scenario,
                                       self.account,
                                       self.network,
                                       self.state,
                                       self.membership,
                                       new_membership)
        um()
