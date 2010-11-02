# -*- coding: utf-8 -*-

#   This file is part of emesene.
#
#    Emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
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

from gui   import base


class PictureHandler (base.PictureHandler): 
    NAME = 'PictureHandler'
    DESCRIPTION = 'An object to manipulate images using ' \
                   'gui toolkit\'s facilities'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''
    
    def __init__(self, source_filename=None):
        '''Constructor'''
        base.PictureHandler.__init__(self, source_filename)
        self._is_animated = False
        
        if not source_filename:
            return
            
        self._pixbuf = gtk.gdk.PixbufAnimation(source_filename)
        if self._pixbuf.is_static_image():
            self._pixbuf = gtk.gdk.pixbuf_new_from_file(source_filename)
            self._is_animated = False
        else:
            self._is_animated = True
    
    
    def resize(self, new_size):
        '''Resizes to new_size the given avatar pix. Overrides base's 
        class abstract method.'''
        if not self.is_animated():
            self._pixbuf = self._pixbuf.scale_simple(new_size, new_size, 
                                                   gtk.gdk.INTERP_BILINEAR)
        
            
    def _save(self, dest_filename):
        '''Saves the image to disk'''
        self._pixbuf.save(dest_filename, 'png')
        self._source_filename = dest_filename
        
        
    def is_animated(self):
        '''Returns true if the image is an animation'''
        return self._is_animated
        
    @staticmethod
    def from_toolkit(pix):
        '''Builds a PictureHandler object from a pix object, whose type
        is gtk.gdk.Pixbuf.'''
        picturehandler = PictureHandler()
        picturehandler._pixbuf = pix
        return picturehandler
    
    
    
