'''a module that define classes to build the conversation widget'''
import gtk
import pango
import gobject

import gui
import Menu
import utils
import e3common.MessageFormatter
import protocol.status

from RichBuffer import RichBuffer
from e3 import Message

import TinyButton

class MainConversation(gtk.Notebook):
    '''the main conversation, it only contains other widgets'''

    def __init__(self, session, on_last_close):
        '''class constructor'''
        gtk.Notebook.__init__(self)
        self.set_scrollable(True)
        self.popup_enable()

        self.session = session
        self.on_last_close = on_last_close

        self.formatter = e3common.MessageFormatter.MessageFormatter(
            session.contacts.me)

        self.conversations = {}
        if self.session:
            self.session.protocol.connect('conv-message', 
                self._on_message)
            self.session.protocol.connect('conv-contact-joined', 
                self._on_contact_joined)
            self.session.protocol.connect('conv-contact-left', 
                self._on_contact_left)
            self.session.protocol.connect('conv-group-started', 
                self._on_group_started)
            self.session.protocol.connect('conv-group-ended', 
                self._on_group_ended)
            self.session.protocol.connect('conv-message-send-failed', 
                self._on_message_send_failed)
            self.session.protocol.connect('contact-attr-changed', 
                self._on_contact_attr_changed)

        self.connect('switch-page', self._on_switch_page)

    def _on_message(self, protocol, args):
        '''called when a message is received'''
        (cid, account, message) = args
        conversation = self.conversations.get(float(cid), None)

        if conversation and message.type == Message.TYPE_MESSAGE:
            contact = self.session.contacts.get(account)

            if contact:
                nick = contact.display_name
            else:
                nick = account

            (is_raw, consecutive, outgoing, first, last) = \
                self.formatter.format(contact) 

            conversation.output.append_formatted(first)

            if is_raw:
                conversation.output.append(message.body)
            else:
                conversation.output.append(message.body, True,
                    *self.format_from_message(message))

            conversation.output.append_formatted(last)

            parent = self.get_parent()

            if not parent.is_active():
                parent.set_urgency_hint(True)
                conversation.message_waiting = True
        elif not conversation:
            print 'conversation', cid, 'not found'

    def _on_focus(self, widget, event):
        '''called when the widget receives the focus'''
        self.get_parent().set_urgency_hint(False)
        page_num = self.get_current_page()
        page = self.get_nth_page(page_num)
        page.message_waiting = False

    def _on_switch_page(self, notebook, page, page_num):
        '''called when the user changes the tab'''
        page = self.get_nth_page(page_num)
        page.message_waiting = False

    def _on_message_send_failed(self, protocol, args):
        '''called when a message is received'''
        (cid, message) = args
        conversation = self.conversations.get(float(cid), None)

        if conversation is not None:
            # TODO: use formatter here
            conversation.output.append('message could not be sent: ', True, 
                fg_color='#A52A2A', bold=True)
            conversation.output.append(message.body + '\n', True,  
                *self.format_from_message(message))
        else:
            print 'conversation', cid, 'not found'

    def _on_contact_joined(self, protocol, args):
        '''called when a contact join the conversation'''
        (cid, account) = args
        conversation = self.conversations.get(float(cid), None)

        if conversation:
            conversation.on_contact_joined(account)
        else:
            print 'on_contact_joined: conversation is None'

    def _on_contact_left(self, protocol, args):
        '''called when a contact leaves the conversation'''
        (cid, account) = args
        conversation = self.conversations.get(float(cid), None)

        if conversation:
            conversation.on_contact_left(account)
        else:
            print 'on_contact_left: conversation is None'

    def _on_group_started(self, protocol, args):
        '''called when a group conversation starts'''
        cid = args[0]
        conversation = self.conversations.get(float(cid), None)

        if conversation:
            conversation.on_group_started()

    def _on_group_ended(self, protocol, args):
        '''called when a group conversation ends'''
        cid = args[0]
        conversation = self.conversations.get(float(cid), None)

        if conversation:
            conversation.on_group_ended()

    def format_from_message(self, message):
        '''return a tuple containing all the format arguments received by
        RichBuffer.put_text'''
        stl = message.style

        result = ('#' + stl.color.to_hex(), None, stl.font, None, stl.bold, 
            stl.italic, stl.underline, stl.strike)
        return result

    def new_conversation(self, cid, members=None):
        '''create a new conversation widget and append it to the tabs, 
        if the cid already exists or there is already a conversation with
        that member, return the existing conversation.
        this method returns a tuple containing a boolean and a conversation
        object. If the conversation already exists, return True on as first
        value'''
        cid = float(cid)
        if cid in self.conversations:
            return (True, self.conversations[cid])
        elif members is not None:   
            for (key, conversation) in self.conversations.iteritems():
                if conversation.members == members:
                    return (True, conversation)

        conversation = Conversation(self.session, cid, None, self.formatter, 
            members)
        label = TabWidget('Connecting', self._on_tab_close, conversation)
        label.set_image(gui.theme.connect)
        conversation.tab_label = label
        self.conversations[cid] = conversation
        self.append_page_menu(conversation, label)
        self.set_tab_label_packing(conversation, True, True, gtk.PACK_START)
        self.set_tab_reorderable(conversation, True)
        return (False, conversation)

    def _on_contact_attr_changed(self, protocol, args):
        '''called when an attribute of a contact changes'''
        account = args[0]

        for conversation in self.conversations.values():
            if account in conversation.members:
                conversation.update_data()

    def _on_tab_close(self, button, event, conversation):
        '''called when the user clicks the close button on a tab'''
        # TODO: we can check the last message timstamp and if it's less than
        # certains seconds, inform that there is a new message (to avoid 
        # closing a tab instants after you receive a new message)
        self.close(conversation)

        if self.get_n_pages() == 0:
            self.on_last_close()

    def close(self, conversation):
        '''close a conversation'''
        self.session.close_conversation(conversation.cid)
        page_num = self.page_num(conversation)
        self.remove_page(page_num)
        del self.conversations[conversation.cid]

    def close_all(self):
        '''close and finish all conversations'''
        conversations = self.conversations.values()
        for conversation in conversations:
            self.close(conversation)


class Conversation(gtk.VBox):
    '''a widget that contains all the components inside'''

    def __init__(self, session, cid, tab_label, formatter, members=None):
        '''constructor'''
        gtk.VBox.__init__(self)
        self.set_border_width(1)

        self.session = session
        self.tab_label = tab_label
        self.cid = float(cid)
        self.formatter = formatter

        self._message_waiting = False

        if members is None:
            self.members = []
        else:
            self.members = members

        self.panel = gtk.VPaned()
        self.header = Header()
        self.output = OutputText()
        self.output.textbox.connect('button-press-event' , 
            self._on_button_press_event)
        self.input = InputText(self._on_send_message)
        self.info = ContactInfo()

        self.panel.pack1(self.output, True, True)
        self.panel.pack2(self.input, True, True)

        hbox = gtk.HBox()
        hbox.pack_start(self.panel, True, True)
        hbox.pack_start(self.info, False)

        self.pack_start(self.header, False)
        self.pack_start(hbox, True, True)

        self.temp = self.panel.connect('map-event', self._on_panel_show)

        if len(self.members) == 0:
            self.header.information = Header.INFO_TPL % \
                ('connecting', 'creating conversation', '')

        self.header.set_image(gui.theme.user)
        self.info.first = utils.safe_gtk_image_load(gui.theme.logo)
        self.info.last = utils.safe_gtk_image_load(gui.theme.logo)

        self.output.grab_focus()

    def _get_message_waiting(self):
        '''return True if a message is waiting'''
        return self._message_waiting

    def _set_message_waiting(self, value):
        '''set the value of message waiting, update the gui to reflect
        the value'''
        self._message_waiting = value
        self.update_tab()

    message_waiting = property(fget=_get_message_waiting, 
        fset=_set_message_waiting)

    def _get_group_chat(self):
        '''return True if the conversation contains more than one member,
        false otherwise'''

        return len(self.members) > 1

    group_chat = property(fget=_get_group_chat)

    def _on_panel_show(self, widget, event):
        '''callback called when the panel is shown, resize the panel'''
        position = self.panel.get_position()
        self.panel.set_position(position + int(position * 0.6))
        self.panel.disconnect(self.temp)
        del self.temp

    def _on_send_message(self, text):
        '''method called when the user press enter on the input text'''
        self.session.send_message(self.cid, text)
        nick = self.session.contacts.me.display_name

        (is_raw, consecutive, outgoing, first, last) = \
            self.formatter.format(self.session.contacts.me) 

        self.output.append_formatted(first)

        if is_raw:
            self.output.append(text)
        else:
            self.output.append(text) 
            # TODO: format here
                #, True, *self.format_from_message(message))

        self.output.append_formatted(last)

    def _on_button_press_event(self, widget, event):
        '''callback called when the user press a button over a widget
        chek if it's the right button and display the menu'''
        if event.button == 3:
            menu_ = gui.ConversationMenu(None, None, None)
            menu = Menu.build_pop_up(menu_)
            menu.popup(None, None, None, 0, 0)
            print 'hola'
            return True

    def update_data(self):
        '''update the data on the conversation'''
        if len(self.members) == 1:
            self.set_data(self.members[0])
        elif len(self.members) > 1:
            self.set_group_data()

    def update_tab(self):
        '''update the values of the tab'''
        if self.message_waiting:
            self.tab_label.set_image(gui.theme.new_message) 
        elif self.group_chat:
            self.tab_label.set_text('Group chat')
            self.tab_label.set_image(gui.theme.group_chat)
        elif len(self.members) == 1:
            contact = self.session.contacts.get(self.members[0])

            # can be false if we are un a group chat with someone we dont 
            # have and the last contact leaves..
            if contact:
                nick = contact.display_name
                stat = contact.status
            else:
                nick = self.members[0]
                stat = protocol.status.ONLINE

            self.tab_label.set_text(nick)
            self.tab_label.set_image(gui.theme.status_icons.get(stat, 
                protocol.status.OFFLINE))

    def on_contact_joined(self, account):
        '''called when a contact joins the conversation'''
        if account not in self.members:
            self.members.append(account)

        self.update_data()

    def on_contact_left(self, account):
        '''called when a contact lefts the conversation'''
        if account in self.members:
            self.members.remove(account)

        self.update_data()

    def on_group_started(self):
        '''called when a group conversation starts'''
        self.update_data()

    def on_group_ended(self):
        '''called when a group conversation ends'''
        self.update_data()

    def set_data(self, account):
        '''set the data of the conversation to the data of the account'''
        contact = self.session.contacts.get(account)

        if contact:
            message = gobject.markup_escape_text(contact.message)
            nick = gobject.markup_escape_text(contact.display_name)
        else:
            message = ''
            nick = account

        self.header.information = Header.INFO_TPL % (nick, message, account)
        self.update_tab()

    def set_group_data(self):
        '''set the data of the conversation to reflect a group chat'''
        self.header.set_image(gui.theme.users)
        text = 'Group chat'

        self.header.information = Header.INFO_TPL % \
            (text, '%d members' % (len(self.members) + 1,), '')

        self.update_tab()

class TextBox(gtk.ScrolledWindow):
    '''a text box inside a scroll that provides methods to get and set the
    text in the widget'''

    def __init__(self):
        '''constructor'''
        gtk.ScrolledWindow.__init__(self)
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.set_shadow_type(gtk.SHADOW_IN)
        self.textbox = gtk.TextView()
        self.textbox.set_left_margin(6)
        self.textbox.set_right_margin(6)
        self.textbox.set_wrap_mode(gtk.WRAP_WORD_CHAR)
        self.textbox.show()
        self.buffer = RichBuffer()
        self.textbox.set_buffer(self.buffer)
        self.add(self.textbox)

    def clear(self):
        '''clear the content'''
        self.buffer.set_text('')

    def append(self, text, scroll=True, fg_color=None, bg_color=None, 
        font=None, size=None, bold=False, italic=False, underline=False, 
        strike=False):
        '''append text to the widget'''
        self.buffer.put_text(text, fg_color, bg_color, font, size, bold, 
            italic, underline, strike)

        if scroll:
            self.scroll_to_end()

    def append_formatted(self, text, scroll=True):
        '''append formatted text to the widget'''
        self.buffer.put_formatted(text)

        if scroll:
            self.scroll_to_end()

    def scroll_to_end(self):
        '''scroll to the end of the content'''
        end_iter = self.buffer.get_end_iter()
        self.textbox.scroll_to_iter(end_iter, 0.0, yalign=1.0)

    def _set_text(self, text):
        '''set the text on the widget'''
        self.buffer.set_text(text)

    def _get_text(self):
        '''return the text of the widget'''
        start_iter = self.buffer.get_start_iter()
        end_iter = self.buffer.get_end_iter()
        return self.buffer.get_text(start_iter, end_iter, True)

    text = property(fget=_get_text, fset=_set_text)

class InputText(TextBox):
    '''a widget that is used to insert the messages to send'''

    def __init__(self, on_send_message):
        '''constructor'''
        TextBox.__init__(self)
        self.on_send_message = on_send_message
        self.textbox.connect('key-press-event', self._on_key_press_event)

    def _on_key_press_event(self, widget, event):
        '''method called when a key is pressed on the input widget'''
        if event.keyval == gtk.keysyms.Return and \
                not event.state == gtk.gdk.SHIFT_MASK:
            if not self.text:
                return True

            self.on_send_message(self.text)
            self.text = ''
            return True

class OutputText(TextBox):
    '''a widget that is used to display the messages on the conversation'''

    def __init__(self):
        '''constructor'''
        TextBox.__init__(self)
        self.textbox.set_editable(False)
        self.textbox.set_cursor_visible(False)

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

    def __init__(self, text, on_close_clicked, *args):
        '''constructor'''
        gtk.HBox.__init__(self)
        self.set_spacing(4)

        self.image = gtk.Image()
        self.label = gtk.Label(text)
        self.close = TinyButton.TinyButton(gtk.STOCK_CLOSE)
        self.close.connect('button_press_event', on_close_clicked, *args)

        self.label.set_max_width_chars(20)
        self.label.set_use_markup(True)

        self.pack_start(self.image, False)
        self.pack_start(self.label, True, True)
        self.pack_start(self.close, False)

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
        self.label.set_markup(text)


if __name__ == '__main__':
    import gui
    mconv = MainConversation(None) 
    conv = mconv.new_conversation(123)
    mconv.new_conversation(1233)
    window = gtk.Window()
    window.add(mconv)
    window.set_default_size(640, 480)
    mconv.show_all()
    window.show()
    gtk.main()
