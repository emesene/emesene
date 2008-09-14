import gtk

import gui
import utils

import TextField

class UserPanel(gtk.VBox):
    '''a panel to display and manipulate the user information'''

    def __init__(self, session):
        '''constructor'''
        gtk.VBox.__init__(self)

        self.session = session

        self.image = utils.safe_gtk_image_load(gui.theme.user)
        self.nick = TextField.TextField('', '<Click here to set nick>', False)
        self.message = TextField.TextField('', '<Click here to set message>', 
            True)
        self.toolbar = gtk.HBox()

        hbox = gtk.HBox()
        hbox.pack_start(self.image, False)

        vbox = gtk.VBox()
        vbox.pack_start(self.nick, False)
        vbox.pack_start(self.message, False)

        hbox.pack_start(vbox, True, True)

        self.pack_start(hbox, True, True)
        self.pack_start(self.toolbar, False)
        hbox.show()
        vbox.show()

    def show(self):
        '''override show'''
        gtk.VBox.show(self)
        self.image.show()
        self.nick.show()
        self.message.show()
        self.toolbar.show()

    def show_all(self):
        '''override show_all'''
        self.show()
