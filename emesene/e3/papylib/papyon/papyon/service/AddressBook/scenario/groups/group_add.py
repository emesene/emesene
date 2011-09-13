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

__all__ = ['GroupAddScenario']

class GroupAddScenario(BaseScenario):
    def __init__(self, ab, callback, errback, group_name=''):
        """Adds a group to the address book.

            @param ab: the address book service
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
            @param group_name: the name of the new group"""
        BaseScenario.__init__(self, 'GroupSave', callback, errback)
        self.__ab = ab

        self.group_name = group_name

    def execute(self):
        self.__ab.GroupAdd(self._callback, self._errback,
                           self._scenario, self.group_name)
