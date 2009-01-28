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
import protocol
import protocol.status

from e3 import Message

import TinyButton

class MainConversation(gtk.Notebook):
    '''the main conversation, it only contains other widgets'''

    def __init__(self, session, on_last_close):
        '''class constructor'''
        gtk.Notebook.__init__(self)
        self.set_scrollable(True)

        self.session = session
        self.on_last_close = on_last_close

        self.conversations = {}
        if self.session:
            self.session.signals.connect('conv-message',
                self._on_message)
            self.session.signals.connect('conv-contact-joined',
                self._on_contact_joined)
            self.session.signals.connect('conv-contact-left',
                self._on_contact_left)
            self.session.signals.connect('conv-group-started',
                self._on_group_started)
            self.session.signals.connect('conv-group-ended',
                self._on_group_ended)
            self.session.signals.connect('conv-message-send-failed',
                self._on_message_send_failed)
            self.session.signals.connect('contact-attr-changed',
                self._on_contact_attr_changed)

        self.connect('switch-page', self._on_switch_page)

    def _on_message(self, protocol, args):
        '''called when a message is received'''
        (cid, account, message) = args
        conversation = self.conversations.get(float(cid), None)

        if conversation is None:
            (exists, conversation) = self.new_conversation(cid, [account])

        contact = self.session.contacts.get(account)

        if message.type == Message.TYPE_MESSAGE:

            if contact:
                nick = contact.display_name
            else:
                nick = account

            (is_raw, consecutive, outgoing, first, last) = \
                conversation.formatter.format(contact)

            middle = e3common.MarkupParser.escape(message.body)
            if not is_raw:
                middle = self.format_from_message(message)

            conversation.output.append(first + middle + last)

        elif message.type == Message.TYPE_NUDGE:
            (is_raw, consecutive, outgoing, first, last) = \
                conversation.formatter.format(contact, message.type)
            conversation.output.append(first)

        parent = self.get_parent()

        if parent is not None and not parent.is_active():
            parent.set_urgency_hint(True)
            conversation.message_waiting = True

    def _on_focus(self, widget, event):
        '''called when the widget receives the focus'''
        self.get_parent().set_urgency_hint(False)
        page_num = self.get_current_page()
        if page_num != -1:
            page = self.get_nth_page(page_num)
            page.message_waiting = False

    def _on_switch_page(self, notebook, page, page_num):
        '''called when the user changes the tab'''
        page = self.get_nth_page(page_num)
        page.message_waiting = False
        parent = self.get_parent()
        parent.set_title(page.text)
        parent.set_icon(page.icon)

    def _on_message_send_failed(self, protocol, args):
        '''called when a message is received'''
        (cid, message) = args
        conversation = self.conversations.get(float(cid), None)

        if conversation is not None:
            error = conversation.formatter.format_error(
                'message couldn\'t be sent: ')
            conversation.output.append(error)
            conversation.output.append(
                self.format_from_message(message))
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
        '''return a markup text representing the format on the message'''
        return utils.add_style_to_message(message.body, message.style)

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
                    old_cid = conversation.cid

                    if old_cid in self.conversations:
                        del self.conversations[old_cid]

                    conversation.cid = cid
                    self.conversations[cid] = conversation
                    return (True, conversation)

        conversation = Conversation(self.session, cid, None, members)
        label = TabWidget('Connecting', self._on_tab_menu, self._on_tab_close,
            conversation)
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

    def _on_tab_menu(self, widget, event, conversation):
        '''called when the user right clicks on the tab'''
        if event.button == 3:
            conversation.show_tab_menu()

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

    def __init__(self, session, cid, tab_label, members=None):
        '''constructor'''
        gtk.VBox.__init__(self)
        self.set_border_width(1)

        self.session = session
        self.tab_label = tab_label
        self.cid = float(cid)
        self.formatter = e3common.MessageFormatter.MessageFormatter(
            session.contacts.me)

        self._header_visible = True
        self._image_visible = True
        self._toolbar_visible = True

        self._message_waiting = False

        if members is None:
            self.members = []
        else:
            self.members = members

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

        self._style = None
        self._load_style()


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

    def _get_style(self):
        '''return the value of style'''
        return self._style

    def _set_style(self, style):
        '''set the value of style and update the style on input'''
        self._style = style
        self.session.config.font = style.font
        self.session.config.i_font_size = style.size
        self.session.config.b_font_bold = style.bold
        self.session.config.b_font_italic = style.italic
        self.session.config.b_font_underline = style.underline
        self.session.config.b_font_strike = style.strike
        self.session.config.font_color = '#' + style.color.to_hex()
        self.input.update_style(style)

    style = property(fget=_get_style, fset=_set_style)

    def _load_style(self):
        '''load the default style from the configuration'''
        if self.session.config.font is None:
            self.session.config.font = 'Sans'

        if self.session.config.i_font_size is None:
            self.session.config.i_font_size = 10
        elif self.session.config.i_font_size < 6 or \
                self.session.config.i_font_size > 32: 
            self.session.config.i_font_size = 10 

        if self.session.config.b_font_bold is None:
            self.session.config.b_font_bold = False

        if self.session.config.b_font_italic is None:
            self.session.config.b_font_italic = False

        if self.session.config.b_font_underline is None:
            self.session.config.b_font_underline = False

        if self.session.config.b_font_strike is None:
            self.session.config.b_font_strike = False

        if self.session.config.font_color is None:
            self.session.config.font_color = '#000000'

        font = self.session.config.font
        font_size = self.session.config.i_font_size
        font_bold = self.session.config.b_font_bold
        font_italic = self.session.config.b_font_italic
        font_underline = self.session.config.b_font_underline
        font_strike = self.session.config.b_font_strike
        font_color = self.session.config.font_color
        color = protocol.Color.from_hex(font_color)

        self.style = protocol.Style(font, color, font_bold, font_italic, 
            font_underline, font_strike, font_size)

    def on_font_selected(self, style):
        '''called when a new font is selected'''
        self.style = style

    def on_color_selected(self, color):
        '''called when a new font is selected'''
        self.style.color = color
        self.session.config.font_color = '#' + color.to_hex()
        self.input.update_style(self.style)

    def on_style_selected(self, style):
        '''called when a new font is selected'''
        self.style = style

    def on_invite(self, account):
        '''called when a contact is selected to be invited'''
        self.session.conversation_invite(account)

    def on_clean(self):
        '''called when the clean button is clicked'''
        self.output.clear()

    def on_emote(self, emote):
        '''called when a emote is selected on the emote window'''
        self.input.append(emote)

    def on_notify_atention(self):
        '''called when the nudge button is clicked'''
        print 'nudge!'

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
        self.panel.disconnect(self._panel_show_id)
        del self._panel_show_id

    def _on_send_message(self, text):
        '''method called when the user press enter on the input text'''
        self.session.send_message(self.cid, text, self.style)
        nick = self.session.contacts.me.display_name

        (is_raw, consecutive, outgoing, first, last) = \
            self.formatter.format(self.session.contacts.me)

        if is_raw:
            middle = e3common.MarkupParser.escape(text)
        else:
            middle = e3common.MarkupParser.escape(text)
            middle = utils.add_style_to_message(middle, self.style, False)

        all = first + middle + last
        self.output.append(all)

    def show_tab_menu(self):
        '''callback called when the user press a button over a widget
        chek if it's the right button and display the menu'''
        pass

    def _get_icon(self):
        '''return the icon that represent the current status of the
            conversation (the status of the contact on a single
            conversation, a group icon on group chat or a waiting icon)
        '''
        if self.message_waiting:
            icon = gui.theme.new_message
        elif self.group_chat:
            icon = gui.theme.group_chat
        elif len(self.members) == 1:
            contact = self.session.contacts.get(self.members[0])

            # can be false if we are un a group chat with someone we dont
            # have and the last contact leaves..
            if contact:
                stat = contact.status
            else:
                stat = protocol.status.ONLINE

            icon = gui.theme.status_icons.get(stat, protocol.status.OFFLINE)
        else:
            print 'unknown state on Conversation._get_icon'
            return gui.theme.connect

        return icon

    icon = property(fget=_get_icon)

    def _get_text(self):
        '''return the text that represent the conversation title'''
        if self.group_chat:
            text = 'Group chat'
        elif len(self.members) == 1:
            contact = self.session.contacts.get(self.members[0])

            # can be false if we are un a group chat with someone we dont
            # have and the last contact leaves..
            if contact:
                text = contact.display_name
            else:
                text = self.members[0]
        else:
            print 'unknown state on Conversation._get_text'
            text = '(?)'

        return text

    text = property(fget=_get_text)

    def update_data(self):
        '''update the data on the conversation'''
        if len(self.members) == 1:
            self.set_data(self.members[0])
        elif len(self.members) > 1:
            self.set_group_data()

    def update_tab(self):
        '''update the values of the tab'''
        self.tab_label.set_image(self.icon)
        self.tab_label.set_text(self.text)

    def on_contact_joined(self, account):
        '''called when a contact joins the conversation'''
        if account not in self.members:
            self.members.append(account)

        self.update_data()

    def on_contact_left(self, account):
        '''called when a contact lefts the conversation'''
        if account in self.members and len(self.members) > 1:
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

    def _set_image_visible(self, value):
        '''hide or show the widget according to value'''
        if value:
            self.info.show()
        else:
            self.info.hide()

        self._image_visible = value

    def _get_image_visible(self):
        '''return the value of image_visible'''
        return self._image_visible

    image_visible = property(fget=_get_image_visible,
        fset=_set_image_visible)
   
    def _set_header_visible(self, value):
        '''hide or show the widget according to value'''
        if value:
            self.header.show()
        else:
            self.header.hide()

        self._header_visible = value

    def _get_header_visible(self):
        '''return the value of image_visible'''
        return self._header_visible

    header_visible = property(fget=_get_header_visible,
        fset=_set_header_visible)

    def _set_toolbar_visible(self, value):
        '''hide or show the widget according to value'''
        if value:
            self.toolbar.show()
        else:
            self.toolbar.hide()

        self._toolbar_visible = value

    def _get_toolbar_visible(self):
        '''return the value of image_visible'''
        return self._toolbar_visible

    toolbar_visible = property(fget=_get_toolbar_visible,
        fset=_set_toolbar_visible)



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
