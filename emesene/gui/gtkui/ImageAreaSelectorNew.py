'''a module that permit to resize an image added as avatar'''
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

from gi.repository import Gtk, GObject, Gdk, GdkPixbuf
import cairo
from gi.repository import Pango
from sys import platform

if platform == 'darwin':
    MAC = True
else:
    MAC = False

import logging
log = logging.getLogger('gtkui.ImageAreaSelector')

WIDTH=64
HEIGHT=64

class ImageAreaSelectorDialog(Gtk.Dialog):

    NAME = 'ImageAreaSelector'
    DESCRIPTION = _('The widget that permits to resize an image added as avatar')
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, callback, pixbuf, title = _("Select area of image"),
                 parent = None):
        Gtk.Dialog.__init__(self, title, parent,
                            Gtk.DialogFlags.DESTROY_WITH_PARENT)
 
        self.callback = callback
        self.set_default_response(Gtk.ResponseType.CANCEL)
        self.set_resizable(False)
        self.button_accept = Gtk.Button(stock=Gtk.STOCK_OK)
        self.button_accept.connect('clicked', lambda *args: self.response(Gtk.ResponseType.OK))
        self.button_accept.set_sensitive(False)
        self.button_cancel = Gtk.Button(stock=Gtk.STOCK_CANCEL)
        self.button_cancel.connect('clicked', lambda *args: self.response(Gtk.ResponseType.CANCEL))

        self.selector = ImageAreaSelector(self.button_accept)
        self.set_size_request(200, 200)
        self.selector.set_from_pixbuf(pixbuf)

        if not MAC:
            self.button_rcw = Gtk.Button(_("Rotate"))
            self.button_rcw.connect("clicked", self._on_rcw_clicked)
            self.button_rccw = Gtk.Button(_("Rotate"))
            self.button_rccw.connect("clicked", self._on_rccw_clicked)

            self.action_area.pack_start(self.button_rccw, True, True, 0)
            self.action_area.pack_end(self.button_rcw, False, False, 0)

        self.action_area.pack_end(self.button_cancel, False, False, 0)
        self.action_area.pack_end(self.button_accept, False, False, 0)

        ##Draw the statusBar
        label = Gtk.Label(label=_('Draw a square to select an area'))
        label.set_ellipsize(Pango.EllipsizeMode.END)
        image = Gtk.Image()
        image.set_from_stock (Gtk.STOCK_DIALOG_INFO, Gtk.IconSize.LARGE_TOOLBAR)
        info = Gtk.InfoBar.new()
        info.set_message_type(Gtk.MessageType.INFO)
        info.set_size_request(0, 30)
        content = info.get_content_area ()
        content.add(image)
        content.add(label)

        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.vbox.pack_start(self.selector, True, True, 0)
        self.vbox.pack_end(info, False, False, 0)
        self.vbox.show_all()

    def run(self):
        response = Gtk.Dialog.run(self)
        if response == Gtk.ResponseType.OK:
            pixbuf = self.selector.get_selected()
            self.callback(Gtk.ResponseType.OK, pixbuf)
            self.destroy()
        else:
            self.destroy()
            return self.callback(Gtk.ResponseType.CANCEL, None)

    def _on_rcw_clicked(self, *args):
        self.selector.rotate(1)
    def _on_rccw_clicked(self, *args):
        self.selector.rotate(-1)

class ImageAreaSelector(Gtk.DrawingArea):
    __gtype_name__ = "ImageAreaSelector"
    def __init__(self, button_accept):
        Gtk.DrawingArea.__init__(self)
        self.connect("draw", self.draw)
        self.image = None
        self.pixbuf = None
        self.button_accept = button_accept #handle sensitivity of accept button
        self.connect("button_press_event", self.button_press)
        self.connect("button_release_event", self.button_release)
        self.connect("motion_notify_event", self.motion_notify)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK |
                        Gdk.EventMask.BUTTON_RELEASE_MASK |
                        Gdk.EventMask.POINTER_MOTION_MASK)

        self._pressed = False
        self._moved = False
        self._state = Gdk.CursorType.LEFT_PTR
        self._angle = 0
        self.dx = 0
        self.dy = 0

    def get_selected(self):
        angle = self.get_angle()
        self._trans_pixbuf = self._trans_pixbuf.rotate_simple(angle)
        # handle no selection
        if self.selection == (0,0,0,0):
            #this should never happens
            return
       
        return self._trans_pixbuf.new_subpixbuf(*self.selection)

    def _get_selection(self):
        return (self._x, self._y, self._width, self._height)
        
    def _set_selection(self, (x, y, width, height)):
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        self.redraw_canvas()
    selection = property(_get_selection, _set_selection)

    def _get_sel_coord(self):
        x1 = self._x
        y1 = self._y
        x2 = x1 + self._width
        y2 = y1 + self._height
        if x1 != x2: #means there is a selection
            self.button_accept.set_sensitive(True)
        else:
            self.button_accept.set_sensitive(False)
        return (x1, y1, x2, y2)

    def _set_sel_coord(self, x1, y1, x2, y2):
        if x1 < 0 or (x1 > 0 and x1 < self.dx) or y1 < 0 \
               or (y1 > 0 and y1 < self.dy) or x2 > self.pixbuf.get_width() - self.dx \
               or y2 > self.pixbuf.get_height() - self.dy:
            return
        if x1 > x2:
            x2 = x1
        if y1 > y2:
            y2 = y1

        self.selection = map(int, (x1, y1, x2-x1, y2-y1))

    def reset_selection(self):
        self.selection = (0,0,0,0)
        self.button_accept.set_sensitive(False)

    def button_release(self, *args):
        self._pressed = False
        if not self._moved and self._state == Gdk.CursorType.LEFT_PTR:
            self.reset_selection()

    def rotate(self, angle):
        self._angle = (self._angle + angle) % 4
        angle = self.get_angle()

        #rotate margins
        tmp = self.dx
        self.dx = self.dy
        self.dy = tmp

        self._init_pixbuf(angle, False)

    def get_angle(self):

        if self._angle == 1:
            angle = GdkPixbuf.PixbufRotation.CLOCKWISE
        elif self._angle == 2:
            angle = GdkPixbuf.PixbufRotation.UPSIDEDOWN
        elif self._angle == 3:
            angle = GdkPixbuf.PixbufRotation.COUNTERCLOCKWISE
        else:
            angle = GdkPixbuf.PixbufRotation.NONE
        return angle

    def update_selection(self, event):
        # track mouse delta
        dx = event.x - self._mouse_x
        dy = event.y - self._mouse_y

        x1, y1, x2, y2 = self._get_sel_coord()
        if self._state == Gdk.CursorType.TOP_LEFT_CORNER:
            w = x2 - event.x
            h = y2 - event.y
            delta = max((w, h))
            x1 = x2 - delta
            y1 = y2 - delta
        elif self._state == Gdk.CursorType.TOP_RIGHT_CORNER:
            w = event.x - x1
            h = y2 - event.y
            delta = max((w, h))
            x2 = x1 + delta
            y1 = y2 - delta
        elif self._state == Gdk.CursorType.BOTTOM_RIGHT_CORNER:
            w = (event.x-x1)
            h = (event.y-y1)
            delta = max((w, h))
            x2 = x1 + delta
            y2 = y1 + delta
        elif self._state == Gdk.CursorType.BOTTOM_LEFT_CORNER:
            w = x2 - event.x
            h = (event.y-y1)
            delta = max((w, h))
            x1 = x2 - delta
            y2 = y1 + delta
        elif self._state == Gdk.CursorType.FLEUR:
            x1 += dx
            y1 += dy
            x2 += dx
            y2 += dy
        else:
            # mouse pressed outside current selection. Create new selection
            x1 = self._press_x
            y1 = self._press_y
            w = event.x - x1
            h = event.y - y1
            delta = max((w, h))
            x2 = x1 + delta
            y2 = y1 + delta

        self._mouse_x = event.x
        self._mouse_y = event.y
        self._set_sel_coord(x1, y1, x2, y2)

    def update_cursor(self, event):
        fuzz = max((5, int(self._width * 0.05)))
        if abs(event.y - self._y) < fuzz:
            if abs(event.x -self._x) < fuzz:
                self._state = Gdk.CursorType.TOP_LEFT_CORNER
            elif abs(event.x - (self._x + self._width)) < fuzz:
                self._state = Gdk.CursorType.TOP_RIGHT_CORNER
        elif abs(event.y - (self._y + self._height)) < fuzz:
            if abs(event.x - self._x) < fuzz:
                self._state = Gdk.CursorType.BOTTOM_LEFT_CORNER
            elif abs(event.x -(self._x + self._width)) < fuzz:
                self._state = Gdk.CursorType.BOTTOM_RIGHT_CORNER
        elif event.x > self._x and event.x < self._x + self._width \
                 and event.y > self._y and event.y < self._y + self._height:
            self._state = Gdk.CursorType.FLEUR
        else:
            self._state = Gdk.CursorType.LEFT_PTR

        self.get_window().set_cursor(Gdk.Cursor.new(self._state))

    def motion_notify(self, widget, event):
        if self._pressed:
            self._moved = True
            self.update_selection(event)
        else:
            self.update_cursor(event)

    def button_press(self, widget, event):
        self._pressed = True
        self._moved = False
        self._mouse_x = event.x
        self._mouse_y = event.y
        self._press_x = event.x
        self._press_y = event.y
        if event.button == 3:
            self.reset_selection()

    def draw (self, widget, cr):

        #draw pixbuf
        width = self.pixbuf.get_width()
        height = self.pixbuf.get_height()
        cr.rectangle(0, 0, width, height)
        Gdk.cairo_set_source_pixbuf(cr, self.pixbuf, 0, 0)
        cr.fill()

        #draw overlay
        if not MAC:
            self.create_overlay(cr, width, height)

        #draw selection
        cr.rectangle(self._x, self._y, self._width, self._height)
        Gdk.cairo_set_source_pixbuf(cr, self.pixbuf, 0, 0)
        cr.fill ()

        #draw selection border
        cr.set_line_width(2)
        cr.rectangle(self._x, self._y, self._width, self._height)
        cr.set_source_rgba(1, 1, 0.74, 0.5)
        cr.stroke()

        return False

    def create_overlay(self, cr, width, height):
        # Draw a grey overlay
        cr.rectangle(0, 0, width, height)
        cr.set_line_width(0)
        cr.set_source_rgba (0.4, 0.4, 0.4, 0.6)
        cr.fill_preserve()
        cr.stroke()

    def redraw_canvas(self):
        if self.get_window():
            alloc = self.get_allocation()
            self.queue_draw_area(alloc.x, alloc.y, alloc.width, alloc.height)

    def do_get_preferred_width(self):
        if not self.pixbuf:
            return 100, 100

        min_width = self.pixbuf.get_width()
        natural_width = self.pixbuf.get_width()
        return min_width, natural_width

    def do_get_preferred_height(self):
        if not self.pixbuf:
            return 100, 100

        min_height = self.pixbuf.get_height()
        natural_height = self.pixbuf.get_height()
        return min_height, natural_height

    def set_from_pixbuf(self, pixbuf):
        h = pixbuf.get_height()
        w = pixbuf.get_width()
        edge = max(w, h)
        self._trans_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8,
                                            edge, edge)
        self._disp_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8,
                                           edge, edge)

        self._trans_pixbuf.fill(0xffffff00)
        self._disp_pixbuf.fill(0x66666666)

        self.dx = dx = (edge-w)/2
        self.dy = dy = (edge-h)/2

        pixbuf.composite(self._trans_pixbuf, dx, dy, w, h, dx, dy, 1, 1,
                         GdkPixbuf.InterpType.BILINEAR, 255)
        pixbuf.composite(self._disp_pixbuf, dx, dy, w, h, dx, dy, 1, 1,
                         GdkPixbuf.InterpType.BILINEAR, 255)

        maxw = int(0.75 * Gdk.Screen.width())
        maxh = int(0.75 * Gdk.Screen.height())
        if edge >= maxw or edge >= maxh:
            wscale = float(maxw) / edge
            hscale = float(maxh) / edge
            scale = min(wscale, hscale)

            edge = int(edge * scale)

            self._trans_pixbuf = self._trans_pixbuf.scale_simple(edge, edge,
                                                    GdkPixbuf.InterpType.BILINEAR )
            self._disp_pixbuf = self._disp_pixbuf.scale_simple(edge, edge,
                                                    GdkPixbuf.InterpType.BILINEAR )
            self.dx *= scale 
            self.dy *= scale

        self._init_pixbuf()

    def _init_pixbuf(self, angle=GdkPixbuf.PixbufRotation.NONE, create_selection=True):

        self.pixbuf = self._disp_pixbuf.copy()
        self.pixbuf = self.pixbuf.rotate_simple(angle)
        w = 0
        h = 0

        if create_selection:
            sw = min((w, h))
            x1 = int((w-sw)/2)
            y1 = int((h-sw)/2)
            self.selection = (x1, y1, sw, sw)
        else:
            self.selection = (0, 0, 0, 0)

