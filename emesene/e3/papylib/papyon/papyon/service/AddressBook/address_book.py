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
from papyon.profile import Membership, NetworkID, Contact
from papyon.util.decorator import rw_property
from papyon.profile import ContactType
from papyon.service.AddressBook.constants import *
from papyon.service.description.AB.constants import *
from papyon.service.AddressBook.scenario.contacts import *
from papyon.util.async import run

import gobject

import logging
logger = logging.getLogger('papyon.service.address_book')


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

            "sync"  : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                ()),

            "contact-added"           : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),
            "messenger-contact-added" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),

            "contact-pending"         : (gobject.SIGNAL_RUN_FIRST,
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
        self.__frozen = 0
        self.__signal_queue = []

        self._ab = ab.AB(sso, client, proxies)
        self._sharing = sharing.Sharing(sso, proxies)
        self._client = client

        self.__state = AddressBookState.NOT_SYNCHRONIZED

        self.groups = set()
        self.contacts = AddressBookStorage()
        self._profile = None

        self.connect_after('contact-deleted', lambda self, contact: contact._reset())

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

    def sync(self, delta_only=False, done_cb=None):
        # Avoid race conditions.
        if self._state in \
        (AddressBookState.INITIAL_SYNC, AddressBookState.RESYNC):
            return

        if self._state == AddressBookState.NOT_SYNCHRONIZED:
            self._state = AddressBookState.INITIAL_SYNC
        else:
            self._state = AddressBookState.RESYNC

        def callback(ab_storage, memberships):
            self.__log_sync_request(ab_storage, memberships)
            self.__freeze_address_book()
            self.__update_address_book(ab_storage)
            self.__update_memberships(memberships)
            self.__unfreeze_address_book()
            self._state = AddressBookState.SYNCHRONIZED
            self.__common_callback('sync', done_cb)

        sc = scenario.SyncScenario(self._ab, self._sharing,
                (callback,),
                (self.__common_errback,),
                delta_only)
        sc()

    # Public API
    def search_contact(self, account, network_id):
        if account.lower() == self._client.profile.account.lower() and \
                network_id == NetworkID.MSN:
            return self._client.profile

        contacts = self.contacts.search_by_network_id(network_id).\
                search_by_account(account)
        if len(contacts) == 0:
            return None
        return contacts[0]

    def search_or_build_contact(self, account, network_id, display_name=None):
        contact = self.search_contact(account, network_id)
        if contact is None:
            if not display_name:
                display_name = account
            contact = profile.Contact(None, network_id, account, display_name)
        return contact

    def accept_contact_invitation(self, pending_contact, add_to_contact_list=True,
            done_cb=None, failed_cb=None):

        if not pending_contact.is_member(Membership.PENDING) \
        and pending_contact.is_member(Membership.REVERSE):
            return

        def callback(memberships, contact):
            self.__update_contact(contact, memberships)
            self.__common_callback('contact-accepted', done_cb, contact)

        def contact_added(pending_contact):
            ai = scenario.AcceptInviteScenario(self._sharing,
                     (callback, pending_contact),
                     (self.__common_errback, failed_cb),
                     pending_contact.account,
                     pending_contact.memberships,
                     pending_contact.network_id)
            ai()

        if add_to_contact_list \
        and not pending_contact.memberships & Membership.FORWARD:
            self.add_messenger_contact(account=pending_contact.account,
                                       network_id=pending_contact.network_id,
                                       done_cb=(contact_added,))
        else:
            contact_added(pending_contact)

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

        def contact_added(was_hidden):
            new_contact = None
            for contact in self.contacts:
                if contact.account == account:
                    new_contact = contact
                    break
            if new_contact is not None:
                allowed_or_blocked = new_contact.memberships & \
                    (Membership.BLOCK | Membership.ALLOW)
                if auto_allow and not allowed_or_blocked:
                    new_contact._add_membership(Membership.ALLOW)
                if not was_hidden:
                    new_contact._remove_membership(Membership.PENDING)
                if new_contact.id != Contact.BLANK_ID:
                    if not new_contact.is_member(Membership.PENDING):
                        new_contact._add_membership(Membership.FORWARD)
                    self.__common_callback('messenger-contact-added',
                                           done_cb, new_contact)
                for group in groups:
                    self.add_contact_to_group(group, new_contact)
            self.__unfreeze_address_book()

        def sync(contact_guid, was_hidden=False):
            self.__freeze_address_book()
            self.sync(True, (contact_added, was_hidden))

        contact = self.search_contact(account, network_id)

        if contact is self._client.profile:
            return # can't add ourself to the address book

        old_memberships = (contact and contact.memberships) or Membership.NONE

        if contact is not None and contact.is_mail_contact():
            self.upgrade_mail_contact(contact, groups, done_cb, failed_cb)
        elif contact is None or not contact.is_member(Membership.FORWARD):
            scenario_class = MessengerContactAddScenario
            s = scenario_class(self._ab,
                    (sync,),
                    (self.__common_errback, failed_cb),
                    account, network_id)
            s.auto_manage_allow_list = auto_allow
            s.invite_display_name = invite_display_name
            s.invite_message = invite_message
            s()

    def upgrade_mail_contact(self, contact, groups=[],
            done_cb=None, failed_cb=None):
        logger.info('upgrade mail contact: %s' % str(contact))
        def callback():
            contact._add_membership(Membership.ALLOW)
            for group in groups:
                self.add_contact_to_group(group, contact)
            self.__common_callback(None, done_cb, contact)

        up = scenario.ContactUpdatePropertiesScenario(self._ab,
                (callback,), (self.__common_errback, failed_cb))
        up.contact_guid = contact.id
        up.contact_properties = { 'is_messenger_user' : True }
        up.enable_allow_list_management = True
        up()

    def delete_contact(self, contact, done_cb=None, failed_cb=None):
        def callback():
            self.__remove_contact(contact, Membership.FORWARD, done_cb)

        dc = scenario.ContactDeleteScenario(self._sharing,
                self._ab,
                (callback,),
                (self.__common_errback, failed_cb))
        dc.contact_guid = contact.id
        dc.account = contact.account
        dc.memberships = contact.memberships
        dc.network = contact.network_id
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
            self.__remove_group(group, done_cb)
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

    def emit(self, detailed_signal, *args, **kwargs):
        if self.__frozen:
            self.__signal_queue.append((detailed_signal, args, kwargs))
        else:
            super(AddressBook, self).emit(detailed_signal, *args, **kwargs)

    # End of public API

    def __freeze_address_book(self):
        """Disable all AB notifications and events until we unfreeze."""
        if not self.__frozen:
            self.freeze_notify()
            for group in self.groups:
                group.freeze_notify()
            for contact in self.contacts:
                contact.freeze_notify()
        self.__frozen += 1

    def __unfreeze_address_book(self):
        """Emit all queued AB notifications and events."""
        if self.__frozen:
            self.__frozen -= 1
            if not self.__frozen:
                for contact in self.contacts:
                    contact.thaw_notify()
                for group in self.groups:
                    group.thaw_notify()
                self.thaw_notify()
                for signal in self.__signal_queue:
                    super(AddressBook, self).emit(signal[0], *signal[1], **signal[2])
                self.__signal_queue = []

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
            if infos.DisplayName:
                contact._display_name = infos.DisplayName
            if not isinstance(contact, profile.Profile):
                contact._server_infos_changed(infos.contact_infos)
                for group in self.groups:
                    if group.id in infos.Groups:
                        contact._add_group_ownership(group)
                    if group.id in infos.DeletedGroups:
                        contact._delete_group_ownership(group)
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

    def __remove_contact(self, contact, removed_memberships, done_cb=None):
        emit_deleted = False
        if removed_memberships & Membership.FORWARD \
        and contact.is_member(Membership.FORWARD):
            emit_deleted = True
        contact._remove_membership(removed_memberships)
        # Do not use __common_callback() here to avoid race
        # conditions with the event-triggered contact._reset().
        run(done_cb, contact)
        if contact.memberships == Membership.NONE:
            self.contacts.discard(contact)
        if emit_deleted:
            self.emit('contact-deleted', contact)

    def __remove_group(self, group, done_cb=None):
        for contact in self.contacts:
            contact._delete_group_ownership(group)
        self.groups.discard(group)
        self.__common_callback('group-deleted', done_cb, group)

    def __log_sync_request(self, ab_storage, memberships):
        myself = '???' if not self._profile else self._profile.account
        contacts = ['%s-%s' % ('D' if contact.Deleted else 'A',
                                   contact.PassportName)
                        for contact in ab_storage.contacts]
        groups = ['%s-%s' % ('D' if group.Deleted else 'A',
                                   group.Name)
                      for group in ab_storage.groups]
        members = []
        for member in memberships:
            member_repr = member.Account
            for role, deleted in member.Roles.items():
                member_repr += ' %s-%s' % ('D' if deleted else 'A', role)
            members.append(member_repr)
        logger.info('[%s] Received sync request:\n'
                     '...contacts: %s\n'
                     '...groups: %s\n'
                     '...memberships: %s'
                     % (myself, str(contacts), str(groups), str(members)))

    def __update_address_book(self, ab_storage):
        for group_infos in ab_storage.groups:
            group = None
            for g in self.groups:
                if g.id == group_infos.Id:
                    group = g
                    break

            if group_infos.Deleted:
                if group is not None:
                    self.__remove_group(group)
            else:
                group_name = group_infos.Name.encode("utf-8")
                if group:
                    group._server_property_changed('name', group_name)
                else:
                    group = profile.Group(group_infos.Id, group_name)
                    group.freeze_notify()
                    self.groups.add(group)
                    if self.state != AddressBookState.INITIAL_SYNC:
                        self.emit('group-added', group)

        for contact_infos in ab_storage.contacts:
            new_contact = self.__build_contact(contact_infos, Membership.FORWARD)
            if new_contact is None:
                continue
            new_contact.freeze_notify()

            contact = self.search_contact(new_contact.account,
                                          new_contact.network_id)

            if contact_infos.Type == ContactType.ME:
                if self._profile is None:
                    self._profile = new_contact
                else:
                    self.__update_contact(self._profile, infos=contact_infos)
                continue

            if contact_infos.Deleted:
                if contact:
                    self.__remove_contact(contact, Membership.FORWARD)
            else:
                new_contact_added = False
                if not contact \
                or contact.id == Contact.BLANK_ID:
                    new_contact_added = True

                if contact:
                    self.__update_contact(contact, infos=contact_infos)
                else:
                    contact = new_contact
                    self.contacts.add(contact)

                if new_contact_added and not isinstance(contact, profile.Profile):
                    if not contact.is_member(Membership.PENDING):
                        contact._add_membership(Membership.FORWARD)
                    if self.state != AddressBookState.INITIAL_SYNC:
                        self.emit('contact-added', contact)

    def __update_memberships(self, members):
        role_to_membership = {
            "Allow"   : Membership.ALLOW,
            "Block"   : Membership.BLOCK,
            "Reverse" : Membership.REVERSE,
            "Pending" : Membership.PENDING
        }

        membership_conflicts = {
            Membership.ALLOW: Membership.BLOCK,
            Membership.BLOCK: Membership.ALLOW,
            Membership.FORWARD: Membership.PENDING,
            Membership.PENDING: Membership.FORWARD
        }

        for member in members:
            if isinstance(member, sharing.PassportMember):
                network = NetworkID.MSN
            elif isinstance(member, sharing.EmailMember):
                network = NetworkID.EXTERNAL
            else:
                continue

            if network == NetworkID.MSN and member.IsPassportNameHidden:
                continue # ignore contacts with hidden passport name

            contact = self.search_contact(member.Account, network)

            new_contact = False
            if contact is None:
                member_deleted = True
                for role, deleted in member.Roles.items():
                    if not deleted:
                        member_deleted = False
                        break
                if member_deleted:
                    continue

                new_contact = True
                cid = getattr(member, "CID", None)
                account = member.Account.encode("utf-8")
                display_name = (member.DisplayName or member.Account).encode("utf-8")
                msg = member.Annotations.get('MSN.IM.InviteMessage', u'')
                contact = profile.Contact(None, network, account, display_name, cid)
                contact.freeze_notify()
                contact._server_attribute_changed('invite_message', msg.encode("utf-8"))
                self.contacts.add(contact)

            if contact is self._client.profile:
                continue # don't update our own memberships

            # TODO: Check whether the contact's membership was changed
            # after member.LastChanged and if so ignore this member.
            # To implement this papyon has to save full membership info
            # for contacts.

            deleted_memberships = Membership.NONE
            for role, deleted in member.Roles.items():
                membership = role_to_membership.get(role, None)
                if membership is None:
                    raise NotImplementedError("Unknown Membership:" + membership)

                if deleted:
                    deleted_memberships |= membership
                else:
                    conflicting_memberships = membership_conflicts.get(membership, Membership.NONE)
                    contact._remove_membership(conflicting_memberships)
                    contact._add_membership(membership)

            if deleted_memberships:
                self.__remove_contact(contact, deleted_memberships)
            if self.state != AddressBookState.INITIAL_SYNC:
                if contact.is_member(Membership.PENDING):
                    self.emit('contact-pending', contact)
                if new_contact:
                    self.emit('contact-added', contact)

    # Callbacks
    def __common_callback(self, signal, callback, *args):
        if signal is not None:
            self.emit(signal, *args)
        run(callback, *args)

    def __common_errback(self, error, errback=None):
        run(errback, error)
        while self.__frozen:
            self.__unfreeze_address_book()
        self.emit('error', error)

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

            #address_book.sync(True)
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
