'''emesene's notification system'''
from e3 import status
from e3 import Message
import extension

import time
import logging
log = logging.getLogger('gui.gtkui.Notification')

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

        self.notifier = extension.get_default('notificationGUI')

        if self.session:
            self.session.signals.conv_message.subscribe(
                self._on_message)
            self.session.signals.contact_attr_changed.subscribe(
                self._on_contact_attr_changed)

        self.notify_online = False
        self.last_online = None

    def _on_message(self, cid, account, msgobj, cedict={}):
        """
        This is called when a new message arrives to a user.
        """
        #TODO don't notify if the conversation is on focus
        if self.session.config.b_notify_receive_message:
            contact = self.session.contacts.get(account)
            if msgobj.type == Message.TYPE_NUDGE:
                # The message needs to be translated.
                self._notify(contact, contact.nick , _('%s just sent you a nudge!') % (contact.nick,))
            else:
                self._notify(contact, contact.nick , msgobj.body)

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

        if contact.status == status.ONLINE:
            if not self.notify_online:
                # detects the first notification flood and enable the
                # online notifications after it to prevent log in flood
                if self.last_online is not None:
                    t = time.time()
                    self.notify_online = (t - self.last_online > 1)
                    self.last_online = t
                else:
                    self.last_online = time.time()
            else:
                if self.session.config.b_notify_contact_online:
                    text = _('is online')
                    self._notify(contact, contact.nick, text)
        elif contact.status == status.OFFLINE:
            if self.session.config.b_notify_contact_offline:
                text = _('is offline')
                self._notify(contact, contact.nick, text)

    def _notify(self, contact, title, text):
        """
        This creates and shows the nofification
        """
        if contact.picture is not None:
            uri = "file://" + contact.picture
        else:
            uri = "notification-message-IM"

        self.notifier(title, text, uri)

