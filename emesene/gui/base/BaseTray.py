'''base class for tray icon like implementations'''

class BaseTray(object):
    '''
    a base tray icon class to reuse code
    '''

    def __init__(self, handler=None):
        self.quit_on_close = False
        self.signals_have_been_connected = False
        self.handler = handler

    def set_contacts(self, contacts):
        """
        sets the contacts
        """
        pass

    def set_login(self):
        """
        dummy,messaging menu doesn't have a login state
        """
        pass

    def set_visible(self, arg):
        """ remove subscriptions if not overridden """
        if arg:
            return
        self.disconnect_signals()

    def set_main(self, session):
        """
        method called to set the state to the main window
        """
        self.disconnect_signals()
        self.handler.session = session
        self.handler.session.signals.contact_attr_changed.subscribe(
            self._on_contact_attr_changed)
        self.handler.session.signals.picture_change_succeed.subscribe(
            self._on_contact_attr_changed)
        self.handler.session.signals.status_change_succeed.subscribe(
            self._on_status_change_succeed)
        self.handler.session.signals.conv_message.subscribe(
            self._on_conv_message)
        self.handler.session.signals.conv_ended.subscribe(
            self._on_conv_ended)
        self.handler.session.signals.message_read.subscribe(
            self._on_message_read)

        self.signals_have_been_connected = True

    def disconnect_signals(self):
        """ Disconnect all signals """
        if not self.signals_have_been_connected:
            return

        self.handler.session.signals.contact_attr_changed.unsubscribe(
            self._on_contact_attr_changed)
        self.handler.session.signals.picture_change_succeed.unsubscribe(
            self._on_contact_attr_changed)
        self.handler.session.signals.status_change_succeed.unsubscribe(
            self._on_status_change_succeed)
        self.handler.session.signals.conv_message.unsubscribe(
            self._on_conv_message)
        self.handler.session.signals.conv_ended.unsubscribe(
            self._on_conv_ended)
        self.handler.session.signals.message_read.unsubscribe(
            self._on_message_read)

        self.signals_have_been_connected = False

    def _on_conv_message(self, cid, account, msgobj, cedict=None):
        """
        This is fired when a new message arrives to a user.
        """
        pass

    def _on_message_read(self, conv):
        """
        This is called when the user read the message.
        """
        pass

    def _on_conv_ended(self, cid):
        """
        This is called when the conversation ends
        """
        pass

    def _on_status_change_succeed(self, *args):
        """
        This is called when status is successfully changed
        """
        pass

    def _on_contact_attr_changed(self, *args):
        """
        This is called when a contact changes something
        """
        pass
