# -*- coding: utf-8 -*-

#    This file is part of emesene.
#
#    emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
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

class TinyButton(gtk.Button):
    '''a simple and tiny button'''

    def __init__(self, stock):
        '''constructor'''
        gtk.Button.__init__(self)

        # name the button to link it to a style
        self.set_name("close-button")

        image = gtk.image_new_from_stock(stock, gtk.ICON_SIZE_MENU)
        self.set_image(image)

        width, height = gtk.icon_size_lookup(gtk.ICON_SIZE_MENU)
        self.set_size_request(width + 2, height + 2)

        self.set_focus_on_click(False)
        self.set_relief(gtk.RELIEF_NONE)

        gtk.rc_parse_string('''
            style "close-button-style" {
                GtkWidget::focus-padding = 0
                GtkWidget::focus-line-width = 0
                xthickness = 0
                ythickness = 0
            }
            widget "*.close-button" style "close-button-style"
        ''')

if __name__ == '__main__':
    w = gtk.Window()

    # create a new style for the close button
    w.add(TinyButton(gtk.STOCK_CLOSE))
    w.show_all()
    gtk.main()
