import gtk
import time
import os

import extension
from e3 import status

import Renderers

class TrayIcon(gtk.StatusIcon):
    """
    A widget that implements the tray icon of emesene for gtk
    """

    def __init__(self, handler, main_window=None):
        """
        constructor

        handler -- a e3common.Handler.TrayIconHandler object
        """
        NAME = 'Tray Icon'
        DESCRIPTION = 'The gtk tray icon'
        AUTHOR = 'Mariano Guerra'
        WEBSITE = 'www.emesene.org'

        gtk.StatusIcon.__init__(self)
        self.handler = handler

        self.main_window = main_window
        self.conversations = None
        self.last_new_message = None

        self.connect('activate', self._on_activate)
        self.connect('popup-menu', self._on_popup)

        self.set_login()
        self.set_visible(True)

        self.set_tooltip("emesene")

    def set_login(self):
        """
        method called to set the state to the login window
        """
        self.menu = LoginMenu(self.handler, self.main_window)
        self.menu.show_all()
        self.set_from_file(self.handler.theme.logo)

    def set_main(self, session):
        """
        method called to set the state to the main window
        """
        self.handler.session = session
        self.handler.session.signals.status_change_succeed.subscribe(
                                                      self._on_change_status)
        self.handler.session.signals.conv_message.subscribe(self._on_message)
        self.handler.session.signals.message_read.subscribe(self._on_read)
        self.menu = MainMenu(self.handler, self.main_window)
        self.menu.show_all()
        self.set_tooltip("emesene - " + self.handler.session.account.account)

    def set_conversations(self, convs):
        """
        Sets the conversations manager
        """
        self.conversations = convs

    def set_contacts(self, contacts):
        """
        sets the contacts
        """

    def _on_message(self, cid, account, msgobj, cedict={}):
        """
        Blink tray icon and save newest unread message
        """
        if not self.conversations.get_parent().is_active():
            self.set_blinking(True)
            self.last_new_message = cid

    def _on_read(self, page):
        """
        Stop tray blinking and resets the newest unread message reference
        """
        self.set_blinking(False)
        self.last_new_message = None

    def _on_activate(self, trayicon):
        """
        callback called when the status icon is activated
        (includes clicking the icon)
        """
        
        if self.last_new_message is not None and self.is_blinking():
            # show the tab with the latest message
            conversation = self.conversations.conversations[self.last_new_message]
            page = self.conversations.page_num(conversation)
            self.conversations.set_current_page(page)
            self.conversations.get_parent().present()
        else:
            self.handler.on_hide_show_mainwindow(self.main_window)

    def _on_change_status(self,stat):
        """
        change the icon in the tray according to user's state
        """
        if stat not in status.ALL or stat == -1:
            return
        self.set_from_file(self.handler.theme.status_icons_panel[stat])

    def _on_popup(self, trayicon, button, activate_time):
        """
        callback called when the popup of the status icon is activated
        (usually through right-clicking the status icon)
        """
        position = None
        if os.name == 'posix':
            position = gtk.status_icon_position_menu
        self.menu.popup(None, None, position, button, activate_time, trayicon)

class LoginMenu(gtk.Menu):
    """
    a widget that represents the menu displayed on the trayicon on the
    login window
    """

    def __init__(self, handler, main_window=None):
        """
        constructor

        handler -- a e3common.Handler.TrayIconHandler object
        """
        gtk.Menu.__init__(self)
        self.handler = handler
        self.hide_show_mainwindow = gtk.MenuItem(_('Hide/Show emesene'))
        self.hide_show_mainwindow.connect('activate',
            lambda *args: self.handler.on_hide_show_mainwindow(main_window))
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
        self.status = gtk.ImageMenuItem(_('Status'))
        self.status.set_image(gtk.image_new_from_stock(gtk.STOCK_CONVERT,
            gtk.ICON_SIZE_MENU))
        self.status_menu = StatusMenu(handler.on_status_selected)
        self.status.set_submenu(self.status_menu)

        self.list = gtk.MenuItem(_('Contacts'))
        self.list_contacts = ContactsMenu(handler, main_window)
        self.list.set_submenu(self.list_contacts)

        self.hide_show_mainwindow = gtk.MenuItem(_('Hide/Show emesene'))
        self.hide_show_mainwindow.connect('activate',
            lambda *args: self.handler.on_hide_show_mainwindow(main_window))

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
    DESCRIPTION = _('A menu with sessions\' contacts')
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
        self.avatar_size = 32

        self.contactmanager = self.handler.session.contacts
        
        for contact in self.contactmanager.get_online_list():
            self.__append_contact(contact)

        self.handler.session.signals.contact_attr_changed.subscribe(self._on_contact_change_something)

        # TODO: find out why gtk ImageMenuItem does not work as expected

    def __append_contact(self, contact):
        """
        appends a contact to our submenu
        """
        #item = gtk.ImageMenuItem()
        item = gtk.MenuItem()
        item.set_label(Renderers.msnplus_to_plain_text(contact.nick))
        #pict = self.__get_contact_pixbuf_or_default(contact)
        #item.set_image(pict)
        item.connect('activate', self._on_contact_clicked)    
        self.item_to_contacts[item] = contact
        self.contacts_to_item[contact.account] = item

        item.show()
        self.add(item)
                
    def _on_contact_change_something(self, *args):
        """
        update the menu when contacts change something
        """
        if len(args) == 3:
            account, type_change, value_change = args
        elif len(args) == 4:
            account, type_change, value_change, do_notify = args
        
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
                nick = self.item_to_contacts[self.contacts_to_item[account]].nick
                self.contacts_to_item[account].set_label(nick)

        if type_change == 'picture':
        #TODO: fixme
            return
            if account in self.contacts_to_item:
                contact = self.item_to_contacts[self.contacts_to_item[account]]
                pict = self.__get_contact_pixbuf_or_default(contact)
                self.contacts_to_item[account].set_image(pict)

    def _on_contact_clicked(self, menu_item):
        """
        called when contacts are clicked
        """
        acc = self.item_to_contacts[menu_item].account
        cid = time.time()
        self.main_window.content.on_new_conversation(cid, [acc], other_started=False)
        self.handler.session.new_conversation(acc, cid)

    def __get_contact_pixbuf_or_default(self, contact):
        '''try to return a pixbuf of the user picture or the default
        picture
        '''
        if contact.picture:
            try:
                animation = gtk.gdk.PixbufAnimation(contact.picture)
            except gobject.GError:
                pix = utils.safe_gtk_pixbuf_load(gui.theme.user,
                        (self.avatar_size, self.avatar_size))
                picture = gtk.image_new_from_pixbuf(pix)
                return picture

            if animation.is_static_image():
                pix = utils.safe_gtk_pixbuf_load(contact.picture,
                        (self.avatar_size, self.avatar_size))
                picture = gtk.image_new_from_pixbuf(pix)
            else:
                picture = gtk.image_new_from_animation(animation)

        else:
            pix = utils.safe_gtk_pixbuf_load(gui.theme.user,
                        (self.avatar_size, self.avatar_size))
            picture = gtk.image_new_from_pixbuf(pix)

        return picture

