# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from papyon.errors import ClientError, ClientErrorType

__all__ = ['AddressBookError', 'AddressBookState']


class AddressBookError(ClientError):
    "Address book related errors"
    UNKNOWN = 0

    AB_DOES_NOT_EXIST = 1
    AB_ALREADY_EXISTS = 2

    CONTACT_ALREADY_EXISTS = 3
    CONTACT_ALREADY_IN_GROUP = 3 # deprecated
    CONTACT_DOES_NOT_EXIST = 4
    CONTACT_NOT_IN_GROUP = 4 # deprecated
    INVALID_CONTACT_ADDRESS = 5

    GROUP_ALREADY_EXISTS = 6
    GROUP_DOES_NOT_EXIST = 7

    MEMBER_ALREADY_EXISTS = 8
    MEMBER_DOES_NOT_EXIST = 9

    INVALID_ARGUMENT = 10
    GROUP_NAME_TOO_LONG = 10 # deprecated
    LIMIT_REACHED = 11
    FULL_SYNC_REQUIRED = 12


    def __init__(self, code, fault="", details=""):
        ClientError.__init__(self, ClientErrorType.ADDRESSBOOK, code)
        self._fault = fault
        self._details = details

    @staticmethod
    def get_detailled_error(fault):
        if fault.detail is not None:
            errorcode = fault.detail.findtext("./ab:errorcode")
            errorstring = fault.detail.findtext("./ab:errorstring")
        else:
            errorcode = fault.faultcode
            errorstring = fault.faultstring
        return errorcode, errorstring

    @staticmethod
    def from_fault(fault):
        code = AddressBookError.UNKNOWN
        errcode, errstring = AddressBookError.get_detailled_error(fault)
        if errcode == 'ABDoesNotExist':
            code = AddressBookError.AB_DOES_NOT_EXIST
        elif errcode == 'ABAlreadyExists':
            code = AddressBookError.AB_ALREADY_EXISTS
        elif errcode == 'ContactDoesNotExist':
            code = AddressBookError.CONTACT_DOES_NOT_EXIST
        elif errcode == 'ContactAlreadyExists':
            code = AddressBookError.CONTACT_ALREADY_EXISTS
        elif errcode == 'ContactDoesNotExist':
            code = AddressBookError.CONTACT_DOES_NOT_EXIST
        elif errcode in ('BadEmailArgument', 'InvalidPassportUser'):
            code = AddressBookError.INVALID_CONTACT_ADDRESS
        elif errcode == 'MemberAlreadyExists':
            code = AddressBookError.MEMBER_ALREADY_EXISTS
        elif errcode == 'MemberDoesNotExist':
            code = AddressBookError.MEMBER_DOES_NOT_EXIST
        elif errcode == 'GroupAlreadyExists':
            code = AddressBookError.GROUP_ALREADY_EXISTS
        elif errcode == 'GroupDoesNotExist':
            code = AddressBookError.GROUP_DOES_NOT_EXIST
        elif errcode == 'BadArgumentLength':
            code = AddressBookError.INVALID_ARGUMENT
        elif errcode == 'RequestLimitReached':
            code = AddressBookError.LIMIT_REACHED
        elif errcode == 'FullSyncRequired':
            code = AddressBookError.FULL_SYNC_REQUIRED
        return AddressBookError(code, errcode, errstring)

    def __str__(self):
        return "Address Book error (%s): %s" % (self._fault, self._details)


class ABUpdateMembershipWrapper(ClientError):
    """Wrap an error that occured while updating membership"""
    def __init__(self, error, done, failed):
        ClientError.__init__(self, error._type, error._code)
        self._error = error
        self.done = done
        self.failed = failed

    def __str__(self):
        return str(self._error)


class AddressBookState(object):
    """Addressbook synchronization state.

    An adressbook is said to be synchronized when it
    matches the addressbook stored on the server."""

    NOT_SYNCHRONIZED = 0
    """The addressbook is not synchronized yet"""
    INITIAL_SYNC = 1
    """The addressbook is being initialized"""
    RESYNC = 2
    """The addressbook is being re-synchronized after an update"""
    SYNCHRONIZED = 3
    """The addressbook is already synchronized"""
