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
'''a gtk implementation of gui.ContactList'''
import gtk
import pango
import gobject

import gui
import utils
import dialog
import gui.ContactList
import protocol.status as status
from protocol.Group import Group
from protocol.Contact import Contact

class ContactList(gui.ContactList.ContactList, gtk.TreeView):
    '''a gtk implementation of gui.ContactList'''

    def __init__(self, contacts, groups):
        '''class constructor'''
        gui.ContactList.ContactList.__init__(self, contacts, groups, 
            dialog)
        gtk.TreeView.__init__(self)

        # the image (None for groups) the object (group or contact), 
        # the string to display and a boolean indicating if the pixbuff should
        # be shown (False for groups, True for contacts), the last is the status
        # image
        self._model = gtk.TreeStore(gtk.gdk.Pixbuf, object, str, bool,
            gtk.gdk.Pixbuf)
        self.model = self._model.filter_new(root=None)
        self.model.set_visible_func(self._visible_func)

        self._model.set_sort_func(1, self._sort_method)
        self._model.set_sort_column_id(1, gtk.SORT_ASCENDING)

        self.set_model(self.model)
        
        crt = gtk.CellRendererText()
        crt.set_property('ellipsize', pango.ELLIPSIZE_END)
        pbr = gtk.CellRendererPixbuf()
        pbr_status = gtk.CellRendererPixbuf()

        column = gtk.TreeViewColumn()
        column.set_expand(True)
        
        self.exp_column = gtk.TreeViewColumn()
        self.exp_column.set_max_width(16)       
        
        self.append_column(self.exp_column)
        self.append_column(column)
        self.set_expander_column(self.exp_column)
        
        column.pack_start(pbr, False)
        column.pack_start(crt, True)
        column.pack_start(pbr_status, False)
        
        column.add_attribute(pbr, 'pixbuf', 0)
        column.add_attribute(crt, 'markup', 2)
        column.add_attribute(pbr, 'visible', 3)
        column.add_attribute(pbr_status, 'visible', 3)
        column.add_attribute(pbr_status, 'pixbuf', 4)
        
        self.set_search_column(2)
        self.set_headers_visible(False)

        self.connect('row-activated', self._on_row_activated)
        self.connect('button-press-event' , self._on_button_press_event)
        
        # valid values:
        # + NICK
        # + ACCOUNT
        # + DISPLAY_NAME (alias if available, or nick if available or mail)
        # + STATUS
        # + MESSAGE
        self.nick_template = '%DISPLAY_NAME%\n'
        self.nick_template += '<span foreground="#AAAAAA" size="small">'
        self.nick_template += '%STATUS% %ACCOUNT%\n%MESSAGE%</span>'
        # valid values:
        # + NAME
        # + ONLINE_COUNT
        # + TOTAL_COUNT
        self.group_template = '<b>%NAME% (%ONLINE_COUNT%/%TOTAL_COUNT%)</b>'

    def _visible_func(self, model, _iter):
        '''return True if the row should be displayed according to the 
        value of the config'''
        obj = self._model[_iter][1]

        if not obj:
            return

        if type(obj) == Group:
            if not self.show_empty_groups:
                # get a list of contact objects from a list of accounts
                contacts = self.contacts.get_contacts(obj.contacts)
                if  self.contacts.get_online_total_count(contacts)[0] == 0:
                    return False

            return True

        # i think joining all the text from a user with a new line between
        # and searching on one string is faster (and the user cant add
        # a new line to the entry so..)
        if self._filter_text:
            if '\n'.join((obj.account, obj.alias, obj.nick, obj.message, 
                obj.account)).lower().find(self._filter_text) == -1:
                return False
            else:
                return True

        if not self.show_offline and obj.status == status.OFFLINE:
            return False

        return True

    def _sort_method(self, model, iter1, iter2, user_data=None):
        '''callback called to decide the order of the contacts'''

        obj1 = self._model[iter1][1]
        obj2 = self._model[iter2][1]

        if type(obj1) == Group and type(obj2) == Group:
            return self.compare_groups(obj1, obj2)
        elif type(obj1) == Contact and type(obj2) == Contact:
            return self.compare_contacts(obj1, obj2)
        elif type(obj1) == Group and type(obj2) == Contact:
            return -1
        else:
            return 1

    def _get_selected(self):
        '''return the selected row or None'''
        return self.model.convert_iter_to_child_iter(\
            self.get_selection().get_selected()[1])

    def _on_row_activated(self, treeview, path, view_column):
        '''callback called when the user selects a row'''
        group = self.get_group_selected()
        contact = self.get_contact_selected()

        if group:
            self.signal_emit('group-selected', group)
        elif contact:
            self.signal_emit('contact-selected', contact)
        else:
            print 'nothing selected?'

    def _on_button_press_event(self, treeview, event):
        '''callback called when the user press a button over a row
        chek if it's the roght button and emit a signal on that case'''
        if event.button == 3:
            paths = self.get_path_at_pos(int(event.x), int(event.y))
            
            if paths is None:
                print 'invalid path'
            elif len(paths) > 0:
                iterator = self.model.get_iter(paths[0])
                child_iter = self.model.convert_iter_to_child_iter(iterator)
                obj = self._model[child_iter][1]
               
                if type(obj) == Group:
                    self.signal_emit('group-menu-selected', obj)
                elif type(obj) == Contact:
                    self.signal_emit('contact-menu-selected', obj)
            else:
                print 'empty paths?'

    # overrided methods
    def refilter(self):
        '''refilter the values according to the value of self.filter_text'''
        self.model.refilter()

    def is_group_selected(self):
        '''return True if a group is selected'''
        return type(self._model[self._get_selected()][1]) == Group

    def is_contact_selected(self):
        '''return True if a contact is selected'''
        return type(self._model[self._get_selected()][1]) == Contact

    def get_group_selected(self):
        '''return a group object if there is a group selected, None otherwise
        '''
        if self.is_group_selected():
            return self._model[self._get_selected()][1]
            
        return None

    def get_contact_selected(self):
        '''return a contact object if there is a group selected, None otherwise
        '''
        if self.is_contact_selected():
            return self._model[self._get_selected()][1]
            
        return None

    def add_group(self, group):
        '''add a group to the contact list'''
        if self.order_by_status:
            return None

        group_data = (None, group, self.format_group(group), False, None)

        for row in self._model:
            obj = row[1]
            if type(obj) == Group:
                if obj.name == group.name:
                    print 'Trying to add an existing group!', obj.name
                    return row.iter

        return self._model.append(None, group_data)

    def remove_group(self, group):
        '''remove a group from the contact list'''
        for row in self._model:
            obj = row[1]
            if type(obj) == Group and obj.name == group.name:
                del self._model[row.iter]

    def add_contact(self, contact, group=None):
        '''add a contact to the contact list, add it to the group if 
        group is not None'''
        contact_data = (utils.safe_gtk_pixbuf_load(gui.theme.user), contact, 
            self.format_nick(contact), True, 
            utils.safe_gtk_pixbuf_load(gui.theme.status_icons[contact.status]))
      
        # if no group add it to the root, but check that it's not on a group
        # or in the root already
        if not group or self.order_by_status:
            for row in self._model:
                obj = row[1]
                # check on group
                if type(obj) == Group:
                    for contact_row in row.iterchildren():
                        con = contact_row[1]
                        if con.account == contact.account:
                            return contact_row.iter
                # check on the root
                elif type(obj) == Contact and obj.account == contact.account:
                    return row.iter

            return self._model.append(None, contact_data)

        for row in self._model:
            obj = row[1]
            if type(obj) == Group and obj.name == group.name:
                return_iter = self._model.append(row.iter, contact_data)
                self.update_group(group)

                # search the use on the root to remove it if it's there
                # since we added him to a group
                for irow in self._model:
                    iobj = irow[1]
                    if type(iobj) == Contact and \
                            iobj.account == contact.account:
                        del self._model[irow.iter]

                return return_iter
        else:            
            self.add_group(group)
            return self.add_contact(contact, group)

    def remove_contact(self, contact, group=None):
        '''remove a contact from the specified group, if group is None
        then remove him from all groups'''
        if not group:
            # go though the groups and the contacts without group
            for row in self._model:
                obj = row[1]
                # if we get a group we go through the contacts
                if type(obj) == Group:
                    for contact_row in row.iterchildren():
                        con = contact_row[1]
                        # if we find it, we remove it
                        if con.account == contact.account:
                            del self._model[contact_row.iter]
                            self.update_group(obj)

                # if it's a contact without group (at the root)
                elif type(obj) == Contact and obj.account == contact.account:
                    del self._model[row.iter]

            return

        # go though the groups
        for row in self._model:
            obj = row[1]
            # if it's the group we are searching
            if type(obj) == Group and obj.name == group.name:
                # go through all the contacts
                for contact_row in row.iterchildren():
                    con = contact_row[1]
                    # if we find it, we remove it
                    if con.account == contact.account:
                        del self._model[contact_row.iter]
                        self.update_group(group)

    def clear(self):
        '''clear the contact list'''
        self._model.clear()

        # this is the best place to put this code without putting gtk code
        # on gui.ContactList
        self.exp_column.set_visible(not self.order_by_status)

    def update_contact(self, contact):
        '''update the data of contact'''
        contact_data = (utils.safe_gtk_pixbuf_load(gui.theme.user), contact, 
            self.format_nick(contact), True,
            utils.safe_gtk_pixbuf_load(gui.theme.status_icons[contact.status]))

        for row in self._model:
            obj = row[1]
            if type(obj) == Group:
                for contact_row in row.iterchildren():
                    con = contact_row[1]
                    if con.account == contact.account:
                        self._model[contact_row.iter] = contact_data
                        self.update_group(obj)
            elif type(obj) == Contact and obj.account == contact.account:
                self._model[row.iter] = contact_data

    def update_group(self, group):
        '''update the data of group'''
        group_data = (None, group, self.format_group(group), False, None)

        for row in self._model:
            obj = row[1]
            if type(obj) == Group and obj.name == group.name:
                self._model[row.iter] = group_data

    def set_group_state(self, group, state):
        '''expand group id state is True, collapse it if False'''
        for row in self._model:
            obj = row[1]
            if type(obj) == Group and obj.name == group.name:
                path = self._model.get_path()

                if state:
                    self.expand_row(path, False)
                else:
                    self.collapse_row(path)
    
    def format_nick(self, contact):
        '''replace the appearance of the template vars using the values of
        the contact
        # valid values:
        # + NICK
        # + ACCOUNT
        # + DISPLAY_NAME (alias if available, or nick if available or mail)
        # + STATUS
        # + MESSAGE
        '''
        template = self.nick_template
        template = template.replace('%NICK%', 
            gobject.markup_escape_text(contact.nick))
        template = template.replace('%ACCOUNT%',
            gobject.markup_escape_text(contact.account))
        template = template.replace('%MESSAGE%', 
            gobject.markup_escape_text(contact.message))
        template = template.replace('%STATUS%', 
            gobject.markup_escape_text(status.STATUS[contact.status]))
        template = template.replace('%DISPLAY_NAME%', 
            gobject.markup_escape_text(contact.display_name))

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
        template = template.replace('%NAME%', 
            gobject.markup_escape_text(group.name))
        template = template.replace('%ONLINE_COUNT%', str(online))
        template = template.replace('%TOTAL_COUNT%', str(total))

        return template

def test():
    import dialog
    import string
    import random
    import protocol.ContactManager as ContactManager

    def _on_contact_selected(contact_list, contact):
        '''callback for the contact-selected signal'''
        print 'contact selected: ', contact.display_name
        contact.nick = random_string()
        contact.status = random.choice(status.ORDERED)
        contact.message = random_string()
        contact_list.update_contact(contact)

    def _on_group_selected(contact_list, group):
        '''callback for the group-selected signal'''
        print 'group selected: ', group.name
        group.name = random_string()
        contact_list.update_group(group)
    
    def _on_contact_menu_selected(contact_list, contact):
        '''callback for the contact-menu-selected signal'''
        print 'contact menu selected: ', contact.display_name
        contact_list.remove_contact(contact)

    def _on_group_menu_selected(contact_list, group):
        '''callback for the group-menu-selected signal'''
        print 'group menu selected: ', group.name
        contact_list.remove_group(group)

    def random_string(length=6):
        '''generate a random string of length "length"'''
        return ''.join([random.choice(string.ascii_letters) for i \
            in range(length)])

    def random_mail():
        '''generate a random mail'''
        return random_string() + '@' + random_string() + '.com'

    contactm = ContactManager('msn@msn.com')

    window = gtk.Window()
    window.set_default_size(200, 200)
    scroll = gtk.ScrolledWindow()
    scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
    conlist = ContactList(contactm, dialog)

    conlist.signal_connect('contact-selected', _on_contact_selected)
    conlist.signal_connect('contact-menu-selected', _on_contact_menu_selected)
    conlist.signal_connect('group-selected', _on_group_selected)
    conlist.signal_connect('group-menu-selected', _on_group_menu_selected)
    conlist.order_by_status = True
    conlist.show_offline = True

    scroll.add(conlist)
    window.add(scroll)
    window.connect("delete-event", gtk.main_quit)
    window.show_all()

    for i in range(6):
        group = Group(random_string())
        for j in range(6):
            contact = Contact(random_mail(), i * 10 + j, random_string())
            contact.status = random.choice(status.ORDERED)
            contact.message = random_string()
            group.contacts.append(contact.account)

            conlist.add_contact(contact, group)

    for j in range(6):
        contact = Contact(random_mail(), 100 + j, random_string())
        contact.status = random.choice(status.ORDERED)
        contact.message = random_string()

        conlist.add_contact(contact)

    gtk.main()

if __name__ == '__main__':
    test()
