# -*- coding: utf-8 -*-
import os
import gtk
import time

import gui
import Menu
import utils
import e3common

gui.components.Menu = Menu

import dialog
import UserPanel
import ContactList

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

        self.session.signals.connect('contact-attr-changed',
            self._on_contact_attr_changed)

        self.menu = None
        self.gtk_menu = None
        self.contact_menu = None
        self.gtk_contact_menu = None
        self.group_menu = None
        self.gtk_group_menu = None

        self._build_menus()

        self.panel = UserPanel.UserPanel(session)
        self.panel.nick.connect('text-changed', self._on_nick_changed)
        self.panel.message.connect('text-changed', self._on_message_changed)
        self.panel.search.connect('toggled', self._on_search_toggled)
        self.panel.enabled = False

        self.entry = gtk.Entry()
        self.entry.connect('changed', self._on_entry_changed)
        self.entry.connect('key-press-event', self._on_entry_key_press)

        self.pack_start(self.gtk_menu, False)
        self.pack_start(self.panel, False)
        self.pack_start(scroll, True, True)
        self.pack_start(self.entry, False)

        self.contact_list.contact_selected.suscribe(self._on_contact_selected)
        self.contact_list.group_selected.suscribe(self._on_group_selected)
        self.contact_list.contact_menu_selected.suscribe(
            self._on_contact_menu_selected)
        self.contact_list.group_menu_selected.suscribe(
            self._on_group_menu_selected)

        scroll.add(self.contact_list)
        scroll.show_all()

    def _build_menus(self):
        '''buildall the menus used on the client'''
        handler = e3common.MenuHandler(self.session, dialog, self.contact_list,
            self.on_disconnect, self.on_close)

        contact_handler = e3common.ContactHandler(self.session, dialog,
            self.contact_list)
        group_handler = e3common.GroupHandler(self.session, dialog,
            self.contact_list)

        self.menu = gui.components.build_main_menu(handler, self.session.config)
        self.gtk_menu = self.menu.build_as_menu_bar()

        self.contact_menu = gui.components.build_contact_menu(contact_handler)
        self.gtk_contact_menu = self.contact_menu.build_as_popup()

        self.group_menu = gui.components.build_group_menu(group_handler)
        self.gtk_group_menu = self.group_menu.build_as_popup()

    def show(self):
        '''show the widget'''
        gtk.VBox.show(self)
        self.gtk_menu.show_all()
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

    def _on_contact_selected(self, contact):
        '''callback for the contact-selected signal'''
        cid = time.time()
        (existed, conversation) = self.on_new_conversation(
            self.session.signals, (cid, [contact.account]))

        if not existed:
            self.session.new_conversation(contact.account, cid)

    def _on_group_selected(self, group):
        '''callback for the group-selected signal'''
        pass

    def _on_contact_menu_selected(self, contact):
        '''callback for the contact-menu-selected signal'''
        self.gtk_contact_menu.popup(None, None, None, 0, 0)

    def _on_group_menu_selected(self, group):
        '''callback for the group-menu-selected signal'''
        self.gtk_group_menu.popup(None, None, None, 0, 0)

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
        self.session.set_nick(new_text)

    def _on_message_changed(self, textfield, old_text, new_text):
        '''method called when the nick is changed on the panel'''
        self.session.set_message(new_text)

    def _on_key_press(self, widget, event):
        '''method called when a key is pressed on the input widget'''
        if event.keyval == gtk.keysyms.f and \
                event.state == gtk.gdk.CONTROL_MASK:
            self.panel.search.set_active(True)
            self.entry.show()
            self.entry.grab_focus()

    def on_disconnect(self):
        '''callback called when the disconnect option is selected'''
        self.contact_list.contact_selected.unsuscribe(self._on_contact_selected)
        self.contact_list.group_selected.unsuscribe(self._on_group_selected)
        self.contact_list.contact_menu_selected.unsuscribe(
            self._on_contact_menu_selected)
        self.contact_list.group_menu_selected.unsuscribe(
            self._on_group_menu_selected)

    def _on_search_toggled(self, button):
        '''called when the searhc button is toggled'''
        if button.get_active():
            self.entry.show()
            self.entry.grab_focus()
        else:
            self.entry.set_text('')
            self.entry.hide()


