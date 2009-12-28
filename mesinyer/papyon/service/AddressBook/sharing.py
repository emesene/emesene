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

from papyon.service.SOAPService import SOAPService
from papyon.util.element_tree import XMLTYPE
from papyon.service.SingleSignOn import *
from papyon.service.AddressBook.common import *

__all__ = ['Sharing']

class Member(object):
    def __init__(self, member):
        self.Roles = {}
        self.MembershipId = member.findtext("./ab:MembershipId")
        self.Account = self.MembershipId
        self.Type = member.findtext("./ab:Type")
        self.DisplayName = member.findtext("./ab:DisplayName")
        self.State = member.findtext("./ab:State")

        self.Deleted = member.findtext("./ab:Deleted", "bool")
        self.LastChanged = member.findtext("./ab:LastChanged", "datetime")
        self.Changes = [] # FIXME: extract the changes
        self.Annotations = annotations_to_dict(member.find("./ab:Annotations"))

    def __hash__(self):
        return hash(self.Type) ^ hash(self.Account)

    def __eq__(self, other):
        return (self.Type == other.Type) and (self.Account == other.Account)

    def __repr__(self):
        return "<%sMember account=%s roles=%r>" % (self.Type, self.Account, self.Roles)

    @staticmethod
    def new(member):
        type = member.findtext("./ab:Type")
        if type == "Passport":
            return PassportMember(member)
        elif type == "Email":
            return EmailMember(member)
        elif type == "Phone":
            return PhoneMember(member)
        elif type == "Circle":
            return CircleMember(member)
        elif type == "Domain":
            return DomainMember(member)
        elif type == "Everyone":
            return EveryoneMember(member)
        elif type == "Group":
            return GroupMember(member)
        elif type == "Role":
            return RoleMember(member)
        elif type == "Service":
            return ServiceMember(member)
        else:
            raise NotImplementedError("Member type not implemented : " + type)


class PassportMember(Member):
    def __init__(self, member):
        Member.__init__(self, member)
        self.Id = member.findtext("./ab:PassportId", "int")
        self.PassportName = member.findtext("./ab:PassportName")
        self.IsPassportNameHidden = member.findtext("./ab:IsPassportNameHidden", "bool")
        self.CID = member.findtext("./ab:CID", "int")
        self.Account = self.PassportName

class EmailMember(Member):
    def __init__(self, member):
        Member.__init__(self, member)
        self.Email = member.findtext("./ab:Email")
        self.Account = self.Email

class PhoneMember(Member):
    def __init__(self, member):
        Member.__init__(self, member)
        self.PhoneNumber = member.findtext("./ab:PhoneNumber")
        self.Account = self.PhoneNumber

class CircleMember(Member):
    def __init__(self, member):
        Member.__init__(self, member)
        self.CircleId = member.findtext("./ab:CircleId")
        self.Account = self.CircleId

class DomainMember(Member):
    def __init__(self, member):
        Member.__init__(self, member)
        self.DomainName = member.findtext("./ab:DomainName")
        self.Account = self.DomainName

class EveryoneMember(Member):
    def __init__(self, member):
        Member.__init__(self, member)

class GroupMember(Member):
    def __init__(self, member):
        Member.__init__(self, member)
        self.Id = member.findtext("./ab:Id")
        self.Account = self.Id

class RoleMember(Member):
    def __init__(self, member):
        Member.__init__(self, member)

class ServiceMember(Member):
    def __init__(self, member):
        Member.__init__(self, member)


class Sharing(SOAPService):
    def __init__(self, sso, proxies=None):
        self._sso = sso
        self._tokens = {}
        SOAPService.__init__(self, "Sharing", proxies)

        self._last_changes = "0001-01-01T00:00:00.0000000-08:00"

    def FindMembership(self, callback, errback, scenario, services, deltas_only):
        """Requests the membership list.

            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
            @param scenario: 'Initial' | ...
            @param services: a list containing the services to check in
                             ['Messenger', 'Invitation', 'SocialNetwork',
                              'Space', 'Profile' ]
            @param deltas_only: True if the method should only check changes
                                since last_change, False else
        """
        self.__soap_request(self._service.FindMembership, scenario,
                (services, deltas_only, self._last_changes), callback, errback)

    def _HandleFindMembershipResponse(self, callback, errback, response, user_data):
        if response[1] is not None:
            self._last_changes = response[1]

        memberships = {}
        for role, members in response[0].iteritems():
            for member in members:
                membership_id = XMLTYPE.int.decode(member.find("./ab:MembershipId").text)
                member_obj = Member.new(member)
                member_id = hash(member_obj)
                if member_id in memberships:
                    memberships[member_id].Roles[role] = membership_id
                else:
                    member_obj.Roles[role] = membership_id
                    memberships[member_id] = member_obj
        callback[0](memberships.values(), *callback[1:])

    def AddMember(self, callback, errback, scenario, member_role, type,
                  state, account):
        """Adds a member to a membership list.

            @param scenario: 'Timer' | 'BlockUnblock' | ...
            @param member_role: 'Allow' | ...
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        self.__soap_request(self._service.AddMember, scenario,
                (member_role, type, state, account), callback, errback)

    def _HandleAddMemberResponse(self, callback, errback, response, user_data):
        callback[0](*callback[1:])

    def DeleteMember(self, callback, errback, scenario, member_role, type,
                     state, account):
        """Deletes a member from a membership list.

            @param scenario: 'Timer' | 'BlockUnblock' | ...
            @param member_role: 'Block' | ...
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        self.__soap_request(self._service.DeleteMember, scenario,
                            (member_role, type, state, account),
                            callback, errback)

    def _HandleDeleteMemberResponse(self, callback, errback, response, user_data):
        callback[0](*callback[1:])

    @RequireSecurityTokens(LiveService.CONTACTS)
    def __soap_request(self, method, scenario, args, callback, errback):
        token = str(self._tokens[LiveService.CONTACTS])
        self._soap_request(method, (scenario, token), args, callback, errback)

    def _HandleSOAPFault(self, request_id, callback, errback,
            soap_response, user_data):
        errcode, errstring = get_detailled_error(soap_response.fault)
        if (request_id == 'AddMember' and errcode == 'MemberAlreadyExists') or \
           (request_id == 'DeleteMember' and errcode == 'MemberDoesNotExist'):
            callback[0](*callback[1:])
        else:
            errback[0](errcode, *errback[1:])

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

    def sharing_callback(memberships):
        print "Memberships :"
        for member in memberships:
            print member

    sso = SingleSignOn(account, password)
    sharing = Sharing(sso)
    sharing.FindMembership((sharing_callback,), None, 'Initial',
            ['Messenger', 'Invitation'], False)

    while mainloop.is_running():
        try:
            mainloop.run()
        except KeyboardInterrupt:
            mainloop.quit()
