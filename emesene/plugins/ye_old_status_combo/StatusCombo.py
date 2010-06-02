'''module to define the StatusCombo class, used by plugin.py'''
import gtk
import gobject

import e3
import gui
from gui.gtkui import utils

class StatusCombo(gtk.ComboBox):
    """a widget to select the status like the one in emesene 1.0"""
    NAME = 'Status Combo'
    DESCRIPTION = 'A combo to select the status like emesene 1.0'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, main_window):
        """constructor"""
        self.model = gtk.ListStore(gtk.gdk.Pixbuf, \
                      gobject.TYPE_INT, gobject.TYPE_STRING)

        gtk.ComboBox.__init__(self, self.model)
        self.main_window = main_window
        self.status = None

        status_pixbuf_cell = gtk.CellRendererPixbuf()
        status_text_cell = gtk.CellRendererText()
        self.pack_start(status_pixbuf_cell, False)
        self.pack_start(status_text_cell, False)
        status_pixbuf_cell.set_property('xalign', 0.0)
        status_pixbuf_cell.set_property('xpad', 5)
        status_text_cell.set_property('xalign', 0.0)
        status_text_cell.set_property('xpad', 5)
        status_text_cell.set_property('width', 158)
        self.add_attribute(status_pixbuf_cell, 'pixbuf', 0)
        self.add_attribute(status_text_cell, 'text', 2)
        self.set_resize_mode(0)
        self.set_wrap_width(1)

        current_status = main_window.session.account.status

        active = 0
        count = 0

        for stat in e3.status.ORDERED:
            status_name = e3.status.STATUS[stat]

            if stat == current_status:
                active = count

            pixbuf = utils.safe_gtk_pixbuf_load(gui.theme.status_icons[stat])
            pixbuf.scale_simple(20, 20, gtk.gdk.INTERP_BILINEAR)
            self.model.append([pixbuf, stat, status_name]) # re-gettext-it

            count += 1

        self.set_active(active)

        self.connect('scroll-event', self.on_scroll_event)
        self.connect('changed', self.on_status_changed)
        main_window.session.signals.status_change_succeed.subscribe(
                self.on_status_change_succeed)

    def on_status_changed(self , *args):
        """called when a status is selected"""
        stat = self.model.get(self.get_active_iter(), 1)[0]

        if self.status != stat:
            self.status = stat
            self.main_window.session.set_status(stat)

    def on_status_change_succeed(self, stat):
        """called when the status was changed on another place"""
        if stat in e3.status.ORDERED:
            self.status = stat
            index = e3.status.ORDERED.index(stat)
            self.set_active(index)

    def on_scroll_event(self, button, event):
        """called when a scroll is made over the combo"""
        self.popup()
        return True
