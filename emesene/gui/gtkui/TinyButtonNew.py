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

from gi.repository import Gtk

class TinyButton(Gtk.Button):
    '''a simple and tiny button'''

    def __init__(self, stock):
        '''constructor'''
        Gtk.Button.__init__(self)

        # name the button to link it to a style
        self.set_name("close-button")

        image = Gtk.Image.new_from_stock(stock, Gtk.IconSize.MENU)
        self.set_image(image)

        self.set_focus_on_click(False)
        self.set_relief(Gtk.ReliefStyle.NONE)

        prov = Gtk.CssProvider()
        prov.load_from_data("* {\n"
		  "-GtkButton-default-border : 0;\n"
		  "-GtkButton-default-outside-border : 0;\n"
		  "-GtkButton-inner-border: 0;\n"
		  "-GtkWidget-focus-line-width : 0;\n"
		  "-GtkWidget-focus-padding : 0;\n"
		  "padding: 0;\n"
		"}");
        ctx = self.get_style_context()
        ctx.add_provider(prov, 600) #GTK_STYLE_PROVIDER_PRIORITY_APPLICATION
