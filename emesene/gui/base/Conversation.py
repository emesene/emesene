'''base implementation of a conversation, it should contain all the logic
derived classes should implement the GUI to operate the conversation and
nothing more'''
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

import extension
import e3
import gui
import MarkupParser

from e3.common.RingBuffer import RingBuffer

import logging
log = logging.getLogger('gui.base.Conversation')

class Conversation(object):
    '''a widget that contains all the components inside'''

    def __init__(self, session, cid, update_window, members=None):
        '''constructor'''
        self.update_window = update_window
        self.session = session
        self.caches = e3.cache.CacheManager(self.session.config_dir.base_dir)
        self.emcache = self.caches.get_emoticon_cache(self.session.account.account)

        self.cid = float(cid)
        self.icid = self.cid
        self.formatter = e3.common.MessageFormatter(session.contacts.me)
        self.first = True

        self._header_visible = True
        self._image_visible = True
        self._toolbar_visible = True

        self._message_waiting = True

        buffer_size = session.config.get_or_set("i_msg_history_size", 5)
        self.messages = RingBuffer(max=buffer_size)
        self.message_offset = 0

        if members is None:
            self.members = []
        else:
            self.members = members

        self._style = None

        # the base class should override this attributes
        self.info = None
        self.input = None
        self.output = None
        self.soundPlayer = extension.get_and_instantiate('sound', session)

    def subscribe_signals(self):
        ''' subscribes current session's signals '''
        self.session.config.subscribe(self._on_avatarsize_changed,
            'i_conv_avatar_size')
        self.session.config.subscribe(self._on_show_toolbar_changed,
            'b_show_toolbar')
        self.session.config.subscribe(self._on_show_header_changed,
            'b_show_header')
        self.session.config.subscribe(self._on_show_info_changed,
            'b_show_info')
        self.session.config.subscribe(self._on_show_avatar_onleft,
            'b_avatar_on_left')
        self.session.config.subscribe(self._on_icon_size_change,
            'b_toolbar_small')
        self.session.signals.picture_change_succeed.subscribe(
            self.on_picture_change_succeed)
        self.session.signals.contact_attr_changed.subscribe(
            self.on_contact_attr_changed_succeed)

        self.session.signals.filetransfer_invitation.subscribe(
                self.on_filetransfer_invitation)
        self.session.signals.filetransfer_accepted.subscribe(
                self.on_filetransfer_accepted)
        self.session.signals.filetransfer_progress.subscribe(
                self.on_filetransfer_progress)
        self.session.signals.filetransfer_completed.subscribe(
                self.on_filetransfer_completed)
        self.session.signals.filetransfer_rejected.subscribe(
                self.on_filetransfer_rejected)
        self.session.signals.filetransfer_canceled.subscribe(
                self.on_filetransfer_canceled)

        self.session.signals.call_invitation.subscribe(
                self.on_call_invitation)

    def unsubscribe_signals(self):
        ''' unsubscribes current session's signals '''
        self.session.config.unsubscribe(self._on_avatarsize_changed,
            'i_conv_avatar_size')
        self.session.config.unsubscribe(self._on_show_toolbar_changed,
            'b_show_toolbar')
        self.session.config.unsubscribe(self._on_show_header_changed,
            'b_show_header')
        self.session.config.unsubscribe(self._on_show_info_changed,
            'b_show_info')
        self.session.config.unsubscribe(self._on_show_avatar_onleft,
            'b_avatar_on_left')
        self.session.config.unsubscribe(self._on_icon_size_change,
            'b_toolbar_small')
        self.session.signals.picture_change_succeed.unsubscribe(
            self.on_picture_change_succeed)
        self.session.signals.contact_attr_changed.unsubscribe(
            self.on_contact_attr_changed_succeed)

        self.session.signals.filetransfer_invitation.unsubscribe(
                self.on_filetransfer_invitation)
        self.session.signals.filetransfer_accepted.unsubscribe(
                self.on_filetransfer_accepted)
        self.session.signals.filetransfer_progress.unsubscribe(
                self.on_filetransfer_progress)
        self.session.signals.filetransfer_completed.unsubscribe(
                self.on_filetransfer_completed)
        self.session.signals.filetransfer_rejected.unsubscribe(
                self.on_filetransfer_rejected)
        self.session.signals.filetransfer_canceled.unsubscribe(
                self.on_filetransfer_canceled)

        self.session.signals.call_invitation.unsubscribe(
                self.on_call_invitation)

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
        font = self.session.config.get_or_set("font", "Sans")
        font_color = self.session.config.get_or_set("font_color", "#000000")
        font_size = self.session.config.get_or_set("i_font_size", 10)
        font_bold = self.session.config.get_or_set("b_font_bold", False)
        font_italic = self.session.config.get_or_set("b_font_italic", False)
        font_underline = self.session.config.get_or_set("b_font_underline",
                False)
        font_strike = self.session.config.get_or_set("b_font_strike", False)

        if self.session.config.i_font_size < 6 or \
                self.session.config.i_font_size > 32:
            font_size = self.session.config.i_font_size = 10

        try:
            color = e3.Color.from_hex(font_color)
        except ValueError:
            font_color = self.session.config.font_color = '#000000'
            color = e3.Color.from_hex(font_color)

        self.cstyle = e3.Style(font, color, font_bold, font_italic,
            font_underline, font_strike, font_size)

    def get_preview(self, completepath):
        return None

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

    def on_filetransfer_invite(self, filename, completepath):
        '''called when a filetransfer is issued'''
        self.session.filetransfer_invite(self.cid, self.members[0],
                filename, completepath, self.get_preview(completepath))

    def on_video_call(self):
        '''called when the user is requesting a video-only call'''
        raise NotImplementedError
		
    def on_toggle_avatar(self):
        '''hide or show the avatar bar'''
        raise NotImplementedError

    def on_voice_call(self):
        '''called when the user is requesting an audio-only call'''
        raise NotImplementedError

    def on_av_call(self):
        '''called when the user is requesting an audio-video call'''
        raise NotImplementedError

    def on_clean(self):
        '''called when the clean button is clicked'''
        self.output.clear()

    def on_block_user(self):
        '''blocks the first user of the conversation'''
        account = self.members[0]
        contact = self.session.contacts.contacts[account]

        if contact.blocked:
            self.session.unblock(account)
        else:
            self.session.block(account)

    def on_emote(self, emote):
        '''called when a emote is selected on the emote window'''
        self.input.append(emote)

    def on_notify_attention(self):
        '''called when the nudge button is clicked'''
        self.session.request_attention(self.cid)
        message = e3.Message(e3.Message.TYPE_NUDGE, '', None, None)
        message.body = _('You just sent a nudge!')
        self.output.information(self.formatter, self.session.contacts.me, message)

        self.play_nudge()

    def show(self):
        '''override the show method'''
        raise NotImplementedError("Method not implemented")

    def iconify(self):
        '''override the iconify method'''
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

    def set_sensitive(self, is_sensitive):
        """
        used to make the conversation insensitive while the conversation
        is still open while the user is disconnected and to set it back to
        sensitive when the user is reconnected
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

    def input_grab_focus(self):
        '''
        sets the focus on the input widget
        '''
        raise NotImplementedError("Method not implemented")

    def on_close(self):
        '''called when the conversation is closed'''
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

    is_group_chat = property(fget=_get_group_chat)

    def _on_send_message(self, text):
        '''method called when the user press enter on the input text'''
        cedict = self.emcache.parse()
        custom_emoticons = gui.base.MarkupParser.get_custom_emotes(text, cedict)

        self.session.send_message(self.cid, text, self.cstyle, cedict, custom_emoticons)
        message = e3.Message(e3.Message.TYPE_MESSAGE, text, None, self.cstyle)
        self.output.send_message(self.formatter, self.session.contacts.me,
                                 message, cedict, self.emcache.path, self.first)
        self.messages.push(text)
        self.play_send()
        self.first = False

    def on_receive_message(self, message, account, received_custom_emoticons):
        '''method called when a message arrives to the conversation'''
        contact = self.session.contacts.get(account)

        if contact is None:
            contact = e3.Contact(account)

        if message.type == e3.Message.TYPE_MESSAGE or message.type == e3.Message.TYPE_FLNMSG:
            if self.session.config.b_override_text_color:
                message.style.color = e3.base.Color.from_hex(self.session.config.override_text_color)

            user_emcache = self.caches.get_emoticon_cache(account)
            self.output.receive_message(self.formatter, contact, message,
                    received_custom_emoticons, user_emcache.path, self.first)
            self.play_type()

        elif message.type == e3.Message.TYPE_NUDGE:
            message.body = _('%s just sent you a nudge!') % (contact.display_name,)
            self.output.information(self.formatter, contact, message)
            self.play_nudge()

        self.first = False

    def on_send_message_failed(self, errorCode):
        '''method called when a message fails to be delivered'''
        contact = self.session.contacts.me
        message = e3.Message(e3.Message.TYPE_MESSAGE, '', None, None)
        message.body = _('Error delivering message')
        self.output.information(self.formatter, contact, message)

        self.first = False

    def on_user_typing(self, account):
        '''method called when a someone is typing'''
        raise NotImplementedError

    def _get_icon(self):
        '''return the icon that represent the current status of the
            conversation (the status of the contact on a single
            conversation, a group icon on group chat or a waiting icon)
        '''
        if self.message_waiting:
            icon = gui.theme.image_theme.new_message
        elif self.is_group_chat:
            icon = gui.theme.image_theme.group_chat
        elif len(self.members) == 1:
            contact = self.session.contacts.get(self.members[0])

            # can be false if we are un a group chat with someone we dont
            # have and the last contact leaves..
            if contact:
                stat = contact.status
            else:
                stat = e3.status.ONLINE

            icon = gui.theme.image_theme.status_icons.get(stat, e3.status.OFFLINE)
        else:
            log.debug('unknown state on Conversation._get_icon')
            return gui.theme.image_theme.connect

        return icon

    icon = property(fget=_get_icon)

    def _get_text(self):
        '''return the text that represent the conversation title'''
        if self.is_group_chat:
            text = _('Group chat')
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

    def update_p2p(self, account, _type, *what):
        ''' update the p2p data in the conversation (custom emoticons) '''
        self.output.update_p2p(account, _type, *what)

    def on_contact_joined(self, account):
        '''called when a contact joins the conversation'''
        if account not in self.members:
            self.members.append(account)
            contact = self.session.contacts.get(account)
            if contact and len(self.members) > 1:
                message = e3.base.Message(e3.base.Message.TYPE_MESSAGE, \
                _('%s has joined the conversation') % (contact.display_name), \
                account)
                self.output.information(self.formatter, contact, message)
        self.update_data()
        

    def on_contact_left(self, account):
        '''called when a contact leaves the conversation'''
        if len(self.members) > 1 and account in self.members:
            self.members.remove(account)
            self.update_data()
            contact = self.session.contacts.get(account)
            if contact:
                message = e3.base.Message(e3.base.Message.TYPE_MESSAGE, \
                _('%s has left the conversation') % (contact.display_name), \
                account)
                self.output.information(self.formatter, contact, message)

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
        if self.session.config.b_play_nudge:
            self.soundPlayer.play(gui.theme.sound_theme.sound_nudge)

    def play_send(self):
        """
        play the send sound
        """
        if self.session.config.b_play_send:
            self.soundPlayer.play(gui.theme.sound_theme.sound_send)

    def play_type(self):
        """
        play the receive sound
        """
        if self.session.config.b_play_type:
            self.soundPlayer.play(gui.theme.sound_theme.sound_type)

    def cycle_history(self, change=-1):
        """
        return one of the last N messages sent, the one returned
        is the one pointed by message_offset, every time you call
        this function it will go to the previous one, you can
        reset it using reset_message_offset.

        change is the direction of cycling, 1 will go forward
        -1 will go backwards

        if no message in the buffer return an empty string
        """
        self.message_offset += change

        try:
            self.input.text = self.messages.peak(self.message_offset)
        except IndexError:
            pass

    def reset_message_offset(self):
        self.message_offset = 0

    def _member_to_contact(self,member):
        return self.session.contacts.contacts[member]
