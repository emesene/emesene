'''a module to handle contacts'''
# -*- coding: utf-8 -*-

#    This file is part of emesene.
#
#    emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    emesene is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with emesene; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import status

from Contact import Contact

class ContactManager(object):
    def __init__(self, account):
        self.contacts = {}
        self.reverse = {}
        self.pending = {}

        self.me = Contact(account)

    def exists(self, account):
        '''check if the account is on self.contacts, return True if exists'''
        return account in self.contacts

    def get(self, account):
        '''return a contact from an account'''
        return self.contacts.get(account, None)

    def safe_get(self, account):
        '''return a contact from an account if present, otherwise create one'''
        contact = self.contacts.get(account)
        if contact is None:
            contact = Contact(account)
        return contact

    # actions on our contact
    def get_no_group(self):
        '''return a list of contacts that dont belong to any group'''
        return [contact for contact in self.contacts.values() \
            if not contact.groups]

    def get_contacts(self, accounts):
        '''return a list of contact objects from a list of accounts
        if in_reverse is True, check that the account is also on the reverse
        list'''
        return [self.contacts[account] for account in accounts if account \
            in self.contacts]

    def get_sorted_list_by_status(self, contacts=None):
        '''return a dict with status.* (OFFLINE, ONLINE etc) as key and
        a list of contact objects as value, you can use then
        status.ORDERED to cycle over the keys.
        The contacts are sorted inside the status by display_name.
        if contacts is None, then use the internal list of contacts
        contacts should be a list of contact objects'''
        sorted_dict = {}
        contacts = contacts or self.contacts.values()

        for stat in status.ORDERED:
            sorted_dict[stat] = [contact for contact in contacts \
                if contact.status == stat]

            sorted_dict[stat].sort(cmp=lambda x, y: cmp(x.display_name,
                y.display_name))

        return sorted_dict

    def get_sorted_list_by_group(self, groups, sort_by_status=False):
        '''return a dict with group names as keys and a list of sorted
        contacts as value, sort them according to display_name if
        sort_by_status is False, and by status and display_name if
        it's True'''
        groups.sort()
        sorted_dict = {}

        for group in groups:
            contacts = [contact for contact in self.contacts.values() \
                if group in contact.groups]

            if sort_by_status:
                sorted_dict[group] = self.get_sorted_list_by_status(contacts)
            else:
                contacts.sort(cmp=lambda x, y: cmp(x.display_name,
                    y.display_name))
                sorted_dict[group] = contacts

        return sorted_dict

    def get_by_domain(self):
        '''return a dict with list of accounts as values and domain
        as key'''
        domains = {}

        for contact in self.contacts:
            (user, domain) = contact.split('@')
            if domain in domains:
                domains[domain].append(user)
            else:
                domains[domain] = [user]

        return domains

    def get_adls(self):
        '''return a list of adl strings'''

        first = True
        length = 0
        adls = []
        adl = []
        tag = ''

        domain = None
        for (domain, accounts) in self.get_by_domain().iteritems():
            # if it's not the first time we must add the adl of the
            # lsat domain in the adls list
            if adl:
                adl.append('</d>')
                adls.append((domain, length, adl))

                adl = []
                length = 0

            # create the domain start tag
            tag = '<d n="%s">' % (domain,)
            adl.append(tag)

            length += len(tag)

            # for each account we add a tag
            for account in accounts:
                email = account + '@' + domain

                if self.contacts[email].blocked:
                    l = '5'
                else:
                    l = '3'

                tag = '<c n="%s" l="%s" t="1" />' % (account, l)
                adl.append(tag)
                length += len(tag)

                # if we reach the size limit we append this
                # list to the adls list and start another
                # on the same domain
                if length > 5000:
                    adl.append('</d>')
                    adls.append((domain, length, adl))

                    length = 0
                    adl = []

                    tag = '<d n="%s">' % (domain,)
                    adl.append(tag)

                    length += len(tag)

        if domain is not None:
            adl.append('</d>')
            adls.append((domain, length, adl))

        result = []
        partial = []
        total_length = 0

        for (domain, length, adl) in adls:
            if not partial:
                if first:
                    adl.insert(0, '<ml l="1">')
                    first = False
                else:
                    adl.insert(0, '<ml>')

            partial.append(''.join(adl))
            total_length += length

            if total_length > 5000:
                partial.append('</ml>')

                result.append(''.join(partial))
                partial = []
                total_length = 0

        if partial:
            partial.append('</ml>')
            result.append(''.join(partial))

        return result

    def get_online_list(self, contacts=None):
        '''return a list of non offline contacts'''
        contacts = contacts or self.contacts.values()

        return [contact for contact in contacts \
                if contact.status != status.OFFLINE]

    def get_online_total_count(self, contacts):
        '''return a tuple with two values, the first is the number of
        non offline contacts on the list, the secont is the total number
        of contacts'''
        total = len(contacts)
        online = len([contact for contact in contacts \
            if contact.status != status.OFFLINE])

        return (online, total)
