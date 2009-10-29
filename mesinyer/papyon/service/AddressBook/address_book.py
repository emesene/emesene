# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2007 Ali Sabil <ali.sabil@gmail.com>
# Copyright (C) 2007-2008 Johann Prieur <johann.prieur@gmail.com>
# Copyright (C) 2007 Ole André Vadla Ravnås <oleavr@gmail.com>
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

import ab
import sharing
import scenario

import papyon
import papyon.profile as profile
from papyon.profile import Membership, NetworkID
from papyon.util.decorator import rw_property
from papyon.profile import ContactType
from papyon.service.AddressBook.constants import *
from papyon.service.description.AB.constants import *
from papyon.service.AddressBook.scenario.contacts import *

import gobject

__all__ = ['AddressBook', 'AddressBookState']

class AddressBookStorage(set):
    def __init__(self, initial_set=()):
        set.__init__(self, initial_set)

    def __repr__(self):
        return "AddressBook : %d contact(s)" % len(self)

    def __getitem__(self, key):
        i = 0
        for contact in self:
            if i == key:
                return contact
            i += 1
        raise IndexError("Index out of range")

    def __getattr__(self, name):
        if name.startswith("search_by_"):
            field = name[10:]
            def search_by_func(criteria):
                return self.search_by(field, criteria)
            search_by_func.__name__ = name
            return search_by_func
        elif name.startswith("group_by_"):
            field = name[9:]
            def group_by_func():
                return self.group_by(field)
            group_by_func.__name__ = name
            return group_by_func
        else:
            raise AttributeError, name

    def search_by_memberships(self, memberships):
        result = []
        for contact in self:
            if contact.is_member(memberships):
                result.append(contact)
                # Do not break here, as the account
                # might exist in multiple networks
        return AddressBookStorage(result)

    def search_by_groups(self, *groups):
        result = []
        groups = set(groups)
        for contact in self:
            if groups <= contact.groups:
                result.append(contact)
        return AddressBookStorage(result)

    def group_by_group(self):
        result = {}
        for contact in self:
            groups = contact.groups
            for group in groups:
                if group not in result:
                    result[group] = set()
                result[group].add(contact)
        return result

    def search_by_predicate(self, predicate):
        result = []
        for contact in self:
            if predicate(contact):
                result.append(contact)
        return AddressBookStorage(result)

    def search_by(self, field, value):
        result = []
        if isinstance(value, basestring):
            value = value.lower()
        for contact in self:
            contact_field_value = getattr(contact, field)
            if isinstance(contact_field_value, basestring):
                contact_field_value = contact_field_value.lower()
            if contact_field_value == value:
                result.append(contact)
                # Do not break here, as the account
                # might exist in multiple networks
        return AddressBookStorage(result)

    def group_by(self, field):
        result = {}
        for contact in self:
            value = getattr(contact, field)
            if value not in result:
                result[value] = AddressBookStorage()
            result[value].add(contact)
        return result


class AddressBook(gobject.GObject):

    __gsignals__ = {
            "error" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),

            "contact-added"           : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),
            "messenger-contact-added" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),

            "contact-deleted"         : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                 (object,)),

            # FIXME: those signals will be removed in the future and will be
            # moved to profile.Contact
            "contact-accepted"         : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),
            "contact-rejected"       : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),
            "contact-blocked"         : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),
            "contact-unblocked"       : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),
            "contact-allowed"         : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),
            "contact-disallowed"      : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),

            "group-added"             : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),
            "group-deleted"           : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),
            "group-renamed"           : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),

            "group-contact-added"     : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object, object)),
            "group-contact-deleted"   : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object, object))
            }

    __gproperties__ = {
        "state":  (gobject.TYPE_INT,
                   "State",
                   "The state of the addressbook.",
                   0, 2, AddressBookState.NOT_SYNCHRONIZED,
                   gobject.PARAM_READABLE)
        }

    def __init__(self, sso, client, proxies=None):
        """The address book object."""
        gobject.GObject.__init__(self)

        self._ab = ab.AB(sso, proxies)
        self._sharing = sharing.Sharing(sso, proxies)
        self._client = client

        self.__state = AddressBookState.NOT_SYNCHRONIZED

        self.groups = set()
        self.contacts = AddressBookStorage()
        self._profile = None

    # Properties
    @property
    def state(self):
        return self.__state

    @rw_property
    def _state():
        def fget(self):
            return self.__state
        def fset(self, state):
            self.__state = state
            self.notify("state")
        return locals()

    @property
    def profile(self):
        return self._profile

    def sync(self):
        if self._state != AddressBookState.NOT_SYNCHRONIZED:
            return
        self._state = AddressBookState.SYNCHRONIZING

        def callback(address_book, memberships):
            ab = address_book.ab
            contacts = address_book.contacts
            groups = address_book.groups
            for group in groups:
                g = profile.Group(group.Id, group.Name.encode("utf-8"))
                self.groups.add(g)
            for contact in contacts:
                c = self.__build_contact(contact, Membership.FORWARD)
                if c is None:
                    continue
                if contact.Type == ContactType.ME:
                    self._profile = c
                else:
                    self.contacts.add(c)
            self.__update_memberships(memberships)
            self._state = AddressBookState.SYNCHRONIZED

        initial_sync = scenario.InitialSyncScenario(self._ab, self._sharing,
                (callback,),
                (self.__common_errback, None),
                self._client.profile.account)
        initial_sync()

    # Public API
    def search_contact(self, account, network_id):
        contacts = self.contacts.search_by_network_id(network_id).\
                search_by_account(account)
        if len(contacts) == 0:
            return None
        return contacts[0]

    def search_or_build_contact(self, account, network_id):
        contact = self.search_contact(account, network_id)
        if contact is None:
            contact = profile.Contact(None, network_id, account, account)
        return contact

    def check_pending_invitations(self):
        cp = scenario.CheckPendingInviteScenario(self._sharing,
                 (self.__update_memberships,),
                 (self.__common_errback, None))
        cp()

    def accept_contact_invitation(self, pending_contact, add_to_contact_list=True,
            done_cb=None, failed_cb=None):
        def callback(contact_infos, memberships):
            self.__update_contact(pending_contact, memberships, contact_infos)
            self.__common_callback('contact-accepted', done_cb, pending_contact)
        ai = scenario.AcceptInviteScenario(self._ab, self._sharing,
                 (callback,),
                 (self.__common_errback, failed_cb))
        ai.account = pending_contact.account
        ai.network = pending_contact.network_id
        ai.memberships = pending_contact.memberships
        ai.add_to_contact_list = add_to_contact_list
        ai()

    def decline_contact_invitation(self, pending_contact, block=True,
            done_cb=None, failed_cb=None):
        def callback(memberships):
            pending_contact._set_memberships(memberships)
            self.__common_callback('contact-rejected', done_cb, pending_contact)
        di = scenario.DeclineInviteScenario(self._sharing,
                 (callback,),
                 (self.__common_errback, failed_cb))
        di.account = pending_contact.account
        di.network = pending_contact.network_id
        di.memberships = pending_contact.memberships
        di.block = block
        di()

    def add_messenger_contact(self, account, invite_display_name='',
            invite_message='', groups=[], network_id=NetworkID.MSN,
            auto_allow=True, done_cb=None, failed_cb=None):
        def callback(contact_infos, memberships):
            c = self.__build_or_update_contact(account, network_id,
                    memberships, contact_infos)
            self.__common_callback('messenger-contact-added', done_cb, c)
            for group in groups:
                self.add_contact_to_group(group, c)

        contact = self.search_contact(account, network_id)
        old_memberships = (contact and contact.memberships) or Membership.NONE

        if contact is not None and contact.is_mail_contact():
            self.upgrade_mail_contact(contact, groups, done_cb, failed_cb)
        elif contact is None or not contact.is_member(Membership.FORWARD):
            scenario_class = MessengerContactAddScenario
            s = scenario_class(self._ab,
                    (callback,),
                    (self.__common_errback, failed_cb))
            s.account = account
            s.network_id = network_id
            s.memberships = old_memberships
            s.auto_manage_allow_list = auto_allow
            s.invite_display_name = invite_display_name
            s.invite_message = invite_message
            s()

    def upgrade_mail_contact(self, contact, groups=[],
            done_cb=None, failed_cb=None):
        def callback():
            contact._add_membership(Membership.ALLOW)
            for group in groups:
                self.add_contact_to_group(group, contact)
            self.__common_callback(None, done_cb)

        up = scenario.ContactUpdatePropertiesScenario(self._ab,
                (callback,), (self.__common_errback, failed_cb))
        up.contact_guid = contact.id
        up.contact_properties = { 'is_messenger_user' : True }
        up.enable_allow_list_management = True
        up()

    def delete_contact(self, contact, done_cb=None, failed_cb=None):
        def callback():
            contact._remove_membership(Membership.FORWARD)
            contact._reset()
            self.__common_callback('contact-deleted', done_cb, contact)
            if contact.memberships == Membership.NONE:
                self.contacts.discard(contact)

        dc = scenario.ContactDeleteScenario(self._ab,
                (callback,),
                (self.__common_errback, failed_cb))
        dc.contact_guid = contact.id
        dc()

    def update_contact_infos(self, contact, infos, done_cb=None, failed_cb=None):
        def callback():
            contact._server_infos_changed(infos)
            self.__common_callback(None, done_cb)
        up = scenario.ContactUpdatePropertiesScenario(self._ab,
                (callback,),
                (self.__common_errback, failed_cb))
        up.contact_guid = contact.id
        up.contact_properties = infos
        up()

    def block_contact(self, contact, done_cb=None, failed_cb=None):
        def callback(memberships):
            contact._set_memberships(memberships)
            self.__common_callback('contact-blocked', done_cb, contact)
        bc = scenario.BlockContactScenario(self._sharing,
                (callback,),
                (self.__common_errback, failed_cb))
        bc.account = contact.account
        bc.network = contact.network_id
        bc.membership = contact.memberships
        bc()

    def unblock_contact(self, contact, done_cb=None, failed_cb=None):
        def callback(memberships):
            contact._set_memberships(memberships)
            self.__common_callback('contact-unblocked', done_cb, contact)
        uc = scenario.UnblockContactScenario(self._sharing,
                (callback,),
                (self.__common_errback, failed_cb))
        uc.account = contact.account
        uc.network = contact.network_id
        uc.membership = contact.memberships
        uc()

    def allow_contact(self, account, network_id=NetworkID.MSN,
            done_cb=None, failed_cb=None):
        def callback(memberships):
            c = self.__build_or_update_contact(account, network_id, memberships)
            self.__common_callback('contact-allowed', done_cb, c)

        contact = self.search_contact(account, network_id)
        old_memberships = (contact and contact.memberships) or Membership.NONE

        if old_memberships & Membership.BLOCK:
            self.unblock_contact(contact, done_cb, failed_cb)
        else:
            ac = scenario.AllowContactScenario(self._sharing,
                     (callback,),
                     (self.__common_errback, failed_cb))
            ac.account = account
            ac.network = network_id
            ac.membership = old_memberships
            ac()

    def disallow_contact(self, contact, done_cb=None, failed_cb=None):
        def callback(memberships):
            contact._remove_membership(Membership.ALLOW)
            self.__common_callback('contact-disallowed', done_cb, contact)
            if contact.memberships == Membership.NONE:
                self.contacts.discard(contact)

        dc = scenario.DisallowContactScenario(self._sharing,
                (callback,),
                (self.__common_errback, failed_cb))
        dc.account = contact.account
        dc.network = contact.network_id
        dc.membership = contact.memberships
        dc()

    def add_group(self, group_name, done_cb=None, failed_cb=None):
        def callback(group_id):
            group = profile.Group(group_id, group_name)
            self.groups.add(group)
            self.__common_callback('group-added', done_cb, group)
        ag = scenario.GroupAddScenario(self._ab,
                (callback,),
                (self.__common_errback, failed_cb))
        ag.group_name = group_name
        ag()

    def delete_group(self, group, done_cb=None, failed_cb=None):
        def callback():
            for contact in self.contacts:
                contact._delete_group_ownership(group)
            self.groups.discard(group)
            self.__common_callback('group-deleted', done_cb, group)
        dg = scenario.GroupDeleteScenario(self._ab,
                (callback,),
                (self.__common_errback, failed_cb))
        dg.group_guid = group.id
        dg()

    def rename_group(self, group, new_name, done_cb=None, failed_cb=None):
        def callback():
            group._name = new_name
            self.__common_callback('group-renamed', done_cb, group)
        rg = scenario.GroupRenameScenario(self._ab,
                (callback,),
                (self.__common_errback, failed_cb))
        rg.group_guid = group.id
        rg.group_name = new_name
        rg()

    def add_contact_to_group(self, group, contact, done_cb=None, failed_cb=None):
        def callback():
            contact._add_group_ownership(group)
            self.__common_callback('group-contact-added', done_cb, group, contact)
        ac = scenario.GroupContactAddScenario(self._ab,
                (callback,),
                (self.__common_errback, failed_cb))
        ac.group_guid = group.id
        ac.contact_guid = contact.id
        ac()

    def delete_contact_from_group(self, group, contact,
            done_cb=None, failed_cb=None):
        def callback():
            contact._delete_group_ownership(group)
            self.__common_callback('group-contact-deleted', done_cb, group, contact)
        dc = scenario.GroupContactDeleteScenario(self._ab,
                (callback,),
                (self.__common_errback, failed_cb))
        dc.group_guid = group.id
        dc.contact_guid = contact.id
        dc()
    # End of public API

    def __build_contact(self, contact=None, memberships=Membership.NONE):
        external_email = None
        is_messenger_enabled = False
        for email in contact.Emails:
            if email.Type == ContactEmailType.EXTERNAL:
                external_email = email
            if email.IsMessengerEnabled:
                is_messenger_enabled = True

        if (not contact.IsMessengerUser) and (external_email is not None):
            display_name = contact.DisplayName
            if not display_name:
                display_name = external_email.Email

            if not is_messenger_enabled:
                memberships = Membership.NONE

            c = profile.Contact(contact.Id,
                    NetworkID.EXTERNAL,
                    external_email.Email.encode("utf-8"),
                    display_name.encode("utf-8"),
                    contact.CID,
                    memberships,
                    contact.Type)
            contact_infos = contact.contact_infos
            c._server_infos_changed(contact_infos)

            for group in self.groups:
                if group.id in contact.Groups:
                    c._add_group_ownership(group)

            return c

        elif contact.PassportName == "":
            # FIXME : mobile phone and mail contacts here
            return None
        else:
            display_name = contact.DisplayName
            if not display_name:
                display_name = contact.QuickName
            if not display_name:
                display_name = contact.PassportName

            if not contact.IsMessengerUser:
                memberships = Membership.NONE
            c = profile.Contact(contact.Id,
                    NetworkID.MSN,
                    contact.PassportName.encode("utf-8"),
                    display_name.encode("utf-8"),
                    contact.CID,
                    memberships)
            contact_infos = contact.contact_infos
            c._server_infos_changed(contact_infos)

            for group in self.groups:
                if group.id in contact.Groups:
                    c._add_group_ownership(group)

            return c
        return None

    def __update_contact(self, contact, memberships=None, infos=None):
        contact.freeze_notify()
        if memberships is not None:
            contact._set_memberships(memberships)
        if infos is not None:
            contact._id = infos.Id
            contact._cid = infos.CID
            contact._display_name = infos.DisplayName
            contact._server_infos_changed(infos.contact_infos)
            for group in self.groups:
                if group.id in infos.Groups:
                    contact._add_group_ownership(group)
        contact.thaw_notify()

    def __build_or_update_contact(self, account, network_id=NetworkID.MSN,
            memberships=None, infos=None):
        contact = self.search_contact(account, network_id)
        if contact is not None:
            self.__update_contact(contact, memberships, infos)
        else:
            if infos is None:
                display_name = ""
                contact = profile.Contact(None, network_id, account,
                        display_name, memberships)
            else:
                contact = self.__build_contact(infos, memberships)
            self.contacts.add(contact)
            self.emit('contact-added', contact)
        return contact

    def __update_memberships(self, members):
        role_to_membership = {
            "Allow"   : Membership.ALLOW,
            "Block"   : Membership.BLOCK,
            "Reverse" : Membership.REVERSE,
            "Pending" : Membership.PENDING
        }

        for member in members:
            if isinstance(member, sharing.PassportMember):
                network = NetworkID.MSN
            elif isinstance(member, sharing.EmailMember):
                network = NetworkID.EXTERNAL
            else:
                continue

            contact = self.search_contact(member.Account, network)
            new_contact = False
            if contact is None:
                new_contact = True
                cid = getattr(member, "CID", None)
                account = member.Account.encode("utf-8")
                display_name = (member.DisplayName or member.Account).encode("utf-8")
                msg = member.Annotations.get('MSN.IM.InviteMessage', u'')
                c = profile.Contact(None, network, account, display_name, cid)
                c._server_attribute_changed('invite_message', msg.encode("utf-8"))
                self.contacts.add(c)
                contact = c

            for role in member.Roles:
                membership = role_to_membership.get(role, None)
                if membership is None:
                    raise NotImplementedError("Unknown Membership:" + membership)
                contact._add_membership(membership)

            if new_contact and self.state == AddressBookState.SYNCHRONIZED:
                self.emit('contact-added', contact)

    # Callbacks
    def __common_callback(self, signal, callback, *args):
        if signal is not None:
            self.emit(signal, *args)
        if callback is not None:
            cb_args = args + callback[1:]
            callback[0](*cb_args)

    def __common_errback(self, error_code, *args):
        callback = args[-1]
        args = args[:-1]
        if callback is not None:
            cb_args = args + callback[1:]
            callback[0](error_code, *cb_args)
        if error_code == AddressBookError.UNKNOWN:
            # known errors are not fatal, just ignore them
            self.emit('error', error_code)

gobject.type_register(AddressBook)

if __name__ == '__main__':
    def get_proxies():
        import urllib
        proxies = urllib.getproxies()
        result = {}
        if 'https' not in proxies and \
                'http' in proxies:
            url = proxies['http'].replace("http://", "https://")
            result['https'] = papyon.Proxy(url)
        for type, url in proxies.items():
            if type == 'no': continue
            if type == 'https' and url.startswith('http://'):
                url = url.replace('http://', 'https://', 1)
            result[type] = papyon.Proxy(url)
        return result

    import sys
    import getpass
    import signal
    import gobject
    import logging
    from papyon.service.SingleSignOn import *
    from papyon.service.description.AB.constants import ContactGeneral

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

    def address_book_state_changed(address_book, pspec):
        if address_book.state == AddressBookState.SYNCHRONIZED:
            for group in address_book.groups:
                print "Group : %s " % group.name

            for contact in address_book.contacts:
                print "Contact : %s (%s) %s" % \
                    (contact.account,
                     contact.display_name,
                     contact.network_id)

            print address_book.contacts[0].account
            address_book.update_contact_infos(address_book.contacts[0], {ContactGeneral.FIRST_NAME : "lolibouep"})

            #address_book._check_pending_invitations()
            #address_book.accept_contact_invitation(address_book.pending_contacts.pop())
            #print address_book.pending_contacts.pop()
            #address_book.accept_contact_invitation(address_book.pending_contacts.pop())
            #address_book.add_group("ouch2")
            #address_book.add_group("callback test6")
            #group = address_book.groups.values()[0]
            #address_book.delete_group(group)
            #address_book.delete_group(group)
            #address_book.rename_group(address_book.groups.values()[0], "ouch")
            #address_book.add_contact_to_group(address_book.groups.values()[1],
            #                                  address_book.contacts[0])
            #contact = address_book.contacts[0]
            #address_book.delete_contact_from_group(address_book.groups.values()[0],
            #                                       contact)
            #address_book.delete_contact_from_group(address_book.groups.values()[0],
            #                                       contact)
            #address_book.block_contact(address_book.contacts.search_by_account('papyon.rewrite@yahoo.com')[0])
            #address_book.block_contact(address_book.contacts.search_by_account('papyon.rewrite@yahoo.com')[0])
            #address_book.unblock_contact(address_book.contacts[0])
            #address_book.block_contact(address_book.contacts[0])
            #contact = address_book.contacts[2]
            #address_book.delete_contact(contact)
            #address_book.delete_contact(contact)
            #g=list(address_book.groups)
            #address_book.add_messenger_contact("wikipedia-bot@hotmail.com",groups=g)

            #for i in range(5):
            #    address_book.delete_contact(address_book.contacts[i])
            #address_book.add_messenger_contact("johanssn.prieur@gmail.com")

    def messenger_contact_added(address_book, contact):
        print "Added contact : %s (%s) %s %s" % (contact.account,
                                                 contact.display_name,
                                                 contact.network_id,
                                                 contact.memberships)

    sso = SingleSignOn(account, password, proxies=get_proxies())
    address_book = AddressBook(sso, proxies=get_proxies())
    address_book.connect("notify::state", address_book_state_changed)
    address_book.connect("messenger-contact-added", messenger_contact_added)
    address_book.sync()

    while mainloop.is_running():
        try:
            mainloop.run()
        except KeyboardInterrupt:
            mainloop.quit()
