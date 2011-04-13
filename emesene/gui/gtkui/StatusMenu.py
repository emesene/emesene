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

class StatusMenu(gtk.Menu):
    """
    A widget that contains the statuses and allows to change the current status
    """
    NAME = 'Status Menu'
    DESCRIPTION = 'A menu to select the status'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, on_status_selected):
        """
        constructor

        on_status_selected -- a callback that receives the status when changed
        """
        gtk.Menu.__init__(self)
        self.on_status_selected = on_status_selected
        self.status = {}

        for stat in e3.status.ORDERED:
            if stat == e3.status.OFFLINE:
                temp_item = gtk.ImageMenuItem(_("Invisible"))
            else:
                temp_item = gtk.ImageMenuItem(e3.status.STATUS[stat])
            temp_item.set_image(utils.safe_gtk_image_load(
                gui.theme.status_icons[stat]))
            temp_item.connect('activate', self._on_activate, stat)
            self.status[stat] = temp_item
            self.append(temp_item)

    def _on_activate(self, menuitem, stat):
        """
        method called when a status menu item is called
        """

        self.on_status_selected(stat)

