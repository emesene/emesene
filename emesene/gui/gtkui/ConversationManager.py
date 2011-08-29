'''a module that define classes to build the conversation widget'''
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
from gui.base import Plus

class ConversationManager(gtk.Notebook, gui.ConversationManager):
    '''the main conversation, it only contains other widgets'''

    NAME = 'Conversation Manager'
    DESCRIPTION = 'The widget that contains a group of conversations'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, session, on_last_close):
        '''class constructor'''
        gtk.Notebook.__init__(self)
        gui.ConversationManager.__init__(self, session, on_last_close)

        self.session = session;
        self.set_scrollable(True)
        self.set_property('can-focus', False)
        self.set_tab_pos(pos=self.get_tab_position())
        #self.set_scrollable(session.config.get_or_set('b_conv_tab_scroll',
        #    True))

        if session.config.get_or_set('b_conv_tab_popup', False):
            self.popup_enable()

        # mozilla tabs are fixed-width, otherwise do the same as emesene-1
        self.mozilla_tabs = session.config.get_or_set('b_conv_tab_mozilla_like', False)

        self.connect('switch-page', self._on_switch_page)
        self.connect('page-reordered', self._on_page_reordered)
        self.session.config.subscribe(self._on_tab_position_changed,
            'i_tab_position')

    def _on_key_press(self, widget, event):
        '''Catches Ctrl+Tab and Ctrl+Shift+Tab for cycling through tabs'''
        if (event.state & gtk.gdk.CONTROL_MASK) and \
            event.keyval in [gtk.keysyms.Tab, gtk.keysyms.ISO_Left_Tab]:
            if event.state & gtk.gdk.SHIFT_MASK:
                self.cycle_tabs(True)
            else:
                self.cycle_tabs()
            return True

    def _on_tab_position_changed(self,value):
        '''callback called when i_tab_position changes'''
        self.set_tab_pos(pos=self.get_tab_position())

    def _set_accels(self):
        """set the keyboard shortcuts
        """
        accel_group = gtk.AccelGroup()
        self.get_parent().add_accel_group(accel_group)
        self.accel_group = accel_group
        accel_group.connect_group(gtk.keysyms.Page_Down, \
                                  gtk.gdk.CONTROL_MASK, gtk.ACCEL_LOCKED, \
                                  self.on_key_cycle_tabs)
        accel_group.connect_group(gtk.keysyms.Page_Up, \
                                  gtk.gdk.CONTROL_MASK, gtk.ACCEL_LOCKED, \
                                  self.on_key_cycle_tabs)
        accel_group.connect_group(gtk.keysyms.W, \
                                  gtk.gdk.CONTROL_MASK, gtk.ACCEL_LOCKED, \
                                  self.on_key_close_tab)
        accel_group.connect_group(gtk.keysyms.Escape, \
                                  0, gtk.ACCEL_LOCKED, \
                                  self.on_key_close_tab)

        for i in range(1, 10):
            accel_group.connect_group(gtk.keysyms._0 + i,
                gtk.gdk.MOD1_MASK, gtk.ACCEL_LOCKED,
                self.on_key_change_tab)

    def on_key_close_tab(self, accel_group, window, keyval, modifier):
        '''Catches events like Ctrl+W and closes current tab'''
        index = self.get_current_page()
        conversation = self.get_nth_page(index)
        self.on_conversation_close(conversation)

    def on_key_change_tab(self, accelGroup, window, keyval, modifier):
        '''Catches alt+number and shows tab number-1  '''
        pages = self.get_n_pages()
        new = keyval - gtk.keysyms._0 - 1

        if new < pages:
            self.set_current_page(new)

    def on_key_cycle_tabs(self, accelGroup, window, keyval, modifier):
        '''Catches events like Ctrl+AvPag and consequently changes current
        tab'''
        if not modifier == gtk.gdk.CONTROL_MASK:
            return

        if keyval == gtk.keysyms.Page_Down:
            self.cycle_tabs()
        elif keyval == gtk.keysyms.Page_Up:
            self.cycle_tabs(True)

        return True

    def cycle_tabs(self, reverse=False):
        last = self.get_n_pages() - 1

        if reverse:
            current = self.get_current_page()

            if current > 0:
                self.prev_page()
            else:
                self.set_current_page(last)
        else:
            current = self.get_current_page()

            if current < last:
                self.next_page()
            else:
                self.set_current_page(0)

    def set_message_waiting(self, conversation, is_waiting):
        """
        inform the user that a message is waiting for the conversation
        """
        parent = self.get_parent()

        if parent is not None and conversation in self.conversations.values():
            if (is_waiting and not parent.is_active()) or not is_waiting:
                parent.set_urgency_hint(is_waiting)
                conversation.message_waiting = is_waiting

    def _on_focus(self, widget, event):
        '''called when the widget receives the focus'''
        page_num = self.get_current_page()

        if page_num != -1:
            page = self.get_nth_page(page_num)
            self.session.add_event(e3.Event.EVENT_MESSAGE_READ, page)
            self.set_message_waiting(page, False)

    def _on_switch_page(self, notebook, page, page_num):
        '''called when the user changes the tab'''
        page = self.get_nth_page(page_num)
        if self.get_current_page() > -1:
            self.session.add_event(e3.Event.EVENT_MESSAGE_READ, page)
            self.set_message_waiting(page, False)
        if page.show_avatar_in_taskbar:
            self.update_window(page.text, page.his_avatar.filename, self.get_current_page())
        else:
            self.update_window(page.text, page.icon, self.get_current_page())
        page.input_grab_focus()
        return True

    def _on_tab_close(self, button, conversation):
        '''called when the user clicks the close button on a tab'''
        # TODO: we can check the last message timstamp and if it's less than
        # certains seconds, inform that there is a new message (to avoid
        # closing a tab instants after you receive a new message)
        self.on_conversation_close(conversation)

    def _on_tab_menu(self, widget, event, conversation):
        '''called when the user right clicks on the tab'''
        if event.button == 3:
            conversation.show_tab_menu()

    def _on_page_reordered(self, widget, conversation, new_num):
        '''called when a page is reordered'''
        conversation.tab_index = new_num

    def remove_conversation(self, conversation):
        """
        remove the conversation from the gui

        conversation -- the conversation instance
        """
        page_num = self.page_num(conversation)
        conversation.tab_label.remove_subscriptions()
        self.remove_page(page_num)
        #FIXME: Dirty hack, why conversation is still alive when it's closed?
        #       Signals are being unsubscribed (see gtkui.Conversation) but...
        conversation.tab_index = -2

    def add_new_conversation(self, session, cid, members):
        """
        create and append a new conversation
        """
        Conversation = extension.get_default('conversation')
        TabWidget = extension.get_default('conversation tab')
        conversation = Conversation(self.session, cid, self.update_window, None, members)
        label = TabWidget('Connecting', self._on_tab_menu, self._on_tab_close,
            conversation, self.mozilla_tabs)
        label.set_image(gui.theme.image_theme.connect)
        conversation.tab_label = label
        conversation.tab_index=self.append_page_menu(conversation, label)
        self.set_tab_label_packing(conversation, not self.mozilla_tabs, True, gtk.PACK_START)
        self.set_tab_reorderable(conversation, True)

        return conversation

    def update_window(self, text, icon, index):
        ''' updates the window's border and item on taskbar
            with given text and icon '''
        if self.get_current_page() == index or index == (self.get_current_page() + self.get_n_pages()):
            win = self.get_parent() # gtk.Window, not a nice hack.
            if win is None:
                return
            win.set_title(Plus.msnplus_strip(text))
            win.set_icon(icon)

    def present(self, conversation):
        '''
        present the given conversation
        '''
        self.set_current_page(conversation.tab_index)
        self.get_parent().present()
        conversation.input_grab_focus()

    def get_dimensions(self):
        '''
        return dimensions of the conversation window, if more than one return
        the value of one of them
        '''
        return self.get_parent().get_dimensions()

    def get_tab_position(self):
        positions = [gtk.POS_TOP,gtk.POS_BOTTOM,gtk.POS_LEFT,gtk.POS_RIGHT]
        return positions[self.session.config.get_or_set('i_tab_position',0)]

    def hide_all(self):
        '''
        hide all conversations
        '''
        self.session.config.unsubscribe(self._on_tab_position_changed,
            'i_tab_position')
        self.get_parent().hide()

    def is_active(self):
        '''
        return True if the conversation manager is active
        '''
        return self.get_parent().is_active()

    def is_maximized(self):
        '''
        return True if the window is maximized
        '''
        return self.get_parent().is_maximized()
