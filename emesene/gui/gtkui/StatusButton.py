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

import e3
import gui
import utils
import extension

class StatusButton(gtk.Button):
    '''a button that when clicked displays a popup that allows the user to
    select a status'''
    NAME = 'Status Button'
    DESCRIPTION = 'A button to select the status'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, session=None):
        gtk.Button.__init__(self)
        self.session = session
        # a cache of gtk.Images to not load the images everytime we change
        # our status
        self.cache_imgs = {}

        self.set_relief(gtk.RELIEF_NONE)
        self.set_border_width(0)
        StatusMenu = extension.get_default('menu status')
        self.menu = StatusMenu(self.set_status)

        if self.session:
            current_status = self.session.account.status
            self.status = current_status
        else:
            self.status = e3.status.OFFLINE

        self.set_status(self.status)

        self.menu.show_all()
        self.connect('clicked', self._on_clicked)

    def _on_clicked(self, button):
        '''callback called when the button is clicked'''
        self.menu.popup(None, None, None, 0, 0)

    def set_status(self, stat):
        '''load an image representing a status and store it on cache'''
        current_status = -1
  
        if self.session:
            current_status = self.session.account.status

        if stat not in self.cache_imgs:
            gtk_img = utils.safe_gtk_image_load(\
                gui.theme.image_theme.status_icons[stat])
            self.cache_imgs[stat] = gtk_img
        else:
            gtk_img = self.cache_imgs[stat]

        self.set_image(gtk_img)
        self.show_all()

        if stat not in e3.status.ALL or stat == current_status:
            return

        self.status = stat
        if self.session:
            self.session.set_status(stat)

