# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Johann Prieur <johann.prieur@gmail.com>
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
from papyon.service.AddressBook.constants import ABUpdateMembershipWrapper
from papyon.service.AddressBook.scenario.base import BaseScenario

from papyon.profile import NetworkID
from papyon.profile import Membership

__all__ = ['UpdateMembershipsScenario']

class UpdateMembershipsScenario(BaseScenario):
    """Scenario used to update contact memberships in a safe way.
        @undocumented: __membership_mapping, __contact_type"""

    __mapping = { Membership.FORWARD: "Forward",
                  Membership.ALLOW:   "Allow",
                  Membership.BLOCK:   "Block",
                  Membership.REVERSE: "Reverse",
                  Membership.PENDING: "Pending" }

    __contact_type = { NetworkID.MSN:      "Passport",
                       NetworkID.EXTERNAL: "Email" }

    def __init__(self, sharing, callback, errback, scenario,
                 account, network, state, old_membership, new_membership):
        """Updates contact memberships.

           @type scenario: L{Scenario<papyon.service.AddressBook.scenario.base.Scenario>}
           @type network: L{NetworkID<papyon.profile.NetworkID>}
           @type old_membership: bitmask of L{Membership<papyon.profile.Membership>}
           @type new_membership: bitmask of L{Membership<papyon.profile.Membership>}
        """
        BaseScenario.__init__(self, scenario, callback, errback)
        self.__sharing = sharing

        self.account = account
        self.contact_type = UpdateMembershipsScenario.__contact_type[network]
        self.old = old_membership
        self.new = new_membership
        self.state = state

        # We keep a trace of what changes are actually done to pass it through
        # the callback or the errback so that the executor of the scenario can
        # update the memberships property of the contact.
        self.__done = old_membership

        # Subscription to the REVERSE or ALLOW lists can only occur when the
        # contact is member of the PENDING list, so when a subscription to the
        # REVERSE or ALLOW membership is detected, we delay the eventual deletion
        # from the PENDING membership list.
        self.__late_pending_delete = False

    def _change(self, membership):
        return (membership & (self.old ^ self.new))

    def _add(self, membership):
        return (self._change(membership) and (membership & self.new))

    def _delete(self, membership):
        return (self._change(membership) and (membership & self.old))

    def execute(self):
        if (self._add(Membership.REVERSE) or self._add(Membership.ALLOW)) and \
                self._delete(Membership.PENDING):
            self.__late_pending_delete = True

        self.__process_delete(UpdateMembershipsScenario.__mapping.keys(),
                              Membership.NONE)

    def __process_delete(self, memberships, last):
        self.__done &= ~last

        if memberships == []:
            self.__process_add(UpdateMembershipsScenario.__mapping.keys(),
                               Membership.NONE)
            return

        current = memberships.pop()
        if self._delete(current) and not (current == Membership.PENDING and \
                                         self.__late_pending_delete):
            membership = UpdateMembershipsScenario.__mapping[current]
            self.__sharing.DeleteMember((self.__process_delete, memberships, current),
                                        (self.__common_errback, self.__done, current),
                                        self._scenario, membership,
                                        self.contact_type, self.state,
                                        self.account)
        else:
            self.__process_delete(memberships, Membership.NONE)

    def __process_add(self, memberships, last):
        self.__done |= last

        if memberships == []:
            if self.__late_pending_delete:
                membership = UpdateMembershipsScenario.__mapping[Membership.PENDING]
                callback = list(self._callback)
                callback.insert(1, self.__done & ~Membership.PENDING)
                callback = tuple(callback) # Required to pass type check in run()
                self.__sharing.DeleteMember(callback,
                                            (self.__common_errback, self.__done,
                                             Membership.PENDING),
                                            self._scenario, membership,
                                            self.contact_type, self.state,
                                            self.account)
            else:
                self.callback(self.__done)
            return

        current = memberships.pop()
        if self._add(current):
            membership = UpdateMembershipsScenario.__mapping[current]
            self.__sharing.AddMember((self.__process_add, memberships, current),
                                     (self.__common_errback, self.__done, current),
                                     self._scenario, membership,
                                     self.contact_type, self.state,
                                     self.account)
        else:
            self.__process_add(memberships, Membership.NONE)

    def __common_errback(self, error, done, failed):
        self.errback(ABUpdateMembershipWrapper(error, done, failed))
