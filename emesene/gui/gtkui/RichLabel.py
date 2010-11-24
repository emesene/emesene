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
import cairo

import protocol 
import RichWidget
import e3common.XmlParser

class RichLabel(gtk.DrawingArea, RichWidget.RichWidget):
    '''a widget that can display rich text'''

    def __init__(self, text='', border_width=0, margin_top=2, margin_left=2,
            margin_bottom=2, margin_right=2):
        '''constructor'''
        RichWidget.RichWidget.__init__(self)
        gtk.DrawingArea.__init__(self)

        self.do_new_line = False
        # the x and y coordinates of the next item
        # to be added
        self.next_item_x = 0
        self.next_item_y = None
        self.max_x = 0

        self.margin_top = margin_top
        self.margin_bottom = margin_bottom
        self.margin_left = margin_left
        self.margin_right = margin_right

        self.text = text
        self.connect("expose_event", self.do_expose_event)

    def _set_text(self, text):
        '''set the value of text and parse the value'''
        self._text = text
        result = e3common.XmlParser.XmlParser(
            '<span>' + text.replace('\n', '') + '</span>').result
        # hold the parsed structure to not parse it every time we
        # draw the widget
        self._parsed = e3common.XmlParser.DictObj(result)

    def _get_text(self):
        '''return the value of text'''
        return self._text

    text = property(fget=_get_text, fset=_set_text)

    # Handle the expose-event by drawing
    def do_expose_event(self, widget, event):
        '''override the expose event handler'''

        # Create the cairo context
        cr = self.window.cairo_create()

        # Restrict Cairo to the exposed area; avoid extra work
        cr.rectangle(event.area.x, event.area.y,
                event.area.width, event.area.height)
        cr.clip()
        print 'expose'
        self.draw(cr, *self.window.get_size())

    def _draw_image(self, x, y, path):
        '''draw an image in the current position'''
        sf_base = cairo.ImageSurface.create_from_png(path)
        width = sf_base.get_width()
        height = sf_base.get_height()

        x, y = self._update_coords(height, x, y)

        cr = self.window.cairo_create()
        cr.set_source_surface(sf_base, x, y - height)
        cr.paint()

        return (x + width, y)

    def _draw_text(self, x, y, text, fg_color=None, bg_color=None, font=None,
        size=None, bold=False, italic=False, underline=False, strike=False):
        '''draw text in the current position with the properties defined'''
        foreground = None
        background = None

        cr = self.window.cairo_create()
        rgb = cr.get_source().get_rgba()[:3]

        if font is None:
            font = self.get_style().font_desc.get_family()

        if size is None or size < 0 or size > 48:
            size = self.get_style().font_desc.get_size() / pango.SCALE

        bold_style = cairo.FONT_WEIGHT_NORMAL

        if bold:
            bold_style = cairo.FONT_WEIGHT_BOLD

        italic_style = cairo.FONT_SLANT_NORMAL

        if italic:
            italic_style = cairo.FONT_SLANT_ITALIC

        cr.select_font_face(font, italic_style, bold_style)

        if size:
            cr.set_font_size(size)

        fascent, fdescent, fheight, fxadvance, fyadvance = cr.font_extents()
        xbearing, ybearing, width, height, xadvance, yadvance = \
            cr.text_extents(text)

        x, y = self._update_coords(height, x, y)

        if bg_color:
            background = protocol.Color.from_hex(bg_color)
            cr.set_source_rgb(*tuple(background))
            cr.rectangle(x + xbearing, y + ybearing, width, height)
            cr.fill()

        if fg_color:
            foreground = protocol.Color.from_hex(fg_color)
            cr.set_source_rgb(*tuple(foreground))
        else:
            cr.set_source_rgb(*rgb)

        cr.move_to (x + xbearing, y)
        cr.show_text(text)

        cr.set_line_width(1 * self.px)

        if strike:
            cr.move_to(x, y - height / 2)
            cr.rel_line_to(xadvance + xbearing, 0)

        if underline:
            cr.move_to(x, y + 2 * self.px)
            cr.rel_line_to(xadvance + xbearing, 0)

        cr.stroke ()
        cr.set_source_rgb(*rgb)

        return (x + xadvance + xbearing, y)

    def _update_coords(self, height, x, y):
        '''update the coordinates'''
        # if this is the first item calculate the initial y coords
        if self.next_item_y is None:
            y = height
            self.next_item_y = y + self.margin_left * self.px

        if self.do_new_line:
            y += height + self.px * 5
            self.next_item_y = y
            x = self.next_item_x = 0
            self.do_new_line = False

        self.set_size_request(int(self.max_x + self.margin_right * self.px),
                int(self.next_item_y + self.margin_bottom * self.px))

        return x, y

    def draw(self, cr, width, height):
        '''called to draw the widget content'''
        self.next_item_y = None
        self.px = max(cr.device_to_user_distance(1, 1))
        self.next_item_x = self.margin_top * self.px

        self.width = width
        self.height = height
        self._put_formatted(self._parsed)

    def put_image(self, path, alt=None):
        '''put an image on the widget'''
        (next_x, next_y) = self._draw_image(self.next_item_x,
            self.next_item_y, path)

        if next_x > self.max_x:
            self.max_x = next_x

        self.next_item_x = next_x
        self.next_item_y = next_y

    def put_text(self, text, fg_color=None, bg_color=None, font=None, size=None,
        bold=False, italic=False, underline=False, strike=False):
        '''insert text at the current position with the style defined by the
        optional parameters'''
        (next_x, next_y) = self._draw_text(self.next_item_x,
            self.next_item_y, text, fg_color, bg_color, font, size, bold,
            italic, underline, strike)

        if next_x > self.max_x:
            self.max_x = next_x

        self.next_item_x = next_x
        self.next_item_y = next_y

    def new_line(self):
        '''put a new line on the text'''
        self.do_new_line = True

if __name__ == "__main__":
    window = gtk.Window()
    window.connect("delete-event", gtk.main_quit)
    text = '''<i>ital<b>i</b>c</i><br/>
<u>under<s>lin<b>ed</b></s></u><br/>
<em>emph<strong>as<span style="color: #CC0000; background-color: #00CC00">is</span></strong></em><br/>
<span style="font-size: 14;">size <span style="font-family: Arial;">test</span></span>
<img src="themes/emotes/default/face-sad.png" alt=":("/><img src="themes/emotes/default/face-smile.png" alt=":)"/>
&lt;-- see that? it is an image! <b>asd</b>'''
    widget = RichLabel(text)
    widget.show()
    window.add(widget)
    window.present()
    gtk.main()
