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
from papyon.service.AddressBook import *

__all__ = ['GroupRenameScenario']

class GroupRenameScenario(BaseScenario):
    def __init__(self, ab, callback, errback, group_guid='', group_name=''):
        """Renames a group to the address book.

            @param ab: the address book service
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
            @param group_guid: the guid of the group to rename
            @param group_name: the new name for the group"""
        BaseScenario.__init__(self, 'GroupSave', callback, errback)
        self.__ab = ab

        self.group_guid = group_guid
        self.group_name = group_name

    def execute(self):
        self.__ab.GroupUpdate((self.__group_rename_callback,),
                              (self.__group_rename_errback,),
                              self._scenario, self.group_guid,
                              self.group_name)

    def __group_rename_callback(self):
        self.callback()

    def __group_rename_errback(self, error_code):
        errcode = AddressBookError.UNKNOWN
        if error_code == 'GroupAlreadyExists':
            errcode = AddressBookError.GROUP_ALREADY_EXIST
        elif error_code == 'GroupDoesNotExist':
            errcode = AddressBookError.GROUP_DOES_NOT_EXIST
        elif error_code == 'BadArgumentLength':
            errcode = AddressBookError.GROUP_NAME_TOO_LONG
        self.errback(errcode)
