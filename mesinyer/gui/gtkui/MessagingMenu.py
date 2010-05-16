import os
import time
import utils
import indicate

class MessagingMenu():
    """
    A widget that implements the messaging menu for ubuntu 
    """

    def __init__ (self, handler, main_window=None):
        '''constructor'''
        NAME = 'Messaging Menu'
        DESCRIPTION = 'The Ayatana Messaging Menu extension'
        AUTHOR = 'Cando, Tom Cowell'
        WEBSITE = 'www.emesene.org'
        self.handler = handler
        self.main_window = main_window
        self.conversations = None
        self.signals_have_been_connected = False
        # if system-wide desktop file is not present
        # fallback to a custom .desktop file to be placed in /mesinyer/
        self.desktop_file = os.path.join("/usr/share/applications/",
                                         "emesene.desktop")
        if not utils.file_readable(self.desktop_file):
            self.desktop_file = os.path.join(os.getcwd(), "emesene.desktop")
            
        self.indicator_dict = {}
        self.r_indicator_dict = {}

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
        self.handler.session.signals.conv_message.subscribe(
            self._on_message)
        self.handler.session.signals.conv_ended.subscribe(
            self._on_conv_ended)
        self.handler.session.signals.message_read.subscribe(
            self._on_message_read)

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
            self.handler.session.signals.conv_message.unsubscribe(
                self._on_message)
            self.handler.session.signals.conv_ended.unsubscribe(
                self._on_conv_ended)
            self.handler.session.signals.message_read.unsubscribe(
                self._on_message_read)

        self.server.disconnect(self.sid)
        self.server.hide()
        self.server = None
        self.sid = None

    def _on_message(self, cid, account, msgobj, cedict):
        """ 
        This is fired when a new message arrives to a user.
        """
        contact = self.handler.session.contacts.get(account)
        if cid not in self.indicator_dict.values():
            current_page = self.conversations.get_current_page()
            conv = self.conversations.get_nth_page(current_page)
            if (not self.conversations.get_parent().is_active()) or \
                conv.members != [account,]:
                self._create_indicator("im", contact.nick, account, cid=cid)

    def _on_message_read(self, page_num):
        """ 
        This is called when the user read the message.
        """
        conv = self.conversations.get_nth_page(page_num)
        if conv.cid in self.r_indicator_dict.keys():
            ind = self.r_indicator_dict[conv.cid]
            if ind is not None:
                ind.hide()
                if self.indicator_dict[ind] is not None:
                    del self.indicator_dict[ind]
                if self.r_indicator_dict[conv.cid] is not None:
                    del self.r_indicator_dict[conv.cid]

    def _on_conv_ended(self, cid):
        """
        Called when the user close the conversation.
        """
        if cid in self.r_indicator_dict.keys():
            ind = self.r_indicator_dict[cid]
            ind.hide()
            del self.r_indicator_dict[cid]

    def _create_indicator(self, subtype, sender, body,
                          extra_text = '', cid=None):
        """ 
        This creates a new indicator item, called by on_message, online & offline. 
        """
        if indicate:
            try:
                # Ubuntu 9.10+
                ind = indicate.Indicator()
            except Exception:
                # Ubuntu 9.04
                ind = indicate.IndicatorMessage()
            
            #Get user icon.
            contact = self.handler.session.contacts.get(body)
            pixbuf = utils.safe_gtk_pixbuf_load(contact.picture, (48, 48))
            if pixbuf is not None:
                ind.set_property_icon("icon", pixbuf)
        
            ind.set_property("subtype", subtype)
            ind.set_property("sender", sender + extra_text)
            if cid is not None:
                ind.set_property("body", str(cid))
            else:
                ind.set_property("body", body)
            ind.set_property_time("time", time.time())
            ind.set_property("draw-attention", "true")
            ind.connect("user-display", self._display)
            ind.show()
            
            # Add indicator to the dictionary
            if subtype == "im":
                self.indicator_dict[ind] = cid
                self.r_indicator_dict[cid] = ind

        else:
            return

    def _display(self, indicator, arg=None):
        """ 
        This is fired when a user clicks on the indicator item in the applet.
        """
        subtype = indicator.get_property("subtype")
        if subtype == "im":
            cid = self.indicator_dict[indicator]
            conv = self.conversations.conversations[cid]
            self.conversations.set_current_page(conv.tab_index)
            self.conversations.get_parent().present()

        if self.indicator_dict[indicator] is not None:
            del self.indicator_dict[indicator]
        if self.r_indicator_dict[conv.cid] is not None:
            del self.r_indicator_dict[conv.cid]

        # Hide the indicator - user has clicked it so we've no use for it now.
        indicator.hide()
             
    
    def _server_display(self, server, arg=None):
        """ 
        This is fired when the user clicks on the server indicator item. 
        """
        self.main_window.present()

