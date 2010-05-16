'''emesene's notification system'''
from e3 import status

import pynotify
if not pynotify.init("emesene"):
    raise ImportError

import logging
log = logging.getLogger('gui.gtkui.Notification')

#TODO add config
#TODO update multiple message on notification
class Notification():
    '''emesene's notification system'''
    NAME = 'Notification'
    DESCRIPTION = 'Emesene\'s notification system'
    AUTHOR = 'Cando'
    WEBSITE = 'www.emesene.org'

    def __init__(self, session):
        """
        Class Constructor
        """
        self.session = session

        if self.session:
            self.session.signals.conv_message.subscribe(
                self._on_message)
            self.session.signals.contact_attr_changed.subscribe(
                self._on_contact_attr_changed)

    def _on_message(self, cid, account, msgobj, cedict):
        """ 
        This is called when a new message arrives to a user.
        """
        #TODO don't notify if the conversation is on focus
        contact = self.session.contacts.get(account)
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
            text = _('is online')
            self._notify(contact, contact.nick , text)
        if contact.status == status.OFFLINE:
            text = _('is offline')
            self._notify(contact, contact.nick , text)


    def _notify(self, contact, title, text):
        """
        This creates and shows the nofification
        """
        if contact.picture is not None:
            uri = "file://" + contact.picture
        else:
            uri = "notification-message-IM"

        n = pynotify.Notification(title, text, uri)

        if not n.show():
            log.exception(_("Failed to send notification"))
        
