'''a module that define classes to build the conversation widget'''
import gtk

import gui
import extension

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

        self.set_scrollable(True)
        self.connect('switch-page', self._on_switch_page)
        self.connect('key-press-event', self.on_key_press)

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
            accel_group.connect_group(gtk.keysyms._0 + i, \
                                  gtk.gdk.MOD1_MASK, gtk.ACCEL_LOCKED, \
                                  self.on_key_change_tab)

    def on_key_press(self, widget, event):
        '''callback called when a key is pressed on the window'''
        if (event.state & gtk.gdk.CONTROL_MASK) and event.keyval in [
                gtk.keysyms.Tab, gtk.keysyms.ISO_Left_Tab]:
            self.cycle_tabs()
            return True

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

        if parent is not None:
            if (is_waiting and not parent.is_active()) or not is_waiting:
                parent.set_urgency_hint(is_waiting)
                conversation.message_waiting = is_waiting

    def _on_focus(self, widget, event):
        '''called when the widget receives the focus'''
        page_num = self.get_current_page()
        if page_num != -1:
            page = self.get_nth_page(page_num)
            self.set_message_waiting(page, False)

    def _on_switch_page(self, notebook, page, page_num):
        '''called when the user changes the tab'''
        page = self.get_nth_page(page_num)
        self.set_message_waiting(page, False)
        parent = self.get_parent()
        parent.set_title(page.text)
        parent.set_icon(page.icon)

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

    def remove_conversation(self, conversation):
        """
        remove the conversation from the gui

        conversation -- the conversation instance
        """
        page_num = self.page_num(conversation)
        self.remove_page(page_num)

    def add_new_conversation(self, session, cid, members):
        """
        create and append a new conversation
        """
        Conversation = extension.get_default('conversation')
        TabWidget = extension.get_default('conversation tab')
        conversation = Conversation(self.session, cid, None, members)
        label = TabWidget('Connecting', self._on_tab_menu, self._on_tab_close,
            conversation)
        label.set_image(gui.theme.connect)
        conversation.tab_label = label
        conversation.tab_index=self.append_page_menu(conversation, label)
        self.set_tab_label_packing(conversation, True, True, gtk.PACK_START)
        self.set_tab_reorderable(conversation, True)
        return conversation

