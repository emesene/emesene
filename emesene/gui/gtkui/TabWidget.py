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

import os
import gtk
import gobject

import utils
import TinyButton

import Renderers

CLOSE_ON_LEFT = 0

try:
    import gconf
    gclient = gconf.client_get_default()
    val = gclient.get("/apps/metacity/general/button_layout")
    if val.get_string().startswith("close"):
        CLOSE_ON_LEFT = 1
except:
    pass

if os.name == 'mac':
    CLOSE_ON_LEFT = 1

class TabWidget(gtk.HBox):
    '''a widget that is placed on the tab on a notebook'''
    NAME = 'Tab Widget'
    DESCRIPTION = 'A widget to display the tab information'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, text, on_tab_menu, on_close_clicked, conversation, mozilla_like):
        '''constructor'''
        gtk.HBox.__init__(self)
        self.set_border_width(0)
        self.set_spacing(4)

        self.session = conversation.session
        self.mozilla_like = mozilla_like
        self.image = gtk.Image()
        self.label = Renderers.SmileyLabel()
        self.label.set_ellipsize(True)
        self.label.set_text(text)
        self.close = TinyButton.TinyButton(gtk.STOCK_CLOSE)
        self.close.set_tooltip_text(_('Close Tab (Ctrl+W)'))
        self.close.connect('clicked', on_close_clicked,
            conversation)

        if CLOSE_ON_LEFT:
            self.pack_start(self.close, False, False, 0)
            self.pack_start(self.image, False, False, 0)
            self.pack_start(self.label, True, True, 0)
        else:
            self.pack_start(self.image, False, False, 0)
            self.pack_start(self.label, True, True, 0)
            self.pack_start(self.close, False, False, 0)

        if self.session.config.i_tab_position > 1:
            self.set_orientation(gtk.ORIENTATION_VERTICAL)
            self.label.set_angle(90)
        else:
            self.set_orientation(gtk.ORIENTATION_HORIZONTAL)
            self.label.set_angle(0)

        self.session.config.subscribe(self.on_tab_position_change,'i_tab_position')

        self.image.show()
        self.label.show()
        self.close.show()

    def set_image(self, path):
        '''set the image from path'''
        if utils.file_readable(path):
            self.image.set_from_file(path)
            self.image.show()

            return True

        return False

    def set_text(self, text):
        '''set the text of the label'''
        self.label.set_markup(Renderers.msnplus_to_list(gobject.markup_escape_text(text)))
        if self.mozilla_like:
            self.set_size_request(235, 18) # Empiric measures.

    def on_tab_position_change(self, position):
        if self.session.config.i_tab_position > 1:
            self.set_orientation(gtk.ORIENTATION_VERTICAL)
            self.label.set_angle(90)
        else:
            self.set_orientation(gtk.ORIENTATION_HORIZONTAL)
            self.label.set_angle(0)
