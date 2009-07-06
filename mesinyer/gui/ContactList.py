# -*- coding: utf-8 -*-

#   This file is part of emesene.
#
#    Emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
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
'''a abstract object that define the API of a contact list and some behavior'''
import protocol.Contact
import protocol.status as status

import Signal

class ContactList(object):
    '''an abstract class that defines the api that the contact list should
    have'''

    def __init__(self, session, dialog):
        '''class constructor'''

        # define the class signals
        # the param is the contact object
        self.contact_selected = Signal.Signal()
        self.group_selected = Signal.Signal()
        self.contact_menu_selected = Signal.Signal()
        self.group_menu_selected = Signal.Signal()

        self.contacts = session.contacts
        self.groups = session.groups
        self.session = session
        self.dialog = dialog

        self.group_state = {}

        self.session.config.get_or_set('b_order_by_group', True)
        self.session.config.get_or_set('b_show_nick', True)
        self.session.config.get_or_set('b_show_empty_groups', False)
        self.session.config.get_or_set('b_show_offline', False)
        self.session.config.get_or_set('b_show_blocked', False)

        avatar_width = self.session.config.get_or_set('i_avatar_width', 48)
        avatar_height = self.session.config.get_or_set('i_avatar_height', 48)

        self.set_image_size(avatar_width, avatar_height)

        # self.order_by_status is a property that returns the inverse
        # value as the one of self.order_by_group, the setter, set the inverse
        # value to this attribute
        self.order_by_group = self.session.config.b_order_by_group
        self.show_nick = self.session.config.b_show_nick
        self._show_empty_groups = self.session.config.b_show_empty_groups
        self._show_offline = self.session.config.b_show_offline
        self._show_blocked = self.session.config.b_show_blocked

        self._filter_text = ''

        # valid values:
        # + NICK
        # + ACCOUNT
        # + DISPLAY_NAME (alias if available, or nick if available or mail)
        # + STATUS
        # + MESSAGE
        self.nick_template = \
            '%DISPLAY_NAME%\n%ACCOUNT%\n(%STATUS%) - %MESSAGE%'
        # valid values:
        # + NAME
        # + ONLINE_COUNT
        # + TOTAL_COUNT
        self.group_template = '%NAME% (%ONLINE_COUNT%/%TOTAL_COUNT%)'

    def _get_order_by_status(self):
        '''return the value of order by status'''
        return not self.order_by_group

    def _set_order_by_status(self, value):
        '''set the value of order by status'''
        self.order_by_group = not value

    order_by_status = property(fget=_get_order_by_status,
        fset=_set_order_by_status)

    def _get_order_by_group(self):
        '''return the value of order by group'''
        return self._order_by_group

    def _set_order_by_group(self, value):
        '''set the value of order by group'''
        self._order_by_group = value
        self.session.config.b_order_by_group = value

    order_by_group = property(fget=_get_order_by_group,
        fset=_set_order_by_group)

    def _get_show_offline(self):
        '''return the value of self._show_offline'''
        return self._show_offline

    def _set_show_offline(self, value):
        '''set the value of self._show_offline to value and call to
        self.refilter()'''
        self._show_offline = value
        self.session.config.b_show_offline = self._show_offline
        self.refilter()

    show_offline = property(fget=_get_show_offline, fset=_set_show_offline)

    def _get_show_blocked(self):
        '''return the value of self._show_blocked'''
        return self._show_blocked

    def _set_show_blocked(self, value):
        '''set the value of self._show_blocked to value and call to
        self.refilter()'''
        self._show_blocked = value
        self.session.config.b_show_blocked = self._show_blocked
        self.refilter()

    show_blocked = property(fget=_get_show_blocked, fset=_set_show_blocked)

    def _get_show_empty_groups(self):
        '''return the value of show_emptry_groups'''
        return self._show_empty_groups

    def _set_show_empty_groups(self, value):
        '''set the value of self._show_empty_groups to value and call to
        self.refilter()'''
        self._show_empty_groups = value
        self.session.config.b_show_empty_groups = value
        self.refilter()

    show_empty_groups = property(fget=_get_show_empty_groups,
        fset=_set_show_empty_groups)

    def _get_filter_text(self):
        '''return the filter_text value'''
        return self._filter_text

    def _set_filter_text(self, value):
        '''set the filter_text value'''
        self._filter_text = value
        self.refilter()

    filter_text = property(fget=_get_filter_text, fset=_set_filter_text)

    def format_nick(self, contact):
        '''replace the appearance of the template vars using the values of
        the contact
        # valid values:
        # + NICK
        # + ACCOUNT
        # + DISPLAY_NAME (alias if available, or nick if available or mail)
        # + STATUS
        # + MESSAGE
        # + BLOCKED
        '''
        template = self.nick_template
        template = template.replace('%NICK%', contact.nick)
        template = template.replace('%ACCOUNT%', contact.account)
        template = template.replace('%MESSAGE%', contact.message)
        template = template.replace('%STATUS%', status.STATUS[contact.status])
        template = template.replace('%DISPLAY_NAME%', contact.display_name)

        blocked_text = ''
        if contact.blocked:
            blocked_text = '(blocked)'

        template = template.replace('%BLOCKED%', blocked_text)

        return template

    def format_group(self, group):
        '''replace the appearance of the template vars using the values of
        the group
        # valid values:
        # + NAME
        # + ONLINE_COUNT
        # + TOTAL_COUNT
        '''
        contacts = self.contacts.get_contacts(group.contacts)
        (online, total) = self.contacts.get_online_total_count(contacts)
        template = self.group_template
        template = template.replace('%NAME%', group.name)
        template = template.replace('%ONLINE_COUNT%', str(online))
        template = template.replace('%TOTAL_COUNT%', str(total))

        return template

    def refilter(self):
        '''refilter the values according to the value of self.filter_text'''
        raise NotImplementedError()

    def is_group_selected(self):
        '''return True if a group is selected'''
        raise NotImplementedError()

    def is_contact_selected(self):
        '''return True if a contact is selected'''
        raise NotImplementedError()

    def get_group_selected(self):
        '''return a group object if there is a group selected, None otherwise
        '''
        raise NotImplementedError()

    def get_contact_selected(self):
        '''return a contact object if there is a group selected, None otherwise
        '''
        raise NotImplementedError()

    def add_group(self, group):
        '''add a group to the contact list'''
        raise NotImplementedError()

    def remove_group(self, group):
        '''remove a group from the contact list'''
        raise NotImplementedError()

    def add_contact(self, contact, group=None):
        '''add a contact to the contact list, add it to the group if
        group is not None'''
        raise NotImplementedError()

    def remove_contact(self, contact, group=None):
        '''remove a contact from the specified group, if group is None
        then remove him from all groups'''
        raise NotImplementedError()

    def set_image_size(self, width, height):
        """set the size of the avatars on the contact list
        """
        raise NotImplementedError()

    def fill(self, clear=True):
        '''fill the contact list with the contacts and groups from
        self.contacts and self.groups'''
        if clear:
            self.clear()

        for group in self.groups.values():
            # get a list of contact objects from a list of accounts
            contacts = self.contacts.get_contacts(group.contacts)
            self.add_group(group)
            for contact in contacts:
                self.add_contact(contact, group)

        for contact in self.contacts.get_no_group():
            self.add_contact(contact)

    def clear(self):
        '''clear the contact list'''
        raise NotImplementedError()

    def update_contact(self, contact):
        '''update the data of contact'''
        raise NotImplementedError()

    def update_group(self, group):
        '''update the data of group'''
        raise NotImplementedError()

    def set_group_state(self, group, state):
        '''expand group id state is True, collapse it if False'''
        raise NotImplementedError()

    def expand_collapse_groups(self):
        '''expand and collapse the groups according to the state of the
        group'''
        for (group, state) in self.group_state.iteritems():
            self.set_group_state(group, state)

    def on_group_collapsed(self, group):
        '''called when a group is collapsed, update the status of the
        groups'''
        self.group_state.update({group.name:False})

    def on_group_expanded(self, group):
        '''called when a group is expanded, update the status of the
        groups'''
        self.group_state.update({group.name:True})

    def compare_groups(self, group1, group2, order1=0, order2=0):
        '''compare two groups and return 1 if group1 should go first, 0
        if equal, -1 if group2 should go first, use order1 and order2 to
        override the group sorting (the user can set the values on these to
        have custom ordering)'''

        override = cmp(order2, order1)

        if override != 0:
            return override

        return cmp(group1.name, group2.name)

    def compare_contacts(self, contact1, contact2, order1=0, order2=0):
        '''compare two contacts and return 1 if contact1 should go first, 0
        if equal and -1 if contact2 should go first, use order1 and order2 to
        override the group sorting (the user can set the values on these to
        have custom ordering)'''

        override = cmp(order2, order1)

        if override != 0:
            return override

        result = cmp(status.ORDERED.index(contact1.status),
            status.ORDERED.index(contact2.status))

        if result != 0:
            return result

        if self.order_by_status:
            return cmp(contact1.display_name, contact2.display_name)

        if len(contact1.groups) == 0:
            if len(contact2.groups) == 0:
                return cmp(contact1.display_name, contact2.display_name)
            else:
                return -1
        elif len(contact2.groups) == 0:
            return 1
        else:
            return cmp(contact1.display_name, contact2.display_name)

