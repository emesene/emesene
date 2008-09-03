# -*- coding: utf-8 -*-
import os
import gtk

import ContactList
import dialog
import Menu
import gui.MainMenu as MainMenu
import gui.ContactMenu as ContactMenu
import gui.GroupMenu as GroupMenu

class MainWindow(gtk.VBox):
    '''this class represents the widget that is shown when the user is logged
    in (menu, contact list etc)'''

    def __init__(self, session):
        '''class constructor'''
        gtk.VBox.__init__(self, spacing=2)
        self.contact_list = ContactList.ContactList(session.contacts, 
            session.groups, dialog)
        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.session = session

        self.menu = MainMenu.MainMenu(dialog, 
            self.session.contacts, self.session.groups, 
                self.contact_list)

        entry = gtk.Entry()
        entry.connect('changed', self._on_entry_changed)

        self.pack_start(Menu.build_menu_bar(self.menu), False)
        self.pack_start(entry, False)
        self.pack_start(scroll, True, True)

        self.contact_list.signal_connect('contact-selected', 
            self._on_contact_selected)
        self.contact_list.signal_connect('contact-menu-selected', 
            self._on_contact_menu_selected)
        self.contact_list.signal_connect('group-selected', 
            self._on_group_selected)
        self.contact_list.signal_connect('group-menu-selected', 
            self._on_group_menu_selected)

        scroll.add(self.contact_list)
        self.show_all()

    def show(self):
        '''show the widget'''
        self.show_all()

    def _on_entry_changed(self, entry, *args):
        '''called when the text on entry changes'''
        self.contact_list.filter_text = entry.get_text()

    def _on_contact_selected(self, contact_list, contact):
        '''callback for the contact-selected signal'''
        print 'contact selected: ', contact.display_name
        
    def _on_group_selected(self, contact_list, group):
        '''callback for the group-selected signal'''
        print 'group selected: ', group.name
    
    def _on_contact_menu_selected(self, contact_list, contact):
        '''callback for the contact-menu-selected signal'''
        contact_menu = ContactMenu.ContactMenu(contact, 
            self.session.contacts, dialog)
        menu = Menu.build_pop_up(contact_menu)
        contact_menu.block_item.enabled = not contact.blocked
        contact_menu.unblock_item.enabled = contact.blocked
        menu.popup(None, None, None, 0, 0)

    def _on_group_menu_selected(self, contact_list, group):
        '''callback for the group-menu-selected signal'''
        group_menu = GroupMenu.GroupMenu(group, 
            self.session.groups, self.session.contacts, dialog)
        menu = Menu.build_pop_up(group_menu)
        menu.popup(None, None, None, 0, 0)

    def do_test(self):
        '''do some test to the contact list'''
        import random
        import string
        import protocol.base.Contact as Contact
        import protocol.base.Group as Group
        import protocol.base.status as status
        self.contact_list.show_by_group = True

        def random_string(length=6):
            '''generate a random string of length "length"'''
            return ''.join([random.choice(string.ascii_letters) for i \
                in range(length)])

        def random_mail():
            '''generate a random mail'''
            return random_string() + '@' + random_string() + '.com'

        for i in range(6):
            group = Group(random_string())
            for j in range(6):
                contact = Contact(random_mail(), i * 10 + j, random_string())
                contact.status = random.choice(status.ORDERED)
                contact.message = random_string()
                group.contacts.append(contact.account)
                self.contact_list.add_contact(contact, group)

        for j in range(6):
            contact = Contact(random_mail(), 100 + j, random_string())
            contact.status = random.choice(status.ORDERED)
            contact.message = random_string()

            self.contact_list.add_contact(contact)

