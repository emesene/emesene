import e3
import gui
import extension
import MarkupParser

import logging
log = logging.getLogger('gui.base.Conversation')

class Conversation(object):
    '''a widget that contains all the components inside'''

    def __init__(self, session, cid, members=None):
        '''constructor'''
        self.session = session
        self.cid = float(cid)
        self.formatter = e3.common.MessageFormatter(session.contacts.me)
        self.first = True

        self._header_visible = True
        self._image_visible = True
        self._toolbar_visible = True

        self._message_waiting = False

        if members is None:
            self.members = []
        else:
            self.members = members

        self._style = None

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

    cstyle = property(fget=_get_style, fset=_set_style)

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

        try:
            color = e3.Color.from_hex(font_color)
        except ValueError:
            self.session.config.font_color = '#000000'
            font_color = self.session.config.font_color
            color = e3.Color.from_hex(font_color)

        self.cstyle = e3.Style(font, color, font_bold, font_italic,
            font_underline, font_strike, font_size)

    def on_font_selected(self, style):
        '''called when a new font is selected'''
        self.cstyle = style

    def on_color_selected(self, color):
        '''called when a new font is selected'''
        self.cstyle.color = color
        self.session.config.font_color = '#' + color.to_hex()
        self.input.update_style(self.cstyle)

    def on_style_selected(self, style):
        '''called when a new font is selected'''
        self.cstyle = style

    def on_invite(self, account):
        '''called when a contact is selected to be invited'''
        self.session.conversation_invite(self.cid, account)

    def on_clean(self):
        '''called when the clean button is clicked'''
        self.output.clear()

    def on_emote(self, emote):
        '''called when a emote is selected on the emote window'''
        self.input.append(emote)

    def on_notify_attention(self):
        '''called when the nudge button is clicked'''
        self.session.request_attention(self.cid)
        self.output.append(
            self.formatter.format_information('you just sent a nudge!'),self.session.config.b_allow_auto_scroll)
        self.play_nudge()

    def show(self):
        '''override the show method'''
        raise NotImplementedError("Method not implemented")

    def update_message_waiting(self, is_waiting):
        """
        update the information on the conversation to inform if a message is waiting

        is_waiting -- boolean value that indicates if a message is waiting
        """
        raise NotImplementedError("Method not implemented")

    def update_single_information(self, nick, message, account):
        """
        update the information for a conversation with a single user

        nick -- the nick of the other account (escaped)
        message -- the message of the other account (escaped)
        account -- the account
        """
        raise NotImplementedError("Method not implemented")

    def update_group_information(self):
        """
        update the information for a conversation with multiple users
        """
        raise NotImplementedError("Method not implemented")

    def set_image_visible(self, is_visible):
        """
        set the visibility of the widget that displays the images of the members

        is_visible -- boolean that says if the message should be shown or hidden
        """
        raise NotImplementedError("Method not implemented")

    def set_header_visible(self, is_visible):
        '''
        hide or show the widget according to is_visible

        is_visible -- boolean that says if the widget should be shown or hidden
        '''
        raise NotImplementedError("Method not implemented")

    def set_toolbar_visible(self, is_visible):
        '''
        hide or show the widget according to is_visible

        is_visible -- boolean that says if the widget should be shown or hidden
        '''
        raise NotImplementedError("Method not implemented")

    def _get_message_waiting(self):
        '''return True if a message is waiting'''
        return self._message_waiting

    def _set_message_waiting(self, value):
        '''set the value of message waiting, update the gui to reflect
        the value'''
        self._message_waiting = value
        self.update_message_waiting(value)

    message_waiting = property(fget=_get_message_waiting,
        fset=_set_message_waiting)

    def _get_group_chat(self):
        '''return True if the conversation contains more than one member,
        false otherwise'''

        return len(self.members) > 1

    group_chat = property(fget=_get_group_chat)

    def _on_send_message(self, text, cedict=None):
        '''method called when the user press enter on the input text'''
        self.session.send_message(self.cid, text, self.cstyle)
        nick = self.session.contacts.me.display_name

        (is_raw, consecutive, outgoing, first, last) = \
            self.formatter.format(self.session.contacts.me)

        if is_raw:
            middle = MarkupParser.escape(text)
        else:
            middle = MarkupParser.escape(text)
            middle = e3.common.add_style_to_message(middle, self.cstyle, False)

        all_ = first + middle + last
        self.output.append(all_, cedict, self.session.config.b_allow_auto_scroll)
        self.play_type()
        self.first = False

    def on_receive_message(self, message, account, cedict):
        '''method called when a message arrives to the conversation'''
        contact = self.session.contacts.get(account)

        if contact:
            nick = contact.display_name
        else:
            nick = account
            contact = e3.Contact(account)

        msg = gui.Message.from_contact(contact, message.body, self.first, True)
        self.first = False

        if message.type == e3.Message.TYPE_MESSAGE:
            (is_raw, consecutive, outgoing, first, last) = \
                self.formatter.format(contact)

            middle = MarkupParser.escape(message.body)
            if not is_raw:
                middle = self.format_from_message(message)

            self.output.append(first + middle + last, cedict, self.session.config.b_allow_auto_scroll)
            self.play_send()

        elif message.type == e3.Message.TYPE_NUDGE:
            self.output.append(
                self.formatter.format_information(
                    '%s just sent you a nudge!' % (nick,)), self.session.config.b_allow_auto_scroll)
            self.play_nudge()

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
                stat = e3.status.ONLINE

            icon = gui.theme.status_icons.get(stat, e3.status.OFFLINE)
        else:
            log.debug('unknown state on Conversation._get_icon')
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
            log.debug('unknown state on Conversation._get_text')
            text = '(?)'

        return text

    text = property(fget=_get_text)

    def update_data(self):
        '''update the data on the conversation'''
        if len(self.members) == 1:
            self._update_single_information(self.members[0])
        elif len(self.members) > 1:
            self.update_group_information()

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

    def _update_single_information(self, account):
        '''set the data of the conversation to the data of the account'''
        contact = self.session.contacts.get(account)

        if contact:
            message = MarkupParser.escape(contact.message)
            nick = MarkupParser.escape(contact.display_name)
        else:
            message = ''
            nick = account

        self.update_single_information(nick, message, account)

    def _set_image_visible(self, value):
        '''hide or show the widget according to value'''
        self.set_image_visible(value)
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
        self.set_header_visible(value)
        self._header_visible = value

    def _get_header_visible(self):
        '''return the value of image_visible'''
        return self._header_visible

    header_visible = property(fget=_get_header_visible,
        fset=_set_header_visible)

    def _set_toolbar_visible(self, value):
        '''hide or show the widget according to value'''
        self.set_toolbar_visible(value)
        self._toolbar_visible = value

    def _get_toolbar_visible(self):
        '''return the value of image_visible'''
        return self._toolbar_visible

    toolbar_visible = property(fget=_get_toolbar_visible,
        fset=_set_toolbar_visible)

    def play_nudge(self):
        """
        play the nudge sound
        """
        gui.play(self.session, gui.theme.sound_nudge)

    def play_send(self):
        """
        play the send sound
        """
        gui.play(self.session, gui.theme.sound_send)

    def play_type(self):
        """
        play the send sound
        """
        gui.play(self.session, gui.theme.sound_type)

    def format_from_message(self, message):
        '''return a markup text representing the format on the message'''
        return e3.common.add_style_to_message(message.body, message.style)

