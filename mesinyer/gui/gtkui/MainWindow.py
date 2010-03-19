# -*- coding: utf-8 -*-
import os
import gtk
import time

import e3
import gui
import utils
import extension

import logging
log = logging.getLogger('gtkui.MainWindow')

class MainWindow(gtk.VBox):
    '''this class represents the widget that is shown when the user is logged
    in (menu, contact list etc)'''
    NAME = 'Main Window'
    DESCRIPTION = 'The window used when an account is logged in'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, session, on_new_conversation, on_close,
                on_disconnect_cb):
        '''class constructor'''
        gtk.VBox.__init__(self)
        self.session = session

        UserPanel = extension.get_default('user panel')
        ContactList = extension.get_default('contact list')

        self.below_menu = extension.get_and_instantiate('below menu', self)
        self.below_panel = extension.get_and_instantiate('below panel', self)
        self.below_userlist = extension.get_and_instantiate('below userlist', self)

        self.music = extension.get_and_instantiate('music', self)

        self.contact_list = ContactList(session)
        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scroll.set_shadow_type(gtk.SHADOW_IN)
        scroll.set_border_width(1)
        self.on_new_conversation = on_new_conversation
        self.on_close = on_close
        self.on_disconnect_cb = on_disconnect_cb

        self.session.signals.contact_attr_changed.subscribe(
            self._on_contact_attr_changed)

        self.menu = None
        self.contact_menu = None
        self.contact_menu = None
        self.group_menu = None

        self._build_menus()

        self.panel = UserPanel(session)
        self.panel.nick.connect('text-changed', self._on_nick_changed)
        self.panel.message.connect('text-changed', self._on_message_changed)
        self.panel.search.connect('toggled', self._on_search_toggled)
        self.panel.enabled = False

        self.entry = gtk.Entry()
        self.entry.connect('changed', self._on_entry_changed)
        self.entry.connect('key-press-event', self._on_entry_key_press)

        self.pack_start(self.menu, False)
        self.pack_start(self.below_menu, False)
        self.pack_start(self.panel, False)
        self.pack_start(self.below_panel, False)
        self.pack_start(scroll, True, True)
        self.pack_start(self.below_userlist, False)
        self.pack_start(self.entry, False)

        self.contact_list.contact_selected.subscribe(self._on_contact_selected)
        self.contact_list.group_selected.subscribe(self._on_group_selected)
        self.contact_list.contact_menu_selected.subscribe(
            self._on_contact_menu_selected)
        self.contact_list.group_menu_selected.subscribe(
            self._on_group_menu_selected)

        scroll.add(self.contact_list)
        scroll.show_all()

        if self.session.config.b_show_userpanel:
            self.panel.hide()

        self.session.config.subscribe(self._on_show_userpanel_changed,
            'b_show_userpanel')

    def _on_show_userpanel_changed(self, value):
        '''callback called when config.b_show_userpanel changes'''
        if value:
            self.panel.show()
        else:
            self.panel.hide()

    def _build_menus(self):
        '''buildall the menus used on the client'''
        dialog = extension.get_default('dialog')

        handler = gui.base.MenuHandler(self.session, dialog, self.contact_list,
            self.on_disconnect, self.on_close)

        contact_handler = gui.base.ContactHandler(self.session, dialog,
            self.contact_list)
        group_handler = gui.base.GroupHandler(self.session, dialog,
            self.contact_list)

        MainMenu = extension.get_default('main menu')
        ContactMenu = extension.get_default('menu contact')
        GroupMenu = extension.get_default('menu group')

        self.menu = MainMenu(handler, self.session.config)

        self.contact_menu = ContactMenu(contact_handler)
        self.group_menu = GroupMenu(group_handler)
        self.contact_menu.show_all()
        self.group_menu.show_all()

    def show(self):
        '''show the widget'''
        gtk.VBox.show(self)
        self.menu.show_all()
        self.panel.show()
        self.contact_list.show()
        self.below_menu.show()
        self.below_panel.show()
        self.below_userlist.show()

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
        self.on_new_conversation(cid, [contact.account], False)
        
        #this calls the e3 Handler
        self.session.new_conversation(contact.account, cid)

    def _on_group_selected(self, group):
        '''callback for the group-selected signal'''
        pass

    def _on_contact_menu_selected(self, contact):
        '''callback for the contact-menu-selected signal'''
        self.contact_menu.popup(None, None, None, 0, 0)

    def _on_group_menu_selected(self, group):
        '''callback for the group-menu-selected signal'''
        self.group_menu.popup(None, None, None, 0, 0)

    def _on_contact_attr_changed(self, account, change_type, old_value,
            do_notify=True):
        '''callback called when an attribute of a contact changed'''
        contact = self.session.contacts.get(account)
        if not contact:
            log.debug('account %s not found on contacts' % account)

        if change_type == 'online' and do_notify:
            if self.session.config.b_notify_contact_online:
                gui.notify(contact.display_name, "is now online")

            if self.session.config.b_play_contact_online:
                gui.play(self.session, gui.theme.sound_online)
        elif change_type == 'offline':
            if self.session.config.b_notify_contact_offline:
                gui.notify(contact.display_name, "is now offline")

            if self.session.config.b_play_contact_offline:
                gui.play(self.session, gui.theme.sound_offline)

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
        self.contact_list.contact_selected.unsubscribe(
            self._on_contact_selected)
        self.contact_list.group_selected.unsubscribe(self._on_group_selected)
        self.contact_list.contact_menu_selected.unsubscribe(
            self._on_contact_menu_selected)
        self.contact_list.group_menu_selected.unsubscribe(
            self._on_group_menu_selected)
        self.session.config.unsubscribe(self._on_show_userpanel_changed,
            'b_show_userpanel')
        self.on_disconnect_cb()

    def _on_search_toggled(self, button):
        '''called when the searhc button is toggled'''
        if button.get_active():
            self.entry.show()
            self.entry.grab_focus()
        else:
            self.entry.set_text('')
            self.entry.hide()

