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

class AvatarManager(object):
    '''Manager for avatars'''

    def __init__(self):
        ''' constructor'''
        pass

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
