# -*- coding: utf-8 -*-
import gtk
import pango

import logging
log = logging.getLogger('gtkui.NiceBar')

NORMALBACKGROUND = gtk.gdk.Color(65025,65025,46155)
NORMALFOREGROUND = "black"
ALERTBACKGROUND = gtk.gdk.Color(57600,23040,19712)
ALERTFOREGROUND = NORMALFOREGROUND

class NiceBar(gtk.EventBox):
    '''A class used to display messages in a non-intrusive bar'''

    def __init__(self, default_background=ALERTBACKGROUND, default_foreground=None):

        gtk.EventBox.__init__(self)

        self.message_label = gtk.Label()
        self.message_label.set_line_wrap(True)
        self.message_label.set_ellipsize(pango.ELLIPSIZE_END)
        self.message_image = gtk.Image()
        self.message_hbox = gtk.HBox()
        self.message_hbox.set_border_width(2)

        if default_background is None:
            default_background = NORMALBACKGROUND
        if default_foreground is None:
            default_foreground = NORMALFOREGROUND

        self.default_back = default_background
        self.default_fore = default_foreground
        self.empty_queue()
        self.markup = '<span foreground="%s">%s</span>'
        self.modify_bg(gtk.STATE_NORMAL, default_background)

        self.message_hbox.pack_end(self.message_label)
        self.add(self.message_hbox)

        self.connect('button-release-event', self.remove_message)

    def new_message(self, message, stock=None, background=None, \
                                                  foreground=None):
        ''' Adds the actual message to the queue and show a new one '''

        if self.actual_message != '':
            self.messages_queue.append([self.actual_message, \
                    self.actual_image, self.actual_background,
                    self.actual_foreground])

        self.display_message(message, stock, background, foreground)

    def remove_message(self, widget, event):
        ''' Removes the actual message and display the next if any '''

        try:
            message, stock, back, fore = self.messages_queue.pop()
            self.display_message(message, stock, back, fore)
        except IndexError:
            self.hide()

    def display_message(self, message, stock=None, background=None, \
                        foreground=None):
        '''
            Displays a message without modifying the queue
            A background, text color and a stock image are optional
        '''

        self.actual_message = message
        self.actual_image = stock
        self.actual_background = background or self.default_back
        self.actual_foreground = foreground or self.default_fore

        if self.message_image.get_parent() is not None:
            self.message_hbox.remove(self.message_image)

        if stock is not None:
            self.message_image = gtk.image_new_from_stock(stock, \
                                             gtk.ICON_SIZE_LARGE_TOOLBAR)
            self.message_hbox.pack_start(self.message_image, False, False)

        self.modify_bg(gtk.STATE_NORMAL, self.actual_background)
        self.message_label.set_markup(self.markup % (self.actual_foreground,
                                                       self.actual_message))
        self.show_all()

    def empty_queue(self):
        ''' Delets all messages and hide the bar '''

        self.messages_queue = list()
        self.actual_message = ''
        self.actual_image = None
        self.actual_background = self.default_back
        self.actual_foreground = self.default_fore
        self.hide()
