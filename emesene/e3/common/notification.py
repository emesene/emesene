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

from e3 import Message, status
import extension
import gui
import logging
import time

log = logging.getLogger('e3.common.notification')

#TODO add config
#TODO update multiple message on notification
class Notification():
    '''emesene's notification system'''
    NAME = 'Notification'
    DESCRIPTION = 'emesene\'s notification system'
    AUTHOR = 'Cando'
    WEBSITE = 'www.emesene.org'

    def __init__(self, session):
        """
        Class Constructor
        """
        self.session = session
        self.session.config.get_or_set('b_notify_contact_online', True)
        self.session.config.get_or_set('b_notify_contact_offline', True)
        self.session.config.get_or_set('b_notify_receive_message', True)
        self.session.config.get_or_set('b_notify_typing', False)
        self.session.config.get_or_set('b_notify_when_focussed', False)
        self.session.config.get_or_set('b_notify_only_when_available', True)

        self.notifier = extension.get_default('notificationGUI')
        self.picture_factory = extension.get_default('notificationImage')
        self.sound_player = extension.get_and_instantiate('sound', session)

        if self.session:
            self.session.signals.conv_message.subscribe(
                self._on_message)
            self.session.signals.user_typing.subscribe(
                self._on_user_typing)
            self.session.signals.contact_attr_changed.subscribe(
                self._on_contact_attr_changed)
            self.session.signals.mail_received.subscribe(
                self._on_mail_received)
            self.session.signals.filetransfer_completed.subscribe(
                self._on_filetransfer_completed)
            self.session.signals.filetransfer_canceled.subscribe(
                self._on_filetransfer_canceled)
            self.session.signals.filetransfer_invitation.subscribe(
                self._on_filetransfer_invitation)

        self.notify_online = False
        self.last_online = None

    def remove_subscriptions(self):
        if self.session:
            self.session.signals.conv_message.unsubscribe(
                self._on_message)
            self.session.signals.user_typing.unsubscribe(
                self._on_user_typing)
            self.session.signals.contact_attr_changed.unsubscribe(
                self._on_contact_attr_changed)
            self.session.signals.mail_received.unsubscribe(
                self._on_mail_received)
            self.session.signals.filetransfer_completed.unsubscribe(
                self._on_filetransfer_completed)
            self.session.signals.filetransfer_canceled.unsubscribe(
                self._on_filetransfer_canceled)
            self.session.signals.filetransfer_invitation.unsubscribe(
                self._on_filetransfer_invitation)

    def _on_filetransfer_completed(self, args):
        uri = self.picture_factory('notification-message-email', 'mail-received')
        self.notifier(_("File transfer successful"), "", uri,
                      'file-transf-completed')

    def _on_filetransfer_canceled(self, args):
        uri = self.picture_factory('notification-message-email', 'mail-received')
        self.notifier(_("File transfer canceled"), "", uri,
                      'file-transf-canceled')

    def _on_filetransfer_invitation(self, arg1, arg2):

        if isinstance(arg1.sender, str): # prevent notifying when we send a file
            return

        contact = self.session.contacts.get(arg1.sender.account)
        self._notify(contact, contact.nick, _("File transfer invitation"), arg1.sender.account)

    def _on_user_typing(self, cid, account, *args):
        ''' called when a user is typing '''
        if self.session.config.b_notify_typing:
            contact = self.session.contacts.get(account)
            self._notify(contact, contact.nick, _("is typing a message"), account)

    def _on_mail_received(self, message):
        ''' called when a new mail is received '''
        uri = self.picture_factory('notification-message-email', 'mail-received')
        self.notifier(_("New mail from %s") % (message.address),
                      message._subject, uri, 'mail-received', None,
                      message.address)

    def _on_message(self, cid, account, msgobj, cedict={}):
        """
        This is called when a new message arrives to a user.
        """
        conversation = self.session.get_conversation(cid, [account])
        contact = self.session.contacts.get(account)

        text = None
        check = False
        if conversation:
            check = conversation.message_waiting or self.session.config.b_notify_when_focussed

        if self.session.config.b_notify_receive_message and check:
            if msgobj.type == Message.TYPE_NUDGE:
                # TODO: unplus contact.nick, so we don't display weird tags
                text = _('%s just sent you a nudge!') % (msgobj.display_name,)
            else:
                text = msgobj.body

        self._notify(contact, msgobj.display_name, text, msgobj.account)

    def _on_contact_attr_changed(self, account, change_type, old_value,
            do_notify=True):
        """
        This is called when an attribute of a contact changes
        """
        if change_type != 'status':
            return

        contact = self.session.contacts.get(account)
        if not contact:
            return

        if contact.status != status.OFFLINE and old_value == status.OFFLINE:
            def _do_notify_online():
                text = None
                sound = None
                if self.session.config.b_notify_contact_online:
                    text = _('is online')
                if self.session.config.b_play_contact_online:
                    sound = gui.theme.sound_theme.sound_online
                self._notify(contact, contact.nick, text, contact.account, sound)

            if not self.notify_online:
                # detects the first notification flood and enable the
                # online notifications after it to prevent log in flood
                if self.last_online is not None:
                    t = time.time()
                    if (t - self.last_online > 2):
                        self.notify_online = True
                        _do_notify_online()
                    self.last_online = t
                else:
                    self.last_online = time.time()
            else:
                _do_notify_online()
        elif contact.status == status.OFFLINE:
            text = None
            sound = None
            if self.session.config.b_notify_contact_offline:
                text = _('is offline')
            if self.session.config.b_play_contact_offline:
                sound = gui.theme.sound_theme.sound_offline

            self._notify(contact, contact.nick, text, contact.account, sound)

    def _notify(self, contact, title, text, tooltip, sound=None):
        """
        This creates and shows the nofification
        """
        only_when_available = self.session.config.b_notify_only_when_available
        #Only show notifications when available
        if not only_when_available or (only_when_available and self.session.account.status == status.ONLINE):
            if contact is not None and contact.picture is not None and contact.picture != "":
                uri = "file://" + contact.picture
            else:
                uri = 'notification-message-im'

            uri = self.picture_factory(uri, 'message-im')

            if text is not None:
                self.notifier(title if title else '', text, uri, 'message-im', None, tooltip)
        if sound is not None:
            self.sound_player.play(sound)
