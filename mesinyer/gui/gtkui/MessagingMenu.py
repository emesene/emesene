#adapted for emesene2 by cando from emesene1.x IndicateMessage plugin of Tom Cowell

import os
import gobject
import time
import utils
from e3 import status

import indicate
#TODO don't notify when emesene is on focus
#TODO exit from emesene when we are in login window.
#TODO mark the message as read without clicking in the messagin menu???or when i close the conversation
#without reading the message???
#TODO fix online/online indicator
class MessagingMenu():
    """
    A widget that implements the messaging menu for ubuntu 
    """

    def __init__ (self, handler, main_window=None):
        '''constructor'''
        self.handler = handler
        self.main_window = main_window
        self.conversations = None
        self.signals_have_been_connected = False
        # if system-wide desktop file is not present
        # fallback to a custom .desktop file to be placed in /mesinyer/
        self.desktop_file = os.path.join("/usr/share/applications/", "emesene.desktop")
        if not utils.file_readable(self.desktop_file):
            self.desktop_file = os.path.join(os.getcwd(), "emesene.desktop")
            
        self.indicator_dict = {}

        self.server = indicate.indicate_server_ref_default()
        self.server.set_type("message.emesene")
        self.server.set_desktop_file(self.desktop_file)
        self.sid = self.server.connect("server-display", self._server_display)
        self.server.show()

    def set_login(self):
        """
        dummy,messaging menu doesn't have a login state
        """
        pass

    def set_main(self, session):
        """
        method called to set the state to the main window
        """
        self.handler.session = session
        self.handler.session.signals.contact_attr_changed.subscribe(
            self._on_contact_attr_changed)
        self.handler.session.signals.conv_message.subscribe(
            self._on_message)

        self.signals_have_been_connected = True

    def set_conversations(self, convs):
        """
        Sets the conversations manager
        """
        self.conversations = convs
    
    def set_visible(self, arg):
        """ we are exiting from emesene: disconnect all signals """
        if arg:
            return

        if self.signals_have_been_connected:
            self.handler.session.signals.contact_attr_changed.unsubscribe(
                self._on_contact_attr_changed)
            self.handler.session.signals.conv_message.unsubscribe(
                self._on_message)

        self.server.disconnect(self.sid)
        self.server.hide()
        self.server = None
        self.sid = None

    def _on_contact_attr_changed(self, account, *args):
        """ Called when a contact changed his attrs(we are interesting in online/offline) """

        type,status_ = args
        if type != 'status':
            return

        contact = self.handler.session.contacts.get(account)
        if not contact:
            return
        if contact.status == status.ONLINE:
            self._create_indicator("online", contact.nick, contact.account,
                                    10, ' is online.')
        elif contact.status == status.OFFLINE:
            self._create_indicator("offline", contact.nick, contact.account,
                                   10, ' is offline.')
        else:
            return

    def _on_message(self, cid, account, msgobj, cedict):
        """ 
        This is fired when a new message arrives to a user.
        """
        contact = self.handler.session.contacts.get(account)
        if cid not in self.indicator_dict.values():
            self._create_indicator("im", contact.nick, account, cid=cid)

    def _create_indicator(self, subtype, sender, body, timeout = 0,
                          extraText = '', cid=None):
        """ 
        This creates a new indicator item, called by newMsg, online & offline. 
        """
        if indicate:
            try:
                # Ubuntu 9.10+
                ind = indicate.Indicator()
            except:
                # Ubuntu 9.04
                ind = indicate.IndicatorMessage()
            
            #Get user icon.
            contact = self.handler.session.contacts.get(body)
            pixbuf = utils.safe_gtk_pixbuf_load(contact.picture,(48,48))
            if pixbuf is not None:
                ind.set_property_icon("icon", pixbuf)
        
            ind.set_property("subtype", subtype)
            ind.set_property("sender", sender + extraText)
            if cid is not None:
                ind.set_property("body", str(cid))
            else:
                ind.set_property("body", body)
            ind.set_property_time("time", time.time())
            ind.set_property("draw-attention", "true")
            ind.show()
            handle = ind.connect("user-display", self._display)
            
            # Add indicator to the dictionary
            if subtype == "im":
                self.indicator_dict[ind] = cid

        else:
            return

    def _display(self, indicator, arg=None):
        """ 
        This is fired when a user clicks on the indicator item in the applet.
        """

        # Get the email address and the type of indicator.
        body = indicator.get_property("body")
        subtype = indicator.get_property("subtype")
        if subtype == "im":
            conv = self.conversations.conversations[self.indicator_dict[indicator]]
            conv.get_window().deiconify()
        elif subtype == "online":
            self.conversations.new_conversation(time.time(), body)
        else:
            pass

        if self.indicator_dict[indicator] is not None:
            del self.indicator_dict[indicator]

        # Hide the indicator - user has clicked it so we've no use for it now.
        indicator.hide()
             
    
    def _server_display( self, server, arg1=None ):
        """ 
        This is fired when the user clicks on the server indicator item. 
        """
        self.main_window.present()

