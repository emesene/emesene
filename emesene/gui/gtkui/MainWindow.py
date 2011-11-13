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

import gtk

import e3
import gui
import extension

import logging

from gui import Desktop

log = logging.getLogger('gtkui.MainWindow')

class MainWindow(gtk.VBox, gui.MainWindowBase):
    '''this class represents the widget that is shown when the user is logged
    in (menu, contact list etc)'''
    NAME = 'Main Window'
    DESCRIPTION = 'The window used when an account is logged in'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, session, on_new_conversation):
        '''class constructor'''
        gtk.VBox.__init__(self)
        gui.MainWindowBase.__init__(self, session, on_new_conversation)

        UserPanel = extension.get_default('user panel')
        ContactList = extension.get_default('contact list')

        self.below_menu = extension.get_and_instantiate('below menu', self)
        self.below_panel = extension.get_and_instantiate('below panel', self)
        self.below_userlist = extension.get_and_instantiate('below userlist', self)

        self.contact_list = ContactList(session)
        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scroll.set_shadow_type(gtk.SHADOW_IN)
        scroll.set_border_width(1)

        self.session.signals.contact_attr_changed.subscribe(
            self._on_contact_attr_changed)
        self.session.signals.close.subscribe(self.on_disconnect)

        self.menu = None
        self.contact_menu = None
        self.group_menu = None

        self._build_menus()

        self.panel = UserPanel(session)
        self.panel.nick.connect('text-changed', self._on_nick_changed)
        self.panel.message.connect('text-changed', self._on_message_changed)
        self.panel.mail.connect('button_release_event', self._on_mail_click)
        self.panel.search.connect('toggled', self._on_search_toggled)
        self.panel.enabled = False

        self.entry = gtk.Entry()
        self.entry.connect('changed', self._on_entry_changed)
        self.entry.connect('key-press-event', self._on_entry_key_press)

        self.pack_start(self.menu, False)
        self.pack_start(self.below_menu, False)
        self.pack_start(self.panel, False)
        self.pack_start(self.below_panel, False)
        self.pack_start(self.entry, False)
        self.pack_start(scroll, True, True)
        self.pack_start(self.below_userlist, False)

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

    def _on_mail_count_changed(self, count):
        self.panel.mail.set_label("(%d)" % count)

    def _on_mail_click(self, widget, data):
        self.on_mail_click()

    def _on_social_request(self, conn_url):
        Desktop.open(conn_url)

        def set_token(token):
            self.session.config.facebook_token = token
        dialog = extension.get_default('dialog')
        fb_token_dialog = dialog.facebook_token_window("", set_token)


    def _on_show_userpanel_changed(self, value):
        '''callback called when config.b_show_userpanel changes'''
        if value:
            self.panel.show()
        else:
            self.panel.hide()

    def _build_menus(self):
        '''buildall the menus used on the client'''
        dialog = extension.get_default('dialog')

        handler = gui.base.MenuHandler(self.session, dialog, self.contact_list)

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
        self.contact_list._set_accels(self.get_parent())

    def _replace_below_userlist(self):
        self.remove(self.below_userlist)
        self.below_userlist = extension.get_and_instantiate('below userlist', self)
        self.pack_start(self.below_userlist, False)
        pos = len(self.get_children()) - 2
        self.reorder_child(self.below_userlist, pos)
        self.below_userlist.show()

    def _replace_below_menu(self):
        self.remove(self.below_menu)
        self.below_menu = extension.get_and_instantiate('below menu', self)
        self.pack_start(self.below_menu, False)
        self.reorder_child(self.below_menu, 1)
        self.below_menu.show()

    def _replace_below_panel(self):
        self.remove(self.below_panel)
        self.below_panel = extension.get_and_instantiate('below panel', self)
        self.pack_start(self.below_panel, False)
        self.reorder_child(self.below_panel, 3)
        self.below_panel.show()

    def replace_extensions(self):
        self._replace_below_userlist()
        self._replace_below_menu()
        self._replace_below_panel()

    def _on_entry_changed(self, entry, *args):
        '''called when the text on entry changes'''
        self.contact_list.filter_text = entry.get_text().lower()
        self.contact_list.un_expand_groups()

    def _on_entry_key_press(self, entry, event):
        '''called when a key is pressed on the search box'''
        if event.keyval == gtk.keysyms.Escape:
            self.panel.search.set_active(False)
            entry.hide()

    def _on_contact_selected(self, contact):
        '''callback for the contact-selected signal'''
        self.on_new_conversation_requested(contact.account)

    def _on_group_selected(self, group):
        '''callback for the group-selected signal'''
        pass

    def _on_contact_menu_selected(self, contact):
        '''callback for the contact-menu-selected signal'''
        if contact.blocked:
            self.contact_menu.set_blocked()
        else:
            self.contact_menu.set_unblocked()
        self.contact_menu.popup(None, None, None, 0, 0)

    def _on_group_menu_selected(self, group):
        '''callback for the group-menu-selected signal'''
        if self.contact_list.is_favorite_group_selected():
            self.group_menu.show_unset_favorite_item()
        else:
            self.group_menu.show_set_favorite_item()
        self.group_menu.popup(None, None, None, 0, 0)

    def _on_contact_attr_changed(self, account, change_type, old_value,
            do_notify=True):
        '''callback called when an attribute of a contact changed'''
        contact = self.session.contacts.get(account)
        if not contact:
            log.debug('account %s not found on contacts' % account)

    def _on_nick_changed(self, textfield, old_text, new_text):
        '''method called when the nick is changed on the panel'''
        self.session.set_nick(new_text)

    def _on_message_changed(self, textfield, old_text, new_text):
        '''method called when the nick is changed on the panel'''
        self.session.set_message(new_text)

    def _on_key_press(self, widget, event):
        '''method called when a key is pressed on the input widget'''
        if event.keyval == gtk.keysyms.f and \
                event.state & gtk.gdk.CONTROL_MASK:
            self.panel.search.set_active(not self.panel.search.get_active())
            if self.panel.search.get_active():
                self.entry.show()
                self.entry.grab_focus()
            else:
                self.entry.hide()
        elif not self.panel.nick.has_focus() and \
             not self.panel.message.has_focus():
            if event.string != "":
                if not self.panel.search.get_active():
                    self.panel.search.set_active(True)
                    self.entry.show()
                    self.entry.grab_focus()
            elif event.keyval == gtk.keysyms.BackSpace and \
                 self.entry.get_text_length() == 1:
                self.panel.search.set_active(False)
                self.entry.hide()

    def on_disconnect(self, close=None):
        '''callback called when the disconnect option is selected'''
        gui.MainWindowBase.on_disconnect(self)
        self.contact_list.contact_selected.unsubscribe(
            self._on_contact_selected)
        self.contact_list.group_selected.unsubscribe(self._on_group_selected)
        self.contact_list.contact_menu_selected.unsubscribe(
            self._on_contact_menu_selected)
        self.contact_list.group_menu_selected.unsubscribe(
            self._on_group_menu_selected)
        self.contact_list.remove_subscriptions()
        self.session.config.unsubscribe(self._on_show_userpanel_changed,
            'b_show_userpanel')
        self.session.signals.contact_attr_changed.unsubscribe(
            self._on_contact_attr_changed)
        self.panel.remove_subscriptions()
        self.session.signals.close.unsubscribe(self.on_disconnect)

    def _on_search_toggled(self, button):
        '''called when the search button is toggled'''
        if button.get_active():
            self.entry.show()
            self.entry.grab_focus()
            self.contact_list.is_searching = True
            # Using private member because i don't want to update config
            self.contact_list._show_empty_groups = True
            self.contact_list.refilter()
        else:
            self.entry.set_text('')
            self.entry.hide()
            self.contact_list.is_searching = False
            self.contact_list.show_empty_groups = self.session.config.b_show_empty_groups
            self.contact_list.un_expand_groups()

