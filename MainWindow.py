# -*- coding: utf-8 -*-
import os
import gtk
import time

import gui
import utils

import Menu
import dialog
import UserPanel
import ContactList
import gui.MainMenu as MainMenu
import gui.ContactMenu as ContactMenu
import gui.GroupMenu as GroupMenu

class MainWindow(gtk.VBox):
    '''this class represents the widget that is shown when the user is logged
    in (menu, contact list etc)'''

    def __init__(self, session, on_new_conversation, on_close):
        '''class constructor'''
        gtk.VBox.__init__(self)
        self.contact_list = ContactList.ContactList(session)
        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scroll.set_shadow_type(gtk.SHADOW_IN)
        scroll.set_border_width(1)
        self.session = session
        self.on_new_conversation = on_new_conversation
        self.on_close = on_close

        self.session.protocol.connect('contact-attr-changed', 
            self._on_contact_attr_changed)

        self._menu = MainMenu.MainMenu(dialog, self.session.account, 
            self.contact_list)
        self._menu.signal_connect('quit-selected', self._on_quit_selected)
        self._menu.signal_connect('disconnect-selected', 
            self._on_disconnect_selected)
        self._menu.signal_connect('preferences-selected', 
            self._on_preferences_selected)
        self._menu.signal_connect('plugins-selected', self._on_plugins_selected)
        self._menu.signal_connect('about-selected', self._on_about_selected)
        self.menu = Menu.build_menu_bar(self._menu)

        self.panel = UserPanel.UserPanel(session)
        self.panel.nick.connect('text-changed', self._on_nick_changed)
        self.panel.message.connect('text-changed', self._on_message_changed)
        self.panel.search.connect('toggled', self._on_search_toggled)
        self.panel.enabled = False

        self.entry = gtk.Entry()
        self.entry.connect('changed', self._on_entry_changed)
        self.entry.connect('key-press-event', self._on_entry_key_press)

        self.pack_start(self.menu, False)
        self.pack_start(self.panel, False)
        self.pack_start(scroll, True, True)
        self.pack_start(self.entry, False)

        self.contact_list.signal_connect('contact-selected', 
            self._on_contact_selected)
        self.contact_list.signal_connect('contact-menu-selected', 
            self._on_contact_menu_selected)
        self.contact_list.signal_connect('group-selected', 
            self._on_group_selected)
        self.contact_list.signal_connect('group-menu-selected', 
            self._on_group_menu_selected)

        scroll.add(self.contact_list)
        scroll.show_all()

    def show(self):
        '''show the widget'''
        gtk.VBox.show(self)
        self.menu.show_all()
        self.panel.show()
        self.contact_list.show()

    def _on_entry_changed(self, entry, *args):
        '''called when the text on entry changes'''
        self.contact_list.filter_text = entry.get_text()

    def _on_entry_key_press(self, entry, event):
        '''called when a key is pressed on the search box'''
        if event.keyval == gtk.keysyms.Escape:
            self.panel.search.set_active(False)
            entry.hide()

    def _on_contact_selected(self, contact_list, contact):
        '''callback for the contact-selected signal'''
        cid = time.time()
        (existed, conversation) = self.on_new_conversation(
            self.session.protocol, (cid, [contact.account]))

        if not existed:
            self.session.protocol.do_new_conversation(contact.account, cid)
        
    def _on_group_selected(self, contact_list, group):
        '''callback for the group-selected signal'''
        print 'group selected: ', group.name
    
    def _on_contact_menu_selected(self, contact_list, contact):
        '''callback for the contact-menu-selected signal'''
        contact_menu = ContactMenu.ContactMenu(contact, 
            self.session, dialog)
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

    def _on_contact_attr_changed(self, protocol, args):
        '''callback called when an attribute of a contact changed'''
        account = args[0]
        contact = self.session.contacts.get(account)

        if contact:
            self.contact_list.update_contact(contact)
        else:
            print 'account', account, 'not found on contacts'

    def _on_nick_changed(self, textfield, old_text, new_text):
        '''method called when the nick is changed on the panel'''
        self.session.account.set_nick(new_text)

    def _on_message_changed(self, textfield, old_text, new_text):
        '''method called when the nick is changed on the panel'''
        self.session.account.set_personal_message(new_text)

    def _on_key_press(self, widget, event):
        '''method called when a key is pressed on the input widget'''
        if event.keyval == gtk.keysyms.f and \
                event.state == gtk.gdk.CONTROL_MASK:
            self.panel.search.set_active(True)
            self.entry.show()
            self.entry.grab_focus()

    def _on_quit_selected(self, menu):
        '''callback called when the quit option is selected'''
        self.on_close()

    def _on_disconnect_selected(self, menu):
        '''callback called when the disconnect option is selected'''
        pass

    def _on_preferences_selected(self, menu):
        '''callback called when the preferences option is selected'''
        dialog.information('Not implemented')

    def _on_plugins_selected(self, menu):
        '''callback called when the plugins option is selected'''
        dialog.information('Not implemented')

    def _on_about_selected(self, menu):
        '''callback called when the about option is selected'''
        about = gtk.AboutDialog()
        about.set_name('mesinyer')
        about.set_version('2.0 alpha 0.0.1')
        about.set_copyright('marianoguerra')
        about.set_license('GPL v3')
        about.set_website('www.emesene.org')
        about.set_authors(['mariano guerra'])
        about.set_artists(['vdepizzol'])
        icon = utils.safe_gtk_pixbuf_load(gui.theme.logo)
        about.set_logo(icon)
        about.set_icon(icon)
        about.set_program_name('emesene')

        about.run()
        about.hide()

    def _on_search_toggled(self, button):
        '''called when the searhc button is toggled'''
        if button.get_active():
            self.entry.show()
            self.entry.grab_focus()
        else:
            self.entry.set_text('')
            self.entry.hide()

    def do_test(self):
        '''do some test to the contact list'''
        import random
        import string
        import protocol.Contact as Contact
        import protocol.Group as Group
        import protocol.status as status
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

