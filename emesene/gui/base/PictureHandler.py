# -*- coding: utf-8 -*-

#   This file is part of emesene.
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

'''This module contains the abstract class "PictureHandler", intended to save 
and resize images.'''

import shutil


class PictureHandler (object): 
    '''PictureHandler is an object that provides means to scale pictures and
    save them to disk. It must be subclassed overriding abstract methods with
    the actual save / scale routines.'''
    
    # This could be useful for issue #93:
    # We could check here for imagemagick or whatever
    
    def __init__(self, source_filename=None):
        '''Constructor'''
        self._source_filename = source_filename
    
    
    def resize(self, new_size):
        '''Resizes to new_size the given avatar pix'''
        raise NotImplementedError("Method not implemented")
        
        
    def save(self, dest_filename):
        '''Saves to disk the given avatar pix'''
        if self.is_animated():
            shutil.copy(self._source_filename, dest_filename)
        else:
            self._save(dest_filename)
            
        
    def _save(self, dest_filename):
        '''This method actually saves the pixmap to disk'''
        raise NotImplementedError("Method not implemented")
    
        
    def is_animated(self):
        '''Return true if this object is operating on an animated image'''
        raise NotImplementedError("Method not implemented")
    
    
    @staticmethod
    def from_toolkit(pix):
        '''Builds a PictureHandler object from a pix object, whose type
        depends on the particular gui toolkit used.'''
        raise NotImplementedError("Method not implemented")
    
    
