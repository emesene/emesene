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

__all__ = ['CheckPendingInviteScenario']

class CheckPendingInviteScenario(BaseScenario):
    def __init__(self, sharing, callback, errback):
        """Checks the pending invitations.

            @param sharing: the membership service
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        BaseScenario.__init__(self, Scenario.MESSENGER_PENDING_LIST, callback, errback)
        self.__sharing = sharing

    def execute(self):
        self.__sharing.FindMembership((self.__membership_findall_callback,),
                (self.__membership_findall_errback,),
                self._scenario, ['Messenger'], True)

    def __membership_findall_callback(self, result):
        self.callback(result)

    def __membership_findall_errback(self, error_code):
        errcode = AddressBookError.UNKNOWN
        self.errback(errcode)

