# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Youness Alaoui <kakaroto@users.sourceforge.net>
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
from papyon.service.Spaces.scenario.base import BaseScenario

__all__ = ['GetContactCardScenario']

class GetContactCardScenario(BaseScenario):
    def __init__(self, ccard, contact, callback, errback):
        """Accepts an invitation.

            @param ccard: the contactcard service
            @param contact: the contact to fetch his CCard
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        BaseScenario.__init__(self, callback, errback)
        self.__ccard = ccard
        self.__contact = contact

    def execute(self):
        self.__ccard.GetXmlFeed(self._callback, self._errback, self.__contact)
