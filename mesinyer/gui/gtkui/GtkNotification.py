import gtk
import pango

import logging
log = logging.getLogger('gui.gtkui.GtkNotification')

NAME = 'GtkNotification'
DESCRIPTION = 'Emesene\'s notification system\'s gtk ui'
AUTHOR = 'arielj'
WEBSITE = 'www.emesene.org'

def gtkNotification(title, text, picturePath=None):
    noti = Notification(title, text, picturePath)
    noti.show()

class Notification(gtk.Window):
    def __init__(self, title, text, picturePath):

        gtk.Window.__init__(self)

        self.set_accept_focus(False)
        self.set_decorated(False)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_SPLASHSCREEN)

        self.callback = None

        self.set_geometry_hints(None, min_width=200, min_height=150, \
                max_width=200, max_height=150)

        messageLabel = gtk.Label(text)
        messageLabel.set_use_markup(True)
        messageLabel.set_justify(gtk.JUSTIFY_CENTER)
        messageLabel.set_ellipsize(pango.ELLIPSIZE_END)

        hbox = gtk.HBox()
        vbox = gtk.VBox()
        lbox = gtk.HBox()
        titleLabel = gtk.Label(title)
        titleLabel.set_use_markup(True)
        titleLabel.set_justify(gtk.JUSTIFY_CENTER)
        titleLabel.set_ellipsize(pango.ELLIPSIZE_END)

        avatarImage = gtk.Image()
        if picturePath != None and picturePath != "file://":
            userPixbuf = gtk.gdk.pixbuf_new_from_file_at_size(picturePath,48, 48)
            avatarImage.set_from_pixbuf(userPixbuf)

        lboxEventBox = gtk.EventBox()
        lboxEventBox.set_visible_window(False)
        lboxEventBox.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        lboxEventBox.connect("button_press_event", self.onClick)
        lboxEventBox.add(lbox)
        
        self.connect("button_press_event", self.onClick)

        hbox.pack_start(titleLabel, True, True)
        lbox.pack_start(avatarImage, False, False, 10)
        lbox.pack_start(messageLabel, True, True, 5)

        vbox.pack_start(hbox, False, False)
        vbox.pack_start(lboxEventBox, True, True)

        self.add(vbox)
        
        self.set_gravity(gtk.gdk.GRAVITY_SOUTH_EAST)
        width, height = self.get_size()
        self.move(gtk.gdk.screen_width() - width, gtk.gdk.screen_height() - height)

        vbox.show_all()

    def onClick(self, widget, event):
        self.close()

    def show(self):
        ''' show it '''
        self.show_all()
        return True

    def close(self , *args):
        ''' hide the Notification '''
        self.hide()
