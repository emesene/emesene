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
import utils
import gui

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


        self.set_favorite = gtk.ImageMenuItem(_('Set as favorite'))
        self.set_favorite.set_image(utils.gtk_ico_image_load(gui.theme.get_image_theme().favorite,
                                                             gtk.ICON_SIZE_MENU))
        self.set_favorite.connect('activate', 
                              lambda *args: self.on_favorite_group_selected())
        
        
        self.unset_favorite = gtk.ImageMenuItem(_('Unset as favorite'))
        self.unset_favorite.set_image(gtk.image_new_from_stock(gtk.STOCK_CANCEL,
                                                               gtk.ICON_SIZE_MENU))
        self.unset_favorite.connect('activate', 
                              lambda *args: self.on_unset_favorite_group_selected())
        
        if self.handler.contact_list.is_favorite_group_selected():
            self.show_unset_favorite_item()
        else:
            self.show_set_favorite_item()
            
        self.append(self.add)
        self.append(self.remove)
        self.append(self.rename)
        self.append(self.set_favorite)
        self.append(self.unset_favorite)

    def on_favorite_group_selected(self):
        ''' handle favorite group selection '''
        if not self.handler.is_by_group_view(): return
        self.handler.on_favorite_group_selected()
    
    def on_unset_favorite_group_selected(self):
        ''' handle unset group as favorite '''
        if not self.handler.is_by_group_view(): return
        self.handler.on_unset_favorite_group_selected()
    
    def show_set_favorite_item(self):
        '''
        Called when the user right clicks on a non favorite group.
        It hides the unset option and shows the set option.
        '''
        self.unset_favorite.hide()
        self.set_favorite.show()
    
    def show_unset_favorite_item(self):
        '''
        Called when the user right clicks on a favorite group.
        It hides the set option and shows the unset option.
        '''
        self.set_favorite.hide()
        self.unset_favorite.show()

