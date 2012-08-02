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

class SearchEntry(gtk.Entry):
    def __init__(self, hint_text=_('Type to search...'), clear_text=_('Clear the search')):
        gtk.Entry.__init__(self)
        self.clear_text = clear_text
        if hasattr(gtk.Entry, "set_placeholder_text"):
            self.set_placeholder_text(hint_text)

        self.set_icon_from_stock(0, gtk.STOCK_FIND)
        self.set_icon_tooltip_text(0, hint_text)
        self.connect('changed', self._update_icons_cb)
        self.connect('icon-press', self._on_icon_press)

    def _on_icon_press(self, entry, icon_position, event):
         if icon_position == gtk.ENTRY_ICON_SECONDARY:
             entry.set_text('')

    def _update_icons_cb(self, entry, *args):
        '''only show clear button if we have text'''
        if self.get_text() is None or self.get_text() == '':
            self.set_icon_from_stock(1, None)
        else:
            self.set_icon_from_stock(1, gtk.STOCK_CLEAR)
            self.set_icon_tooltip_text(1, self.clear_text)
