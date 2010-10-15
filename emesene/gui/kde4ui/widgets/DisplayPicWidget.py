# -*- coding: utf-8 -*-

''' This module contains the DisplayPic class'''

import PyQt4.QtGui      as QtGui
import PyQt4.QtCore     as QtCore
from PyQt4.QtCore   import Qt

class DisplayPic (QtGui.QLabel):
    ''' A DisplayPic widget. Supports changing the displayPic, and emits
    a "clicked" signal.'''
    FRAMESIZE = QtCore.QSize(104, 104)
    PIXMAPSIZE = QtCore.QSize(96, 96)

    def __init__(self, parent = None):
        '''constructor'''
        QtGui.QLabel.__init__(self, parent)
        self.__clickable = True
        self.mask = QtGui.QBitmap("/home/rayleigh/src/aMSN2/\
                            amsn2/ui/front_ends/kde4/mask.bmp")
        self.setFrameStyle(QtGui.QFrame.StyledPanel)
        self.setFrameShadow(QtGui.QFrame.Raised)
        path = ""#KFEThemeManager().pathOf("dp_amsn")
        pixmap = QtGui.QPixmap(path)
        pixmap.setMask(self.mask)
        self.set_display_pic(pixmap)
        self.installEventFilter(self)


    def set_display_pic(self, path):
        ''' sets the display pic'''
        pixmap = QtGui.QPixmap(path)
        pixmap.setMask(self.mask)
        self.setPixmap(pixmap.scaled(self.PIXMAPSIZE))
        self.adjust_size()

    def set_clickable(self, clickable):
        ''' enables or disables clicks '''
        self.__clickable = clickable

    def is_clickable(self):
        ''' returns true if the widget is clickable, False otherwise'''
        return self.__clickable

    def adjust_size(self):
        ''' resizes the display pic to the correct size'''
        self.setMinimumSize(self.FRAMESIZE)
        self.setMaximumSize(self.FRAMESIZE)

    #separate in keyPressEvent and keyReleaseEvent
    def eventFilter(self, obj, event):
        ''' custom event filter '''
        # pylint: disable=C0103
        if not obj == self:
            return False
        if not isinstance(event, QtGui.QMouseEvent):
            return False
        if not self.is_clickable():
            return False
        elif event.type() == QtCore.QEvent.MouseButtonRelease and    \
             event.button() == Qt.LeftButton:
            self.setFrameShadow(QtGui.QFrame.Raised)
            self.adjust_size()
            self.emit(QtCore.SIGNAL("clicked()"))
            return True
        elif event.type() == QtCore.QEvent.MouseButtonPress and  \
             event.button() == Qt.LeftButton:
            self.setFrameShadow(QtGui.QFrame.Sunken)
            self.adjust_size()
            return True
        else:
            return False





