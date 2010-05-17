import os
import gtk
import time
import appindicator

import extension
from e3 import status

import logging
log = logging.getLogger('gui.gtkui.Indicator')

HASMESSAGINGMENU = True
try:
    import MessagingMenu
except ImportError:
    HASMESSAGINGMENU = False
    log.exception(_('Could not import python-indicate: please install via your package manager.'))

class Indicator(appindicator.Indicator):
    """
    A widget that implements the tray icon of emesene for gtk
    """

    def __init__(self, handler, main_window=None):
        """
        constructor

        handler -- a e3common.Handler.TrayIconHandler object
        """
        NAME = 'Indicator'
        DESCRIPTION = 'The Ayatana Indicator applet extension'
        AUTHOR = 'Riccardo (C10ud), Stefano(Cando)'
        WEBSITE = 'www.emesene.org'
        appindicator.Indicator.__init__(self, "emesene", "logo", \
            appindicator.CATEGORY_APPLICATION_STATUS, \
            os.path.join(os.getcwd(), handler.theme.theme_path))

        self.handler = handler

        self.main_window = main_window
        self.conversations = None

        self.menu = None
        self.set_login()
        self.set_status(appindicator.STATUS_ACTIVE)

        self.messaging_menu = None
        if HASMESSAGINGMENU:
            self.messaging_menu = MessagingMenu.MessagingMenu(handler, main_window)

    def set_visible(self, arg):
        """ dummy, indicators remove themselves automagically """
        if self.messaging_menu:
            self.messaging_menu.set_visible(arg)

    def set_login(self):
        """
        method called to set the state to the login window
        """
        self.menu = LoginMenu(self.handler)
        self.menu.hide_show_mainwindow.connect('activate', self._on_activate)
        self.menu.show_all()
        self.set_menu(self.menu)

    def set_main(self, session):
        """
        method called to set the state to the main window
        """
        self.handler.session = session
        self.handler.session.signals.status_change_succeed.subscribe(self._on_change_status)
        self.menu = MainMenu(self.handler, self.main_window)
        self.menu.hide_show_mainwindow.connect('activate', self._on_activate)
        self.menu.show_all()
        self.set_menu(self.menu)

        if self.messaging_menu:
            self.messaging_menu.set_main(session)

    def set_conversations(self, convs):
        """
        Sets the conversations manager
        """
        self.conversations = convs

        if self.messaging_menu:
            self.messaging_menu.set_conversations(convs)

    def set_contacts(self, contacts):
        """
        sets the contacts
        """

    def _on_change_status(self,stat):
        """
        change the icon in the tray according to user's state
        """
        #the appindicator takes a 'name' of an icon and NOT a filename. 
        #that means that we have to strip the file extension
        icon_name = self.handler.theme.status_icons[stat].split("/")[-1]
        icon_name = icon_name[:icon_name.rfind(".")]
        self.set_icon(icon_name)        
        
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

    def __init__(self, handler, main_window=None):
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

        self.list = gtk.MenuItem('Contacts')
        self.list_contacts = ContactsMenu(handler, main_window)
        self.list.set_submenu(self.list_contacts)

        self.hide_show_mainwindow = gtk.MenuItem('Hide/Show emesene')

        self.disconnect = gtk.ImageMenuItem(gtk.STOCK_DISCONNECT)
        self.disconnect.connect('activate',
            lambda *args: self.handler.on_disconnect_selected())
        self.quit = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        self.quit.connect('activate',
            lambda *args: self.handler.on_quit_selected())

        self.append(self.hide_show_mainwindow)
        self.append(self.status)
        self.append(self.list)        
        self.append(self.disconnect)
        self.append(gtk.SeparatorMenuItem())
        self.append(self.quit)

class ContactsMenu(gtk.Menu):
    """
    a gtk menu that contains session's contacts
    """
    NAME = 'Contacts Menu'
    DESCRIPTION = 'A menu with sessions\' contacts'
    AUTHOR = 'Riccardo (C10uD)'
    WEBSITE = 'www.emesene.org'
    def __init__(self, handler, main_window=None):
        """
        constructor
        """
        gtk.Menu.__init__(self)
        self.handler = handler
        self.main_window = main_window
        self.item_to_contacts = {}
        self.contacts_to_item = {}

        self.contactmanager = self.handler.session.contacts
        self.handler.session.signals.contact_attr_changed.subscribe(self._on_contact_change_something)

        for contact in self.contactmanager.get_online_list():
            self.__append_contact(contact)

        # TODO: show [pixbuf] [nick] instead of mail

    def __append_contact(self, contact):
        """
        appends a contact to our submenu
        """
        item = gtk.MenuItem(label=contact.nick)
        #item.set_image(contact.picture)
        item.connect('activate', self._on_contact_clicked)    
        self.item_to_contacts[item] = contact
        self.contacts_to_item[contact.account] = item

        self.append(item)

    def _on_contact_change_something(self, *args):
        """
        update the menu when contacts change something
        """
        account, type_change, value_change = args

        if type_change == 'status':
            if value_change > 0:
                if account in self.contacts_to_item:
                    return
                self.__append_contact(self.contactmanager.get(account))
            else: # offline
                if account in self.contacts_to_item:
                    self.remove(self.contacts_to_item[account])
                    del self.item_to_contacts[self.contacts_to_item[account]]
                    del self.contacts_to_item[account]

        if type_change == 'nick':
            if account in self.contacts_to_item:
                self.contacts_to_item[account].set_label(value_change)

    def _on_contact_clicked(self, menu_item):
        """
        called when contacts are clicked
        """
        acc = self.item_to_contacts[menu_item].account
        cid = time.time()
        self.main_window.content.on_new_conversation(cid, [acc], other_started=False)
        self.handler.session.new_conversation(acc, cid)

