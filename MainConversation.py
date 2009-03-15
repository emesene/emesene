'''a module that define classes to build the conversation widget'''
import gtk
import pango
import gobject

import gui
import utils
import dialog
import TextBox
import WebKitTextBox

if WebKitTextBox.ERROR:
    from TextBox import OutputText
else:
    from WebKitTextBox import OutputText

import e3common.MarkupParser
import e3common.MessageFormatter

import TinyButton
import e3common

class MainConversation(gtk.Notebook, gui.ConversationManager):
    '''the main conversation, it only contains other widgets'''

    def __init__(self, session, on_last_close):
        '''class constructor'''
        gtk.Notebook.__init__(self)
        gui.ConversationManager.__init__(self, session, on_last_close)

        self.set_scrollable(True)
        self.connect('switch-page', self._on_switch_page)

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

    def _on_tab_close(self, button, event, conversation):
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
        conversation = Conversation(self.session, cid, None, members)
        label = TabWidget('Connecting', self._on_tab_menu, self._on_tab_close,
            conversation)
        label.set_image(gui.theme.connect)
        conversation.tab_label = label
        self.append_page_menu(conversation, label)
        self.set_tab_label_packing(conversation, True, True, gtk.PACK_START)
        self.set_tab_reorderable(conversation, True)
        return conversation


class Conversation(gtk.VBox, gui.Conversation):
    '''a widget that contains all the components inside'''

    def __init__(self, session, cid, tab_label, members=None):
        '''constructor'''
        gtk.VBox.__init__(self)
        gui.Conversation.__init__(self, session, cid, members)
        self.set_border_width(1)

        self.tab_label = tab_label

        self._header_visible = True
        self._image_visible = True
        self._toolbar_visible = True

        self.panel = gtk.VPaned()
        self.header = Header()
        toolbar_handler = e3common.ConversationToolbarHandler(self.session,
            dialog, gui.theme, self)
        self.toolbar = gui.components.build_conversation_toolbar(
            toolbar_handler)
        self.gtk_toolbar = self.toolbar.build_as_toolbar(style='only icons')
        self.output = OutputText(self.session.config)
        self.input = TextBox.InputText(self.session.config,
            self._on_send_message)
        self.info = ContactInfo()

        input_box = gtk.VBox()
        input_box.pack_start(self.gtk_toolbar, False)
        input_box.pack_start(self.input, True, True)

        self.panel.pack1(self.output, True, True)
        self.panel.pack2(input_box, True, True)

        self.hbox = gtk.HBox()
        self.hbox.pack_start(self.panel, True, True)
        self.hbox.pack_start(self.info, False)

        self.pack_start(self.header, False)
        self.pack_start(self.hbox, True, True)

        self._panel_show_id = self.panel.connect('map-event',
            self._on_panel_show)

        if len(self.members) == 0:
            self.header.information = Header.INFO_TPL % \
                ('connecting', 'creating conversation', '')

        self.header.set_image(gui.theme.user)
        self.info.first = utils.safe_gtk_image_load(gui.theme.logo)
        self.info.last = utils.safe_gtk_image_load(gui.theme.logo)

        self._load_style()

    def show(self):
        '''override the show method'''
        gtk.VBox.show(self)

        if self.session.config.b_show_header is None:
            self.session.config.b_show_header = True

        if self.session.config.b_show_info is None:
            self.session.config.b_show_info = True

        if self.session.config.b_show_header:
            self.header.show_all()

        if self.session.config.b_show_info:
            self.info.show_all()

        self.hbox.show()
        self.panel.show_all()

    def update_message_waiting(self, is_waiting):
        """
        update the information on the conversation to inform if a message is waiting
        
        is_waiting -- boolean value that indicates if a message is waiting
        """
        self.update_tab()

    def update_single_information(self, nick, message, account):
        """
        update the information for a conversation with a single user
        
        nick -- the nick of the other account (escaped)
        message -- the message of the other account (escaped)
        account -- the account
        """
        self.header.information = Header.INFO_TPL % (nick, message, account)
        self.update_tab()

    def _on_panel_show(self, widget, event):
        '''callback called when the panel is shown, resize the panel'''
        position = self.panel.get_position()
        self.panel.set_position(position + int(position * 0.6))
        self.panel.disconnect(self._panel_show_id)
        del self._panel_show_id

    def show_tab_menu(self):
        '''callback called when the user press a button over a widget
        chek if it's the right button and display the menu'''
        pass

    def update_tab(self):
        '''update the values of the tab'''
        self.tab_label.set_image(self.icon)
        self.tab_label.set_text(self.text)

    def update_group_information(self):
        """
        update the information for a conversation with multiple users
        """
        self.header.set_image(gui.theme.users)
        text = 'Group chat'

        self.header.information = Header.INFO_TPL % \
            (text, '%d members' % (len(self.members) + 1,), '')

        self.update_tab()

    def set_image_visible(self, is_visible):
        """
        set the visibility of the widget that displays the images of the members
        
        is_visible -- boolean that says if the widget should be shown or hidden
        """
        if is_visible:
            self.info.show()
        else:
            self.info.hide()

    def set_header_visible(self, is_visible):
        '''
        hide or show the widget according to is_visible
        
        is_visible -- boolean that says if the widget should be shown or hidden
        '''
        if is_visible:
            self.header.show()
        else:
            self.header.hide()

    def set_toolbar_visible(self, is_visible):
        '''
        hide or show the widget according to is_visible
        
        is_visible -- boolean that says if the widget should be shown or hidden
        '''
        if is_visible:
            self.toolbar.show()
        else:
            self.toolbar.hide()

class Header(gtk.HBox):
    '''a widget used to display some information about the conversation'''
    INFO_TPL = '<span weight="bold">%s</span>\n'
    INFO_TPL += '<span style="italic">%s</span>\n'
    INFO_TPL += '<span size="small">%s</span>'

    def __init__(self):
        '''constructor'''
        gtk.HBox.__init__(self)
        self.set_border_width(4)
        self._information = gtk.Label('info')
        self._information.set_ellipsize(pango.ELLIPSIZE_END)
        self._information.set_alignment(0.0, 0.5)
        self.image = gtk.Image()

        self.pack_start(self._information, True, True)
        self.pack_start(self.image, False)

    def set_image(self, path):
        '''set the image from path'''
        self.remove(self.image)
        self.image = utils.safe_gtk_image_load(path)
        self.pack_start(self.image, False)
        self.image.show()

    def _set_information(self, text):
        '''set the text on the information'''
        self._information.set_markup(text)

    def _get_information(self):
        '''return the text on the information'''
        return self._information.get_markup()

    information = property(fget=_get_information, fset=_set_information)

class ContactInfo(gtk.VBox):
    '''a widget that contains the display pictures of the contacts and our
    own display picture'''

    def __init__(self, first=None, last=None):
        gtk.VBox.__init__(self)
        self._first = first
        self._last = last

        self._first_alig = None
        self._last_alig = None

    def _set_first(self, first):
        '''set the first element and add it to the widget (remove the
        previous if not None'''

        if self._first_alig is not None:
            self.remove(self._first_alig)

        self._first = first
        self._first_alig = gtk.Alignment(xalign=0.5, yalign=0.0, xscale=1.0,
            yscale=0.1)
        self._first_alig.add(self._first)
        self.pack_start(self._first_alig)

    def _get_first(self):
        '''return the first widget'''
        return self._first

    first = property(fget=_get_first, fset=_set_first)

    def _set_last(self, last):
        '''set the last element and add it to the widget (remove the
        previous if not None'''

        if self._last_alig is not None:
            self.remove(self._last_alig)

        self._last = last
        self._last_alig = gtk.Alignment(xalign=0.5, yalign=1.0, xscale=1.0,
            yscale=0.1)
        self._last_alig.add(self._last)
        self.pack_start(self._last_alig)

    def _get_last(self):
        '''return the last widget'''
        return self._last

    last = property(fget=_get_last, fset=_set_last)

class TabWidget(gtk.HBox):
    '''a widget that is placed on the tab on a notebook'''

    def __init__(self, text, on_tab_menu, on_close_clicked, conversation):
        '''constructor'''
        gtk.HBox.__init__(self)
        self.set_spacing(4)

        event = gtk.EventBox()
        event.set_events(gtk.gdk.BUTTON_RELEASE_MASK)
        event.connect('button_release_event', on_tab_menu, conversation)

        self.image = gtk.Image()
        self.label = gtk.Label(text)
        self.close = TinyButton.TinyButton(gtk.STOCK_CLOSE)
        self.close.connect('button_press_event', on_close_clicked,
            conversation)

        self.label.set_max_width_chars(20)
        self.label.set_use_markup(True)

        event.add(self.label)

        self.pack_start(self.image, False)
        self.pack_start(event, True, True)
        self.pack_start(self.close, False)

        event.show()
        self.image.show()
        self.label.show()
        self.close.show()

    def set_image(self, path):
        '''set the image from path'''
        if utils.file_readable(path):
            self.image.set_from_file(path)
            self.image.show()
            return True

        return False

    def set_text(self, text):
        '''set the text of the label'''
        self.label.set_markup(gobject.markup_escape_text(text))

