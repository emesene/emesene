'''Manager for avatars'''
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
import gtk
import cairo
import gobject

class AvatarManager(gtk.Widget):
    '''Manager for avatars'''

    #key-position, is aa Anchor Type constant. Refer to 
    #http://www.pygtk.org/docs/pygtk/gtk-constants.html#gtk-anchor-type-constants

    def __init__(self, cell_dimension = 32, cell_radius = 0.11,
                crossfade = True, cell_key_position = gtk.ANCHOR_CENTER):
        ''' constructor'''
        gtk.Widget.__init__(self)

        self.filename = ''
        self._pixbuf = None
        self._image = None
        self._dimension = cell_dimension
        self._radius_factor = cell_radius
        self._key_position = cell_key_position
        self._offline = False

        # variables related to animation
        self._crossfade = crossfade
        self.in_animation = False
        self.duration = 1500 # milliseconds
        self.fps = 24 # frames per second
        self.total_frames = 0
        self.current_frame = 0
        self.transition_pixbuf = None
        self.anim_source = None
        self.current_animation = None

    def do_get_property(self, property):
        if property.name == 'image':
            return self._image
        elif property.name == 'dimension':
            return self._dimension
        elif property.name == 'radius-factor':
            return self._radius_factor
        elif property.name == 'offline':
            return self._offline
        elif property.name == 'pixbuf':
            return self._pixbuf
        elif property.name == 'pixbuf-animation':
            return self._pixbuf
        elif property.name == 'key-position':
            return self._key_position
        elif property.name == 'crossfade':
            return self._crossfade
        else:
            raise AttributeError, 'unknown property %s' % property.name

    def do_set_property(self, property, value):
        if property.name == 'image':
            self._image = value
        elif property.name == 'dimension':
            self._dimension = value
        elif property.name == 'radius-factor':
            self._radius_factor = value
        elif property.name == 'offline':
            self._offline = value
        elif property.name == 'pixbuf':
            self._set_pixbuf(value)
        elif property.name == 'pixbuf-animation':
            self._pixbuf = value
        elif property.name == 'key-position':
            self._key_position = value
        elif property.name == 'crossfade':
            self._crossfade = value
        else:
            raise AttributeError, 'unknown property %s' % property.name

    def _set_pixbuf(self, pixbuf):
        '''set the pixbuf or crossfades to it'''
        if self.__should_replace(pixbuf):
            if self._crossfade and not (self._pixbuf is None) \
                and not (pixbuf is None):
                self.transition_pixbuf = pixbuf

                if self.fps < 1:
                    self.fps = 24 # reset fps if not valid fps

                time_between_frames = 1000 // self.fps
                self.total_frames = self.duration // time_between_frames
                self.current_frame = 1
                gobject.timeout_add(time_between_frames,
                    self.animate_callback)
                self.in_animation = True
            else:
                self._pixbuf = pixbuf

    def __should_replace(self, pixbuf):
        '''check the equivalence'''
        if self._pixbuf and pixbuf and \
          pixbuf.get_pixels() == self._pixbuf.get_pixels():
            return False
        else:
            return True

    def draw_avatar(self, context, pixbuf, xpos, ypos, dimension,
                    position, radius, alpha):
        '''draw the avatar'''
        context.save()
        context.set_antialias(cairo.ANTIALIAS_SUBPIXEL)
        context.translate(xpos, ypos)

        pix_width = pixbuf.get_width()
        pix_height = pixbuf.get_height()

        if (pix_width > dimension) or (pix_height > dimension):
            scale_factor = float(dimension) / max (pix_width, pix_height)
        else:
            scale_factor = 1

        scale_width = pix_width * scale_factor
        scale_height = pix_height * scale_factor

        #tranlate position
        self.translate_key_postion(context, position, dimension,
                dimension, scale_width, scale_height)

        if radius > 0 :
            self.rounded_rectangle(context, 0, 0, scale_width,
                    scale_height, dimension * radius)
            context.clip()

        context.scale(scale_factor, scale_factor)
        context.set_source_pixbuf(pixbuf, 0, 0)
        context.paint_with_alpha(alpha)
        context.restore()

    def translate_key_postion(self, context, position, width, height,
                             scale_width, scale_height):
        ''' translate anchor type constants to an actual position'''
        if position in (gtk.ANCHOR_NORTH_WEST, gtk.ANCHOR_WEST,
                        gtk.ANCHOR_SOUTH_WEST):
            xpos = 0
        elif position in (gtk.ANCHOR_NORTH, gtk.ANCHOR_CENTER,
                          gtk.ANCHOR_SOUTH):
            xpos = (width // 2) - (scale_width // 2)
        else:
            xpos = width - scale_width

        if position in (gtk.ANCHOR_NORTH_WEST, gtk.ANCHOR_NORTH,
                        gtk.ANCHOR_NORTH_EAST):
            ypos = 0
        elif position in (gtk.ANCHOR_EAST, gtk.ANCHOR_CENTER,
                          gtk.ANCHOR_WEST):
            ypos = (height // 2) - (scale_height // 2)
        else:
            ypos = height - scale_height

        context.translate(xpos, ypos)

    def rounded_rectangle(self, context, xpos, ypos, width, height, radius=5):
        """Create rounded rectangle path"""
        # http://cairographics.org/cookbook/roundedrectangles/
        # modified from mono moonlight aka mono silverlight
        # test limits (without using multiplications)
        # http://graphics.stanford.edu/courses/cs248-98-fall/Final/q1.html

        arc_to_bezier = 0.55228475

        if radius > (min(width, height)/2):
            radius = (min(width, height)/2)

        #approximate (quite close) the arc using a bezier curve
        c = arc_to_bezier * radius

        context.new_path()
        context.move_to(xpos + radius, ypos)
        context.rel_line_to(width - 2 * radius, 0.0)
        context.rel_curve_to(c, 0.0, radius, c, radius, radius)
        context.rel_line_to(0, height - 2 * radius)
        context.rel_curve_to(0.0, c, c - radius, radius, -radius, radius)
        context.rel_line_to(-width + 2 * radius, 0)
        context.rel_curve_to(-c, 0, -radius, -c, -radius, -radius)
        context.rel_line_to(0, -height + 2 * radius)
        context.rel_curve_to(0.0, -c, radius - c, -radius, radius, -radius)
