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
import gtk.gdk
import cairo
import gobject

import gui
import extension
from AvatarManager import AvatarManager

class Avatar(AvatarManager):
    """AvatarWidget """
    #TODO move in an avatarManager class?????

    __gproperties__ = {
        'dimension': (gobject.TYPE_FLOAT, 'cell dimensions',
            'height width of cell', 0.0, 128.0, 32.0,
            gobject.PARAM_READWRITE),
        'radius-factor': (gobject.TYPE_FLOAT, 'radius of pixbuf',
            '0.0 to 0.5 with 0.1 = 10% of dimension', 0.0, 0.5, 0.11,
            gobject.PARAM_READWRITE),
        'pixbuf': (gtk.gdk.Pixbuf, 'Pixbuf', 'normal pixbuf',
            gobject.PARAM_READWRITE),
        'pixbuf-animation': (gtk.gdk.Pixbuf, 'Pixbuf', 'pixbuf from animation',
            gobject.PARAM_READWRITE),
        'crossfade': (bool, 'animate by crossfade if true','',True,
            gobject.PARAM_READWRITE),
        'key-position': (object, 'position of avatar',
            'corresponds to position of key in numpad',
            gobject.PARAM_READWRITE),
         }

    __gsignals__ = { 'size_request': 'override', 'expose-event': 'override' }

    def __init__(self, cell_dimension = 96, crossfade = True, cell_radius = 0.05,
                 cell_key_position = gtk.ANCHOR_CENTER):
        AvatarManager.__init__(self, cell_dimension, cell_radius, crossfade,
            cell_key_position)
        self.set_flags(self.flags() | gtk.NO_WINDOW)

    def animate_callback(self):
        if self.current_frame > self.total_frames:
            self.in_animation = False
            self._pixbuf = self.transition_pixbuf

            if self.current_animation:
                self._start_animation(self.current_animation)
            return False
        else:

            if self.anim_source is not None:
                gobject.source_remove(self.anim_source)
                self.anim_source = None
            self.current_frame += 1
            self.queue_draw()
            return True

    def __set_from_pixbuf(self, pixbuf):
        self.set_property('pixbuf', pixbuf)
        self.queue_draw()

    def __set_from_pixbuf_animation(self, pixbuf):
        self.set_property('pixbuf-animation', pixbuf)
        self.queue_draw()

    #
    #public methods
    #
    def set_from_file(self, filename):
        self.filename = filename
        if not gui.gtkui.utils.file_readable(filename):
            self.filename = gui.theme.get_image_theme().logo

        try:
            animation = gtk.gdk.PixbufAnimation(filename)
        except gobject.GError:
            animation = gtk.gdk.PixbufAnimation(gui.theme.get_image_theme().logo)

        if animation.is_static_image():
            self.__set_from_pixbuf(animation.get_static_image())
            self.current_animation = None
            return

        self.current_animation = animation
        self._start_animation(animation)

    def set_from_image(self, image):
        if image.get_storage_type() == gtk.IMAGE_PIXBUF:
            self.__set_from_pixbuf(image.get_pixbuf())
            self.current_animation = None
            return
        elif image.get_storage_type() == gtk.IMAGE_ANIMATION:
            self.current_animation = image.get_animation()
            self._start_animation(image.get_animation())

    def stop(self):
        '''stop the animation'''
        if self.anim_source is not None:
            gobject.source_remove(self.anim_source)
            self.anim_source = None
    #
    #end of public methods
    #

    def _start_animation(self, animation):
        iteran = animation.get_iter()
        #we don't need to resize here!
        self.__set_from_pixbuf(iteran.get_pixbuf())

        if self.anim_source is None:
            self.anim_source = gobject.timeout_add(iteran.get_delay_time(), self._advance, iteran)

    def _advance(self, iteran):
        iteran.advance()
        self.__set_from_pixbuf_animation(iteran.get_pixbuf())
        self.anim_source = gobject.timeout_add(iteran.get_delay_time(), self._advance, iteran)
        return False

    def do_size_request(self,requisition):
        requisition.width = self._dimension
        requisition.height = self._dimension

    def do_expose_event(self, evnt):
        if not self._pixbuf: return

        ctx = evnt.window.cairo_create()
        cell_area = self.get_allocation()

        cell_x, cell_y, cell_width, cell_height = cell_area
        if self.in_animation:
            self.draw_avatar(ctx, self._pixbuf, cell_x,
                cell_y, self._dimension, self._key_position, self._radius_factor,
                1 - (float(self.current_frame) / self.total_frames))
            self.draw_avatar(ctx, self.transition_pixbuf,
                cell_x, cell_y, self._dimension, self._key_position, self._radius_factor,
                (float(self.current_frame) / self.total_frames))
        else:
            self.draw_avatar(ctx, self._pixbuf, cell_x,
                cell_y, self._dimension, self._key_position, self._radius_factor, 1)


gobject.type_register(Avatar)
