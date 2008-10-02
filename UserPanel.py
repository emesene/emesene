import gtk

import gui
import utils

import TextField
import StatusButton

class UserPanel(gtk.VBox):
    '''a panel to display and manipulate the user information'''

    def __init__(self, session):
        '''constructor'''
        gtk.VBox.__init__(self)

        self.session = session
        account = self.session.account.account
        self._enabled = True

        self.image = utils.safe_gtk_image_load(gui.theme.user)
        self.nick = TextField.TextField(account, '', False)
        self.status = StatusButton.StatusButton()
        self.message = TextField.TextField('', 
            '<span style="italic">&lt;Click here to set message&gt;</span>', 
            True)
        self.toolbar = gtk.HBox()

        hbox = gtk.HBox()
        hbox.pack_start(self.image, False)

        vbox = gtk.VBox()
        vbox.pack_start(self.nick, False)
        message_hbox = gtk.HBox()
        message_hbox.pack_start(self.message, True, True)
        message_hbox.pack_start(self.status, False)
        vbox.pack_start(message_hbox, False)

        hbox.pack_start(vbox, True, True)

        self.pack_start(hbox, True, True)
        self.pack_start(self.toolbar, False)

        hbox.show()
        message_hbox.show()
        vbox.show()

    def show(self):
        '''override show'''
        gtk.VBox.show(self)
        self.image.show()
        self.nick.show()
        self.message.show()
        self.status.show()
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
        self._enabled = value

    def _get_enabled(self):
        '''return the value of the enabled property
        '''
        return self._enabled

    enabled = property(fget=_get_enabled, fset=_set_enabled)
