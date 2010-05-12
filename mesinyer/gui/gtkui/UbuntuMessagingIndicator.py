import os
import gtk
import time
try:
    import appindicator
except ImportError:
    appindicator = None
    log.exception(_('Could not import python-appindicator: please install via your package manager.'))
try:
    import indicate
except ImportError:
    indicate = None
    log.exception(_('Could not import python-indicate: please install via your package manager.'))

#this exception is thrown for choosing the right trayicon extension
#in the _init_.py file in gtkui
if appindicator is None and indicate is None:
    raise ImportError

import utils
import extension
from e3 import status

class UbuntuMessagingIndicator():
    """
    A widget that implements the tray icon and the ubuntu's messaging menu
    of emesene for gtk
    """

    def __init__(self, handler, main_window=None):
        """
        constructor

        handler -- a e3common.Handler.TrayIconHandler object
        """
        self.handler = handler
        self.main_window = main_window
        self.conversations = None

        if appindicator:
            self.trayicon = appindicator.Indicator("emesene", "logo", \
                appindicator.CATEGORY_APPLICATION_STATUS, \
                os.path.join(os.getcwd(), handler.theme.theme_path))
            self.set_login()
            self.trayicon.set_status(appindicator.STATUS_ACTIVE)

        if indicate:
            self.desktop_file = os.path.join("/usr/share/applications/emesene.desktop")
            self.indicator_dict = {}
            self.server = indicate.indicate_server_ref_default()
            self.server.set_type("message.emesene")
            self.server.set_desktop_file(self.desktop_file)
            self.sid = self.server.connect("server-display", self._server_display)
            self.server.show()

    def set_visible(self, arg):
        """ dummy for indicators remove themselves automagically;
            while we must hide messaging menu
        """
        if indicate:
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

    def set_login(self):
        """
        method called to set the state to the login window;
        dummy for messaging menu
        """
        if appindicator:
            self.menu = LoginMenu(self.handler)
            self.menu.hide_show_mainwindow.connect('activate', self._on_activate)
            self.menu.show_all()
            self.trayicon.set_menu(self.menu)

    def set_main(self, session):
        """
        method called to set the state to the main window
        """
        self.handler.session = session
        if appindicator:
            self.handler.session.signals.status_change_succeed.subscribe(self._on_change_status)
            self.menu = MainMenu(self.handler)
            self.menu.hide_show_mainwindow.connect('activate', self._on_activate)
            self.menu.show_all()
            self.trayicon.set_menu(self.menu)
        if indicate:
            self.handler.session.signals.contact_attr_changed.subscribe(
                self._on_contact_attr_changed)
            self.handler.session.signals.conv_message.subscribe(
                self._on_message)

    def set_conversations(self, convs):
        """
        Sets the conversations manager
        """
        self.conversations = convs

    def _on_change_status(self,stat):
        """
        change the icon in the tray according to user's state
        """
        #the appindicator takes a 'name' of an icon and NOT a filename. 
        #that means that we have to strip the file extension
        icon_name = self.handler.theme.status_icons[stat].split("/")[-1]
        icon_name = icon_name[:icon_name.rfind(".")]
        self.trayicon.set_icon(icon_name)        
        
    def _on_activate(self, trayicon):
	"""
        callback called when the menu entry 'hide/show emesene'
        is clicked
        """
        if(self.main_window != None):
            if(self.main_window.get_property("visible")):
                self.main_window.hide()
            else:
                self.main_window.show()

    #
    #Messaging Menu stuffs
    #

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

class LoginMenu(gtk.Menu):
    """
    a widget that represents the menu displayed on the trayicon on the
    login window
    """

    def __init__(self, handler):
        """
        constructor

        handler -- a e3common.Handler.TrayIconHandler object
        """
        gtk.Menu.__init__(self)
        self.handler = handler
        self.hide_show_mainwindow = gtk.MenuItem('Hide/Show emesene')
        self.quit = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        self.quit.connect('activate',
            lambda *args: self.handler.on_quit_selected())
            
        self.append(self.hide_show_mainwindow)
        self.append(self.quit)

class MainMenu(gtk.Menu):
    """
    a widget that represents the menu displayed on the trayicon on the
    main window
    """

    def __init__(self, handler):
        """
        constructor

        handler -- a e3common.Handler.TrayIconHandler object
        """
        gtk.Menu.__init__(self)
        self.handler = handler

        StatusMenu = extension.get_default('menu status')
        self.status = gtk.ImageMenuItem('Status')
        self.status.set_image(gtk.image_new_from_stock(gtk.STOCK_CONVERT,
            gtk.ICON_SIZE_MENU))
        self.status_menu = StatusMenu(handler.on_status_selected)
        self.status.set_submenu(self.status_menu)
        
        self.hide_show_mainwindow = gtk.MenuItem('Hide/Show emesene')

        self.disconnect = gtk.ImageMenuItem(gtk.STOCK_DISCONNECT)
        self.disconnect.connect('activate',
            lambda *args: self.handler.on_disconnect_selected())
        self.quit = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        self.quit.connect('activate',
            lambda *args: self.handler.on_quit_selected())

        self.append(self.status)
        self.append(self.hide_show_mainwindow)
        self.append(self.disconnect)
        self.append(gtk.SeparatorMenuItem())
        self.append(self.quit)
