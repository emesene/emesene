''' gtk tooltips for contact list '''
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
from __future__ import division

import e3
import utils

import gtk
from glib import timeout_add, source_remove
import xml.sax.saxutils

import gui

import Renderers

class Tooltips(gtk.Window):
    ''' Class that implements the tooltips shown in the user list '''
    DELAY = 500
    def __init__(self):
        ''' init the class with some default vals '''
        gtk.Window.__init__(self, gtk.WINDOW_POPUP)

        self.set_name('gtk-tooltips')
        self.set_position(gtk.WIN_POS_MOUSE)
        self.set_resizable(False)
        self.set_border_width(4)
        self.set_app_paintable(True)
        self.connect('expose-event', self.on_expose_event)

        self.label = gtk.Label('')
        self.label.set_line_wrap(True)
        self.label.set_alignment(0, 0.5)
        self.label.set_use_markup(True)
        self.label.show()

        self.image = gtk.Image()
        self.data_string = '<span size="small">(%s)\n\n'
        self.data_string += _('Blocked: ')+ '%s\n'
        #self.data_string += _('Has you: %s')+ '\n'
        self.data_string += '</span>'
        
        self.yes_no = {True : _('Yes'), False : _('No')}
        
        hbox = gtk.HBox(spacing=6)
        vbox = gtk.VBox()
        hbox.pack_start(self.image)
        hbox.pack_start(vbox)
        vbox.pack_start(self.label)
        hbox.show_all()
        self.add(hbox)

        self.connect('delete-event', self.reset)

        self.tag = None
        self.path_array = None

    def hideTooltip(self):
        ''' hides the tooltip and removes any timeout for the tooltip
            to be shown '''
        self.hide()
        self.reset()

    def reset(self):
        ''' removes eventual to-be-shown tooltips '''
        if self.tag and not self.tag == -1:
            source_remove(self.tag)
            self.tag = None
        self.path_array = None

    def on_motion(self, view, event):
        ''' computes if a tooltip must be showed '''
        x, y = int(event.x), int(event.y)
        path_array = view.get_path_at_pos(x, y)
        if not path_array:
            # Mouse out of any user / group element
            self.reset()
            self.hide()
            return

        iterator = view.get_model().get_iter(path_array[0])
        obj = view.get_model().get_value(iterator, 1)
        if not isinstance(obj, e3.Contact):
            self.hide()
            self.reset()
            return

        if self.tag and (path_array[0] == self.path_array):
            # TimeOut on and mouse on same element
            return
        elif self.tag and not (path_array[0] == self.path_array):
            # TO on and mouse has moved to another element
            self.hide()
            self.path_array = path_array[0]
            source_remove(self.tag)
            eventCoords = (event.x_root, event.y_root, y)
            self.tag = timeout_add(Tooltips.DELAY, self.show_tooltip, \
                                            view, eventCoords, \
                                            path_array, obj)
        elif (self.tag == -1)and (path_array[0] == self.path_array):
            # Tooltip visible, no TO, mouse still in the same element
            return
        elif (self.tag == -1)and not (path_array[0] == self.path_array):
            # Tooltip visible, no TO, mouse moves
            self.hide()
            self.path_array = path_array[0]
            eventCoords = (event.x_root, event.y_root, y)
            self.tag = timeout_add(Tooltips.DELAY, self.show_tooltip, \
                                            view, eventCoords, \
                                            path_array, obj)
        else:
            self.path_array = path_array[0]
            eventCoords = (event.x_root, event.y_root, y)
            self.tag = timeout_add(Tooltips.DELAY, self.show_tooltip, \
                                            view, eventCoords, \
                                            path_array, obj)

    def show_tooltip(self, view, origCoords, path_array, obj):
        ''' shows the tooltip of an e3.Contact '''
        self.tag = -1

        text = xml.sax.saxutils.escape(Renderers.msnplus_to_plain_text(obj.nick)) 
        text += '\n' + xml.sax.saxutils.escape(Renderers.msnplus_to_plain_text(obj.message))
        text += '\n' + self.data_string % (\
            obj.account, self.yes_no[bool(obj.blocked)])

        self.label.set_markup(text)

        # Sets tooltip image
        if obj.picture!="":
            pixbuf = utils.gtk_pixbuf_load(obj.picture, (96,96))
        else:
            pixbuf = utils.gtk_pixbuf_load(gui.theme.user_def_image)

        if bool(obj.blocked)==True:
            pixbufblock=utils.gtk_pixbuf_load(gui.theme.blocked_overlay_big)
            utils.simple_images_overlap(pixbuf,pixbufblock,-pixbufblock.props.width,-pixbufblock.props.width)

        self.image.set_from_pixbuf(pixbuf)
        self.image.show()

        # set the location of the tooltip
        x, y = self.computePosition(origCoords, view.window)
        self.move(x, y)
        self.show()
        return False

    def on_leave(self, view, event):
        ''' called when the cursor leaves the area '''
        self.hide()
        self.reset()

    def on_expose_event(self, tooltip_window, event):
        ''' draws a border around the tooltip '''
        width, height = tooltip_window.get_size()
        tooltip_window.style.paint_flat_box(tooltip_window.window, \
                                            gtk.STATE_NORMAL, gtk.SHADOW_OUT, \
                                            None, tooltip_window, 'tooltip', \
                                            0, 0, width, height)

    def computePosition(self, origCoords, viewWindow):
        ''' calculates the position of the tooltip '''
        x_root, y_root, origY = origCoords
        currentY = viewWindow.get_pointer()[1]

        width, height = self.get_size()
        s_width, s_height = gtk.gdk.screen_width(), gtk.gdk.screen_height()

        x = int(x_root) - width // 2
        if currentY >= origY:
            y = int(y_root)+ 24
        else:
            y = int(y_root)+ 6

        # check if over the screen
        if x + width > s_width:
            x = s_width - width
        elif x < 0:
            x = 0

        if y + height > s_height:
            y = y - height - 24
        elif y < 0:
            y = 0
            
        return (x, y)

