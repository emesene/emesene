#adapted for emesene2 by cando from emesene1.x IndicateMessage plugin of Tom Cowell

import os
import gobject
import time
import utils
from e3 import status

try:
    import indicate
except ImportError:
    ERROR = _('Could not import python-indicate: please install via your package manager.')
    print ERROR

#TODO move from gui/base/gtkui!this is not gtk dependent!
#TODO exit from emesene when we are in login window.
class MessagingMenu():
    """
    A widget that implements the messaging menu for ubuntu 
    """

    def __init__ (self, handler, main_window=None):
        '''constructor'''
        self.handler = handler
        self.main_window = main_window
        #cwd = os.getcwd()

        #TODO if this file is not present???
        self.desktop_file = os.path.join("/usr/share/applications/emesene.desktop")
        self.indicatorDict = {}

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
        #connect signals
        self.handler.session.signals.contact_attr_changed.subscribe(
            self._on_contact_attr_changed)
        self.handler.session.signals.conv_message.subscribe(
            self._on_message)
        #TODO
        #self.msgRead = self.controller.connect('message-read', self.messageRead)
    
    def set_visible(self, arg):
        """ we are exiting from emesene: disconnect all signals """
        if arg:
            return
       
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
        self._create_indicator("im", contact.nick, account)

    def _create_indicator(self, subtype, sender, body, timeout = 0, extraText = ''):
        """ 
        This creates a new indicator item, called by newMsg, online & offline. 
        """

        #This creates an indicator object in the indicator-applet.
        handle = None
        ind = None
    
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
            ind.set_property("body", body)
            ind.set_property_time("time", time.time())
            ind.set_property("draw-attention", "true")
            ind.show()
            handle = ind.connect("user-display", self._display)
            
            # Add indicator to the dictionary
            if subtype == "im":
                self.indicatorDict[body] = {handle: ind}
            
            if timeout > 0:
                gobject.timeout_add_seconds(timeout, self.display_timeout, ind)
        else:
            return

        return handle

    def _display(self, indicator, arg=None):
        """ 
        This is fired when a user clicks on the indicator item in the applet.
        """

        # Get the email address and the type of indicator.
        address = indicator.get_property("body")
        subtype = indicator.get_property("subtype")
            
        if subtype == "im" or subtype == "online":
            #TODO
            print "new conv"
             
        # Delete the item (or items?) from the dictionary
        if address in self.indicatorDict:
            del self.indicatorDict[address]
        
        # Hide the indicator - user has clicked it so we've no use for it now.
        indicator.hide()
             
    
    def _server_display( self, server, arg1=None ):
        """ 
        This is fired when the user clicks on the server indicator item. 
        """
        print "main window"
        self.main_window.present()
    

    def display_timeout( self, indicator ):
        ''' Once an indicator has reached it's time limit, this event will fire. '''
        #TODO 
        return
        # Flag to let gobject know if it should continue calling this at x intervals.
        carryOn = False
        
        subtype = indicator.get_property("subtype")
        mail = indicator.get_property("body")

        if mail in self.indicatorDict:
            localDict = self.indicatorDict[mail]
            localKeys = localDict.keys()
            
            # The handle ID for the indicator
            hid = localKeys[0]

            if subtype is "im":
                ''' Indicator is for an instant message.'''
                #Check that the message has been read.
                if self.hasWindowTabFocus(mail):
                    del self.indicatorDict[mail]
                    indicator.hide()
                    carryOn = False
                else:
                    # Message hasn't been read, keep calling this method.
                    carryOn = True

            else:
                ''' online or offline indicator '''
                del self.indicatorDict[mail]
                #indicator.disconnect(hid)
            
                indicator.hide()
                carryOn = False
        
        else:
            ''' The email address is not in the dictionary for some reason.  Stop looping. '''
            carryOn = False
            
        return carryOn

