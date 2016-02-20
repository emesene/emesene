# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2007-2008 Johann Prieur <johann.prieur@gmail.com>
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

from papyon.service.SOAPService import SOAPService
from papyon.util.async import *
from papyon.util.element_tree import XMLTYPE
from papyon.service.SingleSignOn import *
from papyon.service.AddressBook.common import *
from papyon.service.AddressBook.constants import *

from papyon.service.description.AB.constants import ContactGeneral

import logging
logger = logging.getLogger('papyon.service.address_book')

__all__ = ['AB']

class ABResult(object):
    """ABFindAll Result object"""
    def __init__(self, ab, contacts, groups):
        self.ab = ab
        self.contacts = contacts
        self.groups = groups

class Group(object):
    def __init__(self, group):
        self.Id = group.findtext("./ab:groupId")

        group_info = group.find("./ab:groupInfo")

        self.Type = group_info.findtext("./ab:groupType")
        self.Name = group_info.findtext("./ab:name")
        self.IsNotMobileVisible = group_info.findtext("./ab:IsNotMobileVisible", "bool")
        self.IsPrivate = group_info.findtext("./ab:IsPrivate", "bool")

        self.Annotations = annotations_to_dict(group_info.find("./ab:Annotations"))

        self.PropertiesChanged = [] #FIXME: implement this
        self.Deleted = group.findtext("./ab:fDeleted", "bool")
        self.LastChanged = group.findtext("./ab:lastChange", "bool")

    def __hash__(self):
        return hash(self.Id)

    def __eq__(self, other):
        return self.Id == other.Id

    def __repr__(self):
        return "<Group id=%s>" % self.Id

class ContactEmail(object):
    def __init__(self, email):
        self.Type = email.findtext("./ab:contactEmailType")
        self.Email = email.findtext("./ab:email")
        self.IsMessengerEnabled = email.findtext("./ab:isMessengerEnabled", "bool")
        self.Capability = email.findtext("./ab:Capability", "int")
        self.MessengerEnabledExternally = email.findtext("./ab:MessengerEnabledExternally", "bool")

class ContactPhone(object):
    def __init__(self, phone):
        self.Type = phone.findtext("./ab:contactPhoneType")
        self.Number = phone.findtext("./ab:number")
        self.IsMessengerEnabled = phone.findtext("./ab:isMessengerEnabled", "bool")
        self.PropertiesChanged = phone.findtext("./ab:propertiesChanged").split(' ')

class ContactLocation(object):
    def __init__(self, location):
        self.Type = location.findtext("./ab:contactLocationType")
        self.Name = location.findtext("./ab:name")
        self.City = location.findtext("./ab:city")
        self.Country = location.findtext("./ab:country")
        self.PostalCode = location.findtext("./ab:postalcode")
        self.Changes = location.findtext("./ab:Changes").split(' ')

class Contact(object):
    def __init__(self, contact):
        self.Id = contact.findtext("./ab:contactId")

        contact_info = contact.find("./ab:contactInfo")

        self.Groups = []
        groups = contact_info.find("./ab:groupIds")
        if groups is not None:
            for group in groups:
                self.Groups.append(group.text)

        self.DeletedGroups = []
        deletedGroups = contact_info.find("./ab:groupIdsDeleted")
        if deletedGroups is not None:
            for deletedGroup in deletedGroups:
                self.DeletedGroups.append(deletedGroup.text)

        self.Type = contact_info.findtext("./ab:contactType")
        self.QuickName = contact_info.findtext("./ab:quickName")
        self.PassportName = contact_info.findtext("./ab:passportName")
        self.DisplayName = contact_info.findtext("./ab:displayName")
        self.IsPassportNameHidden = contact_info.findtext("./ab:IsPassportNameHidden", "bool")

        self.FirstName = contact_info.findtext("./ab:firstName")
        self.LastName = contact_info.findtext("./ab:lastName")

        self.PUID = contact_info.findtext("./ab:puid", "int")
        self.CID = contact_info.findtext("./ab:CID", "int")

        self.IsNotMobileVisible = contact_info.findtext("./ab:IsNotMobileVisible", "bool")
        self.IsMobileIMEnabled = contact_info.findtext("./ab:isMobileIMEnabled", "bool")
        self.IsMessengerUser = contact_info.findtext("./ab:isMessengerUser", "bool")
        self.IsFavorite = contact_info.findtext("./ab:isFavorite", "bool")
        self.IsSmtp = contact_info.findtext("./ab:isSmtp", "bool")
        self.HasSpace = contact_info.findtext("./ab:hasSpace", "bool")

        self.SpotWatchState = contact_info.findtext("./ab:spotWatchState")
        self.Birthdate = contact_info.findtext("./ab:birthdate", "datetime")

        self.PrimaryEmailType = contact_info.findtext("./ab:primaryEmailType")
        self.PrimaryLocation = contact_info.findtext("./ab:PrimaryLocation")
        self.PrimaryPhone = contact_info.findtext("./ab:primaryPhone")

        self.IsPrivate = contact_info.findtext("./ab:IsPrivate", "bool")
        self.Gender = contact_info.findtext("./ab:Gender")
        self.TimeZone = contact_info.findtext("./ab:TimeZone")

        self.Annotations = annotations_to_dict(contact_info.find("./ab:annotations"))

        self.Emails = []
        emails = contact_info.find("./ab:emails") or []
        for contact_email in emails:
            self.Emails.append(ContactEmail(contact_email))

        self.PropertiesChanged = [] #FIXME: implement this
        self.Deleted = contact.findtext("./ab:fDeleted", "bool")
        self.LastChanged = contact.findtext("./ab:lastChanged", "datetime")

    @property
    def contact_infos(self):
        annotations = {}
        for key in self.Annotations:
            annotations[key] = self.Annotations[key].encode("utf-8")
        return {ContactGeneral.ANNOTATIONS : annotations}


class AB(SOAPService):
    def __init__(self, sso, client, proxies=None):
        self._sso = sso
        self._client = client
        self._tokens = {}
        SOAPService.__init__(self, "AB", proxies)

        self._creating_ab = False
        self._last_changes = XMLTYPE.datetime.DEFAULT_TIMESTAMP

    def Add(self, callback, errback, scenario, account):
        """Creates the address book on the server.

            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
            @param scenario: "Initial"
            @param account: the owner account"""
        if self._creating_ab:
            return
        self._creating_ab = True
        self.__soap_request(callback, errback,
                            self._service.ABAdd, scenario, (account,),
                            (scenario,))

    def HandleABAddResponse(self, callback, errback, response, user_data):
        self._creating_ab = False
        self.FindAll(callback, errback, user_data[0], False)

    def HandleABAddFault(self, callback, errback, response, user_data):
        self._creating_ab = False
        error = AddressBookError.from_fault(response.fault)
        if error == AddressBookError.AB_ALREADY_EXISTS:
            self.FindAll(callback, errback, user_data[0], False)
            return True
        return False

    def FindAll(self, callback, errback, scenario, deltas_only):
        """Requests the contact list.

            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
            @param scenario: "Initial" | "ContactSave" ...
            @param deltas_only: True if the method should only check changes
                since last_change, otherwise False"""
        if self._last_changes == XMLTYPE.datetime.DEFAULT_TIMESTAMP \
        or not deltas_only:
            deltas_only = False
            last_changes = XMLTYPE.datetime.DEFAULT_TIMESTAMP
        else:
            last_changes = self._last_changes
        self.__soap_request(callback, errback,
                self._service.ABFindAll, scenario,
                (XMLTYPE.bool.encode(deltas_only),
                 last_changes),
                (scenario, deltas_only))

    def _HandleABFindAllResponse(self, callback, errback, response, user_data):
        last_changes = response[0] and response[0].find("./ab:lastChange")
        if last_changes is not None \
        and XMLTYPE.datetime.decode(self._last_changes) < XMLTYPE.datetime.decode(last_changes.text):
            self._last_changes = last_changes.text

        groups = []
        contacts = []
        for group in response[1]:
            groups.append(Group(group))

        for contact in response[2]:
            contacts.append(Contact(contact))

        #FIXME: add support for the ab param
        address_book = ABResult(None, contacts, groups)
        run(callback, address_book)

    def _HandleABFindAllFault(self, callback, errback, response, user_data):
        error = AddressBookError.from_fault(response.fault)
        scenario, deltas_only = user_data
        if error == AddressBookError.AB_DOES_NOT_EXIST:
            self.Add(callback, errback, scenario, self._client.profile.account)
            return True
        elif error == AddressBookError.FULL_SYNC_REQUIRED:
            self.FindAll(callback, errback, scenario, False)
            return True
        return False

    def ContactAdd(self, callback, errback, scenario,
            contact_info, invite_info, auto_manage_allow_list=True):
        """Adds a contact to the contact list.

            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
            @param scenario: "ContactSave" | "ContactMsgrAPI"
            @param contact_info: info dict concerning the new contact
            @param invite_info: info dict concerning the sent invite
            @param auto_manage_allow_list: whether to auto add to Allow role or not
        """
        is_messenger_user = contact_info.get('is_messenger_user', None)
        if is_messenger_user is not None:
            is_messenger_user = XMLTYPE.bool.encode(is_messenger_user)
        self.__soap_request(callback, errback,
                self._service.ABContactAdd, scenario,
                (contact_info.get('passport_name', None),
                    is_messenger_user,
                    contact_info.get('contact_type', None),
                    contact_info.get('first_name', None),
                    contact_info.get('last_name', None),
                    contact_info.get('birth_date', None),
                    contact_info.get('email', None),
                    contact_info.get('phone', None),
                    contact_info.get('location', None),
                    contact_info.get('web_site', None),
                    contact_info.get('annotation', None),
                    contact_info.get('comment', None),
                    contact_info.get('anniversary', None),
                    invite_info.get('display_name', ''),
                    invite_info.get('invite_message', ''),
                    contact_info.get('capability', None),
                    auto_manage_allow_list))

    def _HandleABContactAddResponse(self, callback, errback, response, user_data):
        run(callback, response)

    def _HandleABContactAddFault(self, callback, errback, response, user_data):
        """Make sure that "contact exists" errors are handled gracefully."""
        error = AddressBookError.from_fault(response.fault)
        if error == AddressBookError.CONTACT_ALREADY_EXISTS:
            # This error may occur when we try to re-add a previously
            # deleted (and now hidden) contact.
            # We ignore this error as the contact will be added (aka:
            # made visible) anyway.
            logger.warning('AddressBookError: Contact already exists!')
            conflict_id = response.fault.detail. \
                findtext('additionalDetails/conflictObjectId')
            if conflict_id:
                run(callback, conflict_id.lower(), True)
                return True
        elif error == AddressBookError.MEMBER_DOES_NOT_EXIST:
            # This error may occur when the counterpart blocked us
            # and we're trying to add.
            # We ignore this error as the contact may have been added
            # anyway. We'll discover the real content of our address
            # book (including the GUID) via delta sync.
            logger.warning('AddressBookError: Member does not exist!')
            run(callback, None, True)
            return True
        return False

    def ContactDelete(self, callback, errback, scenario,
            contact_id):
        """Deletes a contact from the contact list.

            @param scenario: "Timer" | ...
            @param contact_id: the contact id (a GUID)
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        self.__soap_request(callback, errback,
                self._service.ABContactDelete, scenario,
                (contact_id,))

    def ContactUpdate(self, callback, errback,
            scenario, contact_id, contact_info,
            enable_allow_list_management=False):
        """Updates a contact informations.

            @param scenario: "ContactSave" | "Timer" | ...
            @param contact_id: the contact id (a GUID)
            @param contact_info: info dict
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        if 'is_messenger_user' in contact_info:
            contact_info['is_messenger_user'] = \
                    XMLTYPE.bool.encode(contact_info['is_messenger_user'])

        self.__soap_request(callback, errback,
                self._service.ABContactUpdate, scenario,
                (contact_id,
                    contact_info.get('display_name', None),
                    contact_info.get('is_messenger_user', None),
                    contact_info.get('contact_type', None),
                    contact_info.get(ContactGeneral.FIRST_NAME, None),
                    contact_info.get(ContactGeneral.LAST_NAME, None),
                    contact_info.get(ContactGeneral.BIRTH_DATE, None),
                    contact_info.get(ContactGeneral.EMAILS, None),
                    contact_info.get(ContactGeneral.PHONES, None),
                    contact_info.get(ContactGeneral.LOCATIONS, None),
                    contact_info.get(ContactGeneral.WEBSITES, None),
                    contact_info.get(ContactGeneral.ANNOTATIONS, None),
                    contact_info.get(ContactGeneral.COMMENT, None),
                    contact_info.get(ContactGeneral.ANNIVERSARY, None),
                    contact_info.get('has_space', None),
                    enable_allow_list_management))

    def GroupAdd(self, callback, errback, scenario,
            group_name):
        """Adds a group to the address book.

            @param scenario: "GroupSave" | ...
            @param group_name: the name of the group
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        self.__soap_request(callback, errback,
                self._service.ABGroupAdd, scenario,
                (group_name,))

    def _HandleABGroupAddResponse(self, callback, errback, response, user_data):
        run(callback, response)

    def GroupDelete(self, callback, errback, scenario,
            group_id):
        """Deletes a group from the address book.

            @param scenario: "Timer" | ...
            @param group_id: the id of the group (a GUID)
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        self.__soap_request(callback, errback,
                self._service.ABGroupDelete, scenario,
                (group_id,))

    def GroupUpdate(self, callback, errback, scenario,
            group_id, group_name):
        """Updates a group name.

            @param scenario: "GroupSave" | ...
            @param group_id: the id of the group (a GUID)
            @param group_name: the new name for the group
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        self.__soap_request(callback, errback,
                self._service.ABGroupUpdate, scenario,
                (group_id, group_name))

    def GroupContactAdd(self, callback, errback, scenario,
            group_id, contact_id):
        """Adds a contact to a group.

            @param scenario: "GroupSave" | ...
            @param group_id: the id of the group (a GUID)
            @param contact_id: the id of the contact to add to the
                               group (a GUID)
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        self.__soap_request(callback, errback,
                self._service.ABGroupContactAdd, scenario,
                (group_id, contact_id))

    def GroupContactDelete(self, callback, errback, scenario,
            group_id, contact_id):
        """Deletes a contact from a group.

            @param scenario: "GroupSave" | ...
            @param group_id: the id of the group (a GUID)
            @param contact_id: the id of the contact to delete from the
                               group (a GUID)
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        self.__soap_request(callback, errback,
                self._service.ABGroupContactDelete, scenario,
                (group_id, contact_id))

    @RequireSecurityTokens(LiveService.CONTACTS)
    def __soap_request(self, callback, errback, method, scenario, args,
            user_data=None):
        token = str(self._tokens[LiveService.CONTACTS])
        self._soap_request(method, (scenario, token), args, callback, errback,
                user_data)

    def _HandleSOAPResponse(self, request_id, callback, errback,
            soap_response, user_data):
        run(callback)

    def _HandleSOAPFault(self, request_id, callback, errback,
            soap_response, user_data):
        error = AddressBookError.from_fault(soap_response.fault)
        run(errback, error)

if __name__ == '__main__':
    import sys
    import getpass
    import signal
    import gobject
    import logging
    from papyon.service.SingleSignOn import *

    logging.basicConfig(level=logging.DEBUG)

    if len(sys.argv) < 2:
        account = raw_input('Account: ')
    else:
        account = sys.argv[1]

    if len(sys.argv) < 3:
        password = getpass.getpass('Password: ')
    else:
        password = sys.argv[2]

    mainloop = gobject.MainLoop(is_running=True)

    signal.signal(signal.SIGTERM,
            lambda *args: gobject.idle_add(mainloop.quit()))

    def ab_callback(contacts, groups):
        print contacts
        print groups

    sso = SingleSignOn(account, password)
    ab = AB(sso)
    ab.FindAll((ab_callback,), None, 'Initial', False)

    while mainloop.is_running():
        try:
            mainloop.run()
        except KeyboardInterrupt:
            mainloop.quit()
