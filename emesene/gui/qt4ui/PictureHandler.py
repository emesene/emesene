# -*- coding: utf-8 -*-

from PyQt4          import QtGui
from PyQt4.QtCore   import Qt

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
        
        format = QtGui.QImageReader(source_filename).format()
        if format == 'gif' or format == 'pbm' or format == 'pgm':
            self._is_animated = True
        else:
            self._qimage = QtGui.QImage(source_filename)
        
    
    
    def resize(self, new_size):
        '''Resizes to new_size the given avatar pix. Overrides base's 
        class abstract method.'''
        if not self.is_animated():
            self._qimage = self._qimage.scaled(new_size, new_size, 
                                               Qt.IgnoreAspectRatio, 
                                               Qt.SmoothTransformation)
        
            
    def _save(self, dest_filename):
        '''Saves the image to disk'''
        self._qimage.save(dest_filename, 'png')
        self._source_filename = dest_filename
        
        
    def is_animated(self):
        '''Returns true if the image is an animation'''
        return self._is_animated
        
    @staticmethod
    def from_toolkit(pix):
        '''Builds a PictureHandler object from a pix object, whose type
        is gtk.gdk.Pixbuf.'''
        picturehandler = PictureHandler()
        picturehandler._qimage = QtGui.QImage(pix)
        return picturehandler
