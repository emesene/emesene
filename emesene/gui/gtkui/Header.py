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

import Renderers

class Header(gtk.HBox):
    '''a widget used to display some information about the conversation'''
    INFO_TPL = '%s[$nl]'
    INFO_TPL += '[$small]%s[$/small]'

    NAME = 'Header'
    DESCRIPTION = 'The widget that displays information about the conversation'
    AUTHOR = 'Mariano Guerra, Ivan25'
    WEBSITE = 'www.emesene.org'

    def __init__(self, session, members):
        '''constructor'''
        gtk.HBox.__init__(self)
        self.set_border_width(2)
        self._information = Renderers.SmileyLabel()

        self.eventBox = gtk.EventBox()
        self.eventBox.set_visible_window(False)
        self.eventBox.add(self._information)
        self.eventBox.connect('button-press-event', self.on_clicked)

        self.pack_start(self.eventBox, True, True)

        self.session = session
        self.members = members

        self.menu = gtk.Menu()
        copynick = gtk.ImageMenuItem(_('Copy nick to clipboard'))
        copynick.set_image(gtk.image_new_from_stock(gtk.STOCK_COPY, gtk.ICON_SIZE_MENU))
        copypm = gtk.ImageMenuItem(_('Copy personal message to clipboard'))
        copypm.set_image(gtk.image_new_from_stock(gtk.STOCK_COPY, gtk.ICON_SIZE_MENU))
        copymail = gtk.ImageMenuItem(_('Copy mail to clipboard'))
        copymail.set_image(gtk.image_new_from_stock(gtk.STOCK_COPY, gtk.ICON_SIZE_MENU))
        self.menu.append(copynick)
        self.menu.append(copypm)
        self.menu.append(copymail)
        copynick.connect('activate', self.copy_nick)
        copypm.connect('activate', self.copy_pm)
        copymail.connect('activate', self.copy_mail)
        copynick.show()
        copypm.show()
        copymail.show()

    def _set_information(self, lines):
        '''set the text on the information, lines is a tuple of size 3 with 3
        strings that will be replaced on the template'''
        self._information.set_markup(Renderers.msnplus_to_list(Header.INFO_TPL % lines))
        
    def _get_information(self):
        '''return the text on the information'''
        return self._information.get_markup()

    def copy_nick(self, data, widget=None):
        account = self.members[0]
        contact = self.session.contacts.get(account)

        clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(contact.display_name)

    def copy_pm(self, data, widget=None):
        account = self.members[0]
        contact = self.session.contacts.get(account)

        clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(contact.message)

    def copy_mail(self, data, widget=None):
        account = self.members[0]

        clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(account)

    def on_clicked(self, widget, event):
        '''called when the header clicked'''
        self.menu.popup(None, None, None, event.button, event.time, None)

    information = property(fget=_get_information, fset=_set_information)
