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

class GroupMenu(gtk.Menu):
    """
    A class that represents a menu to handle contact related information
    """
    NAME = 'Group Menu'
    DESCRIPTION = 'The menu that displays all the group options'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, handler):
        """
        constructor

        handler -- a e3common.Handler.GroupHandler
        """
        gtk.Menu.__init__(self)
        self.handler = handler

        self.add = gtk.ImageMenuItem(gtk.STOCK_ADD)
        self.add.connect('activate', 
            lambda *args: self.handler.on_add_group_selected())

        self.remove = gtk.ImageMenuItem(gtk.STOCK_REMOVE)
        self.remove.connect('activate', 
            lambda *args: self.handler.on_remove_group_selected())

        self.rename = gtk.ImageMenuItem(_('Rename'))
        self.rename.set_image(gtk.image_new_from_stock(gtk.STOCK_EDIT,
            gtk.ICON_SIZE_MENU))
        self.rename.connect('activate', 
            lambda *args: self.handler.on_rename_group_selected())


        self.append(self.add)
        self.append(self.remove)
        self.append(self.rename)
