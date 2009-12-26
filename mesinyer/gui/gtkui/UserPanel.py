import gtk

import gui
import utils

import TextField
import StatusButton

class UserPanel(gtk.VBox):
    '''a panel to display and manipulate the user information'''
    NAME = 'User Panel'
    DESCRIPTION = 'A widget to display/modify the account information on the main window'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, session):
        '''constructor'''
        gtk.VBox.__init__(self)

        self.session = session
        account = self.session.account.account
        self._enabled = True

        self.image = utils.safe_gtk_image_load(gui.theme.user)
        self.nick = TextField.TextField(account, '', False)
        self.status = StatusButton.StatusButton(session)
        self.search = gtk.ToggleButton()
        self.search.set_image(gtk.image_new_from_stock(gtk.STOCK_FIND,
            gtk.ICON_SIZE_MENU))
        self.search.set_relief(gtk.RELIEF_NONE)

        self.message = TextField.TextField('',
            '<span style="italic">&lt;Click here to set message&gt;</span>',
            True)
        self.toolbar = gtk.HBox()

        hbox = gtk.HBox()
        hbox.pack_start(self.image, False)

        vbox = gtk.VBox()
        nick_hbox = gtk.HBox()
        nick_hbox.pack_start(self.nick, True, True)
        nick_hbox.pack_start(self.search, False)
        vbox.pack_start(nick_hbox, False)
        message_hbox = gtk.HBox()
        message_hbox.pack_start(self.message, True, True)
        message_hbox.pack_start(self.status, False)
        vbox.pack_start(message_hbox, False)

        hbox.pack_start(vbox, True, True)

        self.pack_start(hbox, True, True)
        self.pack_start(self.toolbar, False)

        hbox.show()
        nick_hbox.show()
        message_hbox.show()
        vbox.show()

        session.signals.message_change_succeed.subscribe(
            self.on_message_change_succeed)
        session.signals.status_change_succeed.subscribe(
            self.on_status_change_succeed)
        session.signals.contact_list_ready.subscribe(
            self.on_contact_list_ready)
        session.signals.picture_change_succeed.subscribe(
            self.on_picture_change_succeed)
        session.signals.profile_get_succeed.subscribe(
                self.on_profile_get_succeed)

    def show(self):
        '''override show'''
        gtk.VBox.show(self)
        self.image.show()
        self.nick.show()
        self.message.show()
        self.status.show()
        self.search.show()
        self.toolbar.show()

    def show_all(self):
        '''override show_all'''
        self.show()

    def _set_enabled(self, value):
        '''set the value of enabled and modify the widgets to reflect the status
        '''
        self.nick.enabled = value
        self.message.enabled = value
        self.status.set_sensitive(value)
        self.search.set_sensitive(value)
        self._enabled = value

    def _get_enabled(self):
        '''return the value of the enabled property
        '''
        return self._enabled

    enabled = property(fget=_get_enabled, fset=_set_enabled)

    def on_status_change_succeed(self, stat):
        '''callback called when the status has been changed successfully'''
        self.status.set_status(stat)

    def on_message_change_succeed(self, message):
        '''callback called when the message has been changed successfully'''
        self.message.text = message

    def on_contact_list_ready(self):
        '''callback called when the contact list is ready to be used'''
        self.enabled = True

    def on_picture_change_succeed(self, account, path):
        '''callback called when the picture of an account is changed'''
        # out account
        if account == self.session.account.account:
            pixbuf = utils.safe_gtk_pixbuf_load(path, (32, 32))
            self.image.set_from_pixbuf(pixbuf)

    def on_profile_get_succeed(self, cid, nick, message):
        '''method called when information about our profile is obtained
        '''
        self.nick.text = nick
        self.message.text = message

