# -*- coding: utf-8 -*-

#   This file is part of emesene.
#
#    Emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    emesene is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with emesene; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
import gtk

class NiceBar(gtk.EventBox):
    '''widget that represents the a bar that display errors'''

    def __init__(self):
        
        gtk.EventBox.__init__(self)

        self.label = gtk.Label()
        self.label.set_line_wrap(True)
        self.image = gtk.Image()
        self.image.set_from_stock(gtk.STOCK_DIALOG_ERROR,
                gtk.ICON_SIZE_LARGE_TOOLBAR)

        nicebar_box = gtk.HBox(False)

        nicebar_box.pack_start(self.image, False, False)
        nicebar_box.pack_start(self.label, True, False)

        self.add(nicebar_box)
        self.connect("button-press-event", self._on_nice_bar_clicked)

        self.show_all()

    def show_error(self, message, color=None):
        '''show an error message on the top of the window'''
        if message != None:
            if color is None:
                color = gtk.gdk.Color(57600, 23040, 19712)
            self.modify_bg(gtk.STATE_NORMAL, color)
            self.image.set_from_stock(gtk.STOCK_DIALOG_ERROR,
                                      gtk.ICON_SIZE_LARGE_TOOLBAR)
            self.label.set_text(message)
            self.show_all()
        else:
            self.eventbox.hide_all()

    def show_info(self, message, color=None):
        '''show an info message on the top of the window'''
        if message != None:
            if color is None:
                color = gtk.gdk.color_parse('#CDF00B')
            self.modify_bg(gtk.STATE_NORMAL, color)
            self.image.set_from_stock(gtk.STOCK_DIALOG_INFO,
                                      gtk.ICON_SIZE_LARGE_TOOLBAR)
            self.label.set_text(message)
            self.show_all()
        else:
            self.eventbox.hide_all()

    def _on_nice_bar_clicked(self, widget, event):
        '''hides the bar'''
        self.hide()
