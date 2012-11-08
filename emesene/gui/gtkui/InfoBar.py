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
import pango

import logging
log = logging.getLogger('gtkui.InfoBar')

class NiceBar(gtk.InfoBar):
    '''A class used to display messages in a non-intrusive bar'''

    def __init__(self):
        ''' prepare the gtk InfoBar widget'''
        gtk.InfoBar.__init__(self)

        self.message_label = gtk.Label()
        self.message_label.set_line_wrap(True)
        self.message_label.set_ellipsize(pango.ELLIPSIZE_END)
        self.message_image = gtk.Image()
        self.message_hbox = gtk.HBox()
        self.message_hbox.set_border_width(2)
        button = gtk.Button(_("Close"))

        self.empty_queue()

        self.message_hbox.pack_end(button, False, False)
        self.message_hbox.pack_end(self.message_label)

        button.connect('clicked', self.remove_message, gtk.MESSAGE_OTHER)

        content = self.get_content_area()
        content.add(self.message_hbox)

    def new_message(self, message, stock=None):
        ''' Adds the actual message to the queue and show a new one '''

        if self.actual_message != '':
            self.messages_queue.append([self.actual_message, self.actual_image])

        self.display_message(message, stock)

    def remove_message(self, widget, event):
        ''' Removes the actual message and display the next if any '''

        try:
            message, stock = self.messages_queue.pop()
            self.display_message(message, stock)
        except IndexError:
            pass
        self.hide()

    def display_message(self, message, stock=None):
        '''
            Displays a message without modifying the queue
            A background, text color and a stock image are optional
        '''

        self.actual_message = message
        self.actual_image = stock

        if self.message_image.get_parent() is not None:
            self.message_hbox.remove(self.message_image)

        if stock is not None:
            self.message_image = gtk.image_new_from_stock(stock, \
                                             gtk.ICON_SIZE_LARGE_TOOLBAR)
            self.message_hbox.pack_start(self.message_image, False, False)

        self.message_label.set_text(self.actual_message)
        self.show_all()

    def empty_queue(self):
        ''' Delets all messages and hide the bar '''

        self.messages_queue = list()
        self.actual_message = ''
        self.actual_image = None
        self.hide()
