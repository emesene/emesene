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

import gtk
import cairo
import pango
from sys import platform

if platform == 'darwin':
    MAC = True
else:
    MAC = False

import logging
log = logging.getLogger('gtkui.ImageAreaSelector')

WIDTH=64
HEIGHT=64
NORMALBACKGROUND = gtk.gdk.Color(65025,65025,46155)

class ImageAreaSelectorDialog(gtk.Dialog):

    NAME = 'ImageAreaSelector'
    DESCRIPTION = _('The widget that permits to resize an image added as avatar')
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, callback, pixbuf, title = _("Select area of image"),
                 parent = None):
        gtk.Dialog.__init__(self, title, parent,
                            gtk.DIALOG_DESTROY_WITH_PARENT)
 
        self.callback = callback
        self.set_default_response(gtk.RESPONSE_CANCEL)
        self.set_resizable(False)
        self.button_accept = gtk.Button(stock=gtk.STOCK_OK)
        self.button_accept.connect('clicked', lambda *args: self.response(gtk.RESPONSE_OK))
        self.button_accept.set_sensitive(False)
        self.button_cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
        self.button_cancel.connect('clicked', lambda *args: self.response(gtk.RESPONSE_CANCEL))

        self.selector = ImageAreaSelector(self.button_accept)
        self.selector.set_from_pixbuf(pixbuf)

        if not MAC:
            self.button_rcw = gtk.Button(_("Rotate"))
            self.button_rcw.connect("clicked", self._on_rcw_clicked)
            self.button_rccw = gtk.Button(_("Rotate"))
            self.button_rccw.connect("clicked", self._on_rccw_clicked)

            if gtk.gtk_version >= (2, 10, 0):
                self.action_area.pack_start(self.button_rccw)
                self.action_area.pack_end(self.button_rcw)

        self.action_area.pack_end(self.button_cancel)
        self.action_area.pack_end(self.button_accept)

        ##Draw the statusBar
        self.eventBox = gtk.EventBox()
        box = gtk.HBox(False, 0)
        self.eventBox.set_size_request(0, 30)
        self.eventBox.add(box)
        self.eventBox.modify_bg(gtk.STATE_NORMAL, NORMALBACKGROUND)
        self.label = gtk.Label(_('Draw a square to select an area'))
        self.label.set_ellipsize(pango.ELLIPSIZE_END)
        image = gtk.Image()
        image.set_from_stock (gtk.STOCK_DIALOG_INFO, gtk.ICON_SIZE_LARGE_TOOLBAR)
        box.pack_start(image, False, False, 5)
        box.pack_start(self.label, True, True, 5)

        self.vbox.pack_start(self.selector)
        self.vbox.pack_end(self.eventBox)
        self.vbox.show_all()

    def run(self):
        response = gtk.Dialog.run(self)
        if response == gtk.RESPONSE_OK:
            pixbuf = self.selector.get_selected()
            self.callback(gtk.RESPONSE_OK, pixbuf)
            self.destroy()
        else:
            self.destroy()
            return self.callback(gtk.RESPONSE_CANCEL, None)

    def _on_rcw_clicked(self, *args):
        self.selector.rotate(1)
    def _on_rccw_clicked(self, *args):
        self.selector.rotate(-1)

class ImageAreaSelector(gtk.DrawingArea):
    __gtype_name__ = "ImageAreaSelector"
    def __init__(self, button_accept):
        gtk.DrawingArea.__init__(self)
        self.connect("expose_event", self.expose)
        self.image = None
        self.pixbuf = None
        self.button_accept = button_accept #handle sensitivity of accept button
        self.connect("button_press_event", self.button_press)
        self.connect("button_release_event", self.button_release)
        self.connect("motion_notify_event", self.motion_notify)
        self.connect("configure_event", self.configure_event)
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK |
                        gtk.gdk.BUTTON_RELEASE_MASK |
                        gtk.gdk.POINTER_MOTION_MASK)

        self._pressed = False
        self._moved = False
        self._state = gtk.gdk.LEFT_PTR
        self._has_overlay = False
        self._angle = 0
        self.dx = 0
        self.dy = 0

    def get_selected(self):
        if gtk.gtk_version >= (2, 10, 0):
            angle = self.get_angle()
            self._trans_pixbuf = self._trans_pixbuf.rotate_simple(angle)
        # handle no selection
        if self.selection == (0,0,0,0):
            #this should never happens
            return
            #w = self.pixbuf.get_width()
            #h = self.pixbuf.get_height()
            #sw = min((w, h))
            #x1 = int((w-sw)/2)
            #y1 = int((h-sw)/2)
            #self.selection = (x1, y1, sw, sw)
        
        return self._trans_pixbuf.subpixbuf(*self.selection)

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
        if not self._moved and self._state == gtk.gdk.LEFT_PTR:
            self.reset_selection()


    def expose(self, widget, event):
        if not self._has_overlay and not MAC:
            self.create_overlay()
        x , y, width, height = event.area

        widget.window.draw_drawable(widget.get_style().fg_gc[gtk.STATE_NORMAL],
                                    self.pixmap_shaded, 0, 0,
                                    0, 0,
                                    self.pixbuf.get_width(),
                                    self.pixbuf.get_height())

        widget.window.draw_pixbuf(None, pixbuf=self.pixbuf,
                                  src_x=self._x,
                                  src_y=self._y,
                                  dest_x= self._x,
                                  dest_y=self._y ,
                                  width=self._width, height=self._height,
                                  dither=gtk.gdk.RGB_DITHER_NORMAL,
                                  x_dither=0, y_dither=0)
        return False



    def rotate(self, angle):
        self._angle = (self._angle + angle) % 4
        angle = self.get_angle()
        self._init_pixbuf(angle, False)

    def get_angle(self):
        if not gtk.gtk_version >= (2, 10, 0):
            return 0

        if self._angle == 1:
            angle = gtk.gdk.PIXBUF_ROTATE_CLOCKWISE
        elif self._angle == 2:
            angle = 180
        elif self._angle == 3:
            angle = gtk.gdk.PIXBUF_ROTATE_COUNTERCLOCKWISE
        else:
            angle = 0
        return angle

    def update_selection(self, event):
        # track mouse delta
        dx = event.x - self._mouse_x
        dy = event.y - self._mouse_y

        x1, y1, x2, y2 = self._get_sel_coord()
        if self._state == gtk.gdk.TOP_LEFT_CORNER:
            w = x2 - event.x
            h = y2 - event.y
            delta = max((w, h))
            x1 = x2 - delta
            y1 = y2 - delta
        elif self._state == gtk.gdk.TOP_RIGHT_CORNER:
            w = event.x - x1
            h = y2 - event.y
            delta = max((w, h))
            x2 = x1 + delta
            y1 = y2 - delta
        elif self._state == gtk.gdk.BOTTOM_RIGHT_CORNER:
            w = (event.x-x1)
            h = (event.y-y1)
            delta = max((w, h))
            x2 = x1 + delta
            y2 = y1 + delta
        elif self._state == gtk.gdk.BOTTOM_LEFT_CORNER:
            w = x2 - event.x
            h = (event.y-y1)
            delta = max((w, h))
            x1 = x2 - delta
            y2 = y1 + delta
        elif self._state == gtk.gdk.FLEUR:
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
                self._state = gtk.gdk.TOP_LEFT_CORNER
            elif abs(event.x - (self._x + self._width)) < fuzz:
                self._state = gtk.gdk.TOP_RIGHT_CORNER
        elif abs(event.y - (self._y + self._height)) < fuzz:
            if abs(event.x - self._x) < fuzz:
                self._state = gtk.gdk.BOTTOM_LEFT_CORNER
            elif abs(event.x -(self._x + self._width)) < fuzz:
                self._state = gtk.gdk.BOTTOM_RIGHT_CORNER
        elif event.x > self._x and event.x < self._x + self._width \
                 and event.y > self._y and event.y < self._y + self._height:
            self._state = gtk.gdk.FLEUR
        else:
            self._state = gtk.gdk.LEFT_PTR

        self.window.set_cursor(gtk.gdk.Cursor(self._state))

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

    def configure_event(self, widget, event):
        x, y, width, height = widget.get_allocation()

        self.pixmap = gtk.gdk.Pixmap(widget.window, width, height)
        self.pixmap.draw_rectangle(widget.get_style().white_gc,
                                   True, 0, 0, width, height)

        self.pixmap_shaded = gtk.gdk.Pixmap(widget.window, width, height)
        self.pixmap_shaded.draw_rectangle(widget.get_style().white_gc,
                                          True, 0, 0, width, height)
        self._has_overlay = False
        return True

    def create_overlay(self):
        context = self.pixmap_shaded.cairo_create()
        width = self.pixbuf.get_width()
        height = self.pixbuf.get_height()

        target  = context.get_target()
        overlay = target.create_similar(cairo.CONTENT_COLOR_ALPHA, width, height)
        punch   = target.create_similar(cairo.CONTENT_ALPHA, width, height)
        context.set_source_pixbuf(self.pixbuf, 0, 0)
        context.fill()
        context.paint()

        # Draw a grey overlay
        overlay_cr = cairo.Context (overlay)
        overlay_cr.set_source_rgba (0.4, 0.4, 0.4, 0.6)
        overlay_cr.rectangle(0, 0, width, height)
        overlay_cr.fill()

        context.set_source_surface (overlay, 0, 0)
        context.paint()
        self._has_overlay = True


    def redraw_canvas(self):
        if self.window:
            alloc = self.get_allocation()
            self.queue_draw_area(alloc.x, alloc.y, alloc.width, alloc.height)

    def do_size_request(self, requisition):
        if not self.pixbuf:
            return
        requisition.width = self.pixbuf.get_width()
        requisition.height = self.pixbuf.get_height()

    def set_from_pixbuf(self, pixbuf):
        h = pixbuf.get_height()
        w = pixbuf.get_width()
        edge = max(w, h)
        self._trans_pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8,
                                            edge, edge)
        self._disp_pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8,
                                           edge, edge)

        self._trans_pixbuf.fill(0xffffff00)
        self._disp_pixbuf.fill(0x66666666)

        self.dx = dx = (edge-w)/2
        self.dy = dy = (edge-h)/2

        pixbuf.composite(self._trans_pixbuf, dx, dy, w, h, dx, dy, 1, 1,
                         gtk.gdk.INTERP_BILINEAR, 255)
        pixbuf.composite(self._disp_pixbuf, dx, dy, w, h, dx, dy, 1, 1,
                         gtk.gdk.INTERP_BILINEAR, 255)

        maxw = int(0.75 * gtk.gdk.screen_width())
        maxh = int(0.75 * gtk.gdk.screen_height())
        if w > maxw or h > maxh:
            wscale = float(maxw) / edge
            hscale = float(maxh) / edge
            scale = min(wscale, hscale)

            edge = int(edge * scale)

            self._trans_pixbuf = self._trans_pixbuf.scale_simple(edge, edge,
                                                    gtk.gdk.INTERP_BILINEAR )
            self._disp_pixbuf = self._disp_pixbuf.scale_simple(edge, edge,
                                                    gtk.gdk.INTERP_BILINEAR )
            self.dx *= scale 
            self.dy *= scale

        self._init_pixbuf()

    def _init_pixbuf(self, angle=None, create_selection=True):
        self.pixbuf = self._disp_pixbuf.copy()

        if angle and gtk.gtk_version >= (2, 10, 0):
            self.pixbuf = self.pixbuf.rotate_simple(angle)
            self.configure_event(self, None)
            tmp = self.dx
            self.dx = self.dy
            self.dy = tmp

        self._has_overlay = False
        w = 0
        h = 0

        if create_selection:
            sw = min((w, h))
            x1 = int((w-sw)/2)
            y1 = int((h-sw)/2)
            self.selection = (x1, y1, sw, sw)
        else:
            self.selection = (0, 0, 0, 0)
