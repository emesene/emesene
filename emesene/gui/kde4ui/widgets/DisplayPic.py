# -*- coding: utf-8 -*-

''' This module contains the DisplayPic class'''

import PyKDE4.kdeui     as KdeGui
import PyQt4.QtGui      as QtGui
import PyQt4.QtCore     as QtCore
from PyQt4.QtCore   import Qt


import gui

class DisplayPic (QtGui.QLabel):
    ''' A DisplayPic widget. Supports changing the displayPic, and emits
    a "clicked" signal.'''
    FRAMESIZE = QtCore.QSize(104, 104)
    PIXMAPSIZE = QtCore.QSize(96, 96)

    clicked = QtCore.pyqtSignal()
    
    def __init__(self, config_dir, server_host, parent = None):
        '''constructor'''
        QtGui.QLabel.__init__(self, parent)
        self._config_dir = config_dir
        self._server_host = server_host
        self._clickable = True
        self._fader = PixmapFader(self._draw_pixmap, self.PIXMAPSIZE)
        self.mask = QtGui.QBitmap(
            "/home/rayleigh/src/aMSN2/amsn2/ui/front_ends/kde4/mask.bmp")
        self.setFrameStyle(QtGui.QFrame.StyledPanel)
        self.setFrameShadow(QtGui.QFrame.Raised)
        self.set_logo()
        self.installEventFilter(self)

    def set_logo(self):
        ''' sets emesene's logo as a display pic'''
        path = gui.theme.logo
        self._set_display_pic(path)
    
    def set_display_pic(self, account, contact='', display_pic='last' ):
        '''set a display pic from the account's name, the contact name, and pic
        name. If no contact is provided, the account's user's pic is set.
        If no pic is specified, then the last one is set'''
        path = self._config_dir.join(self._server_host, account, 
                                    contact, 'avatars', display_pic)
        self._set_display_pic(path)

    def _set_display_pic(self, path):
        ''' sets the display pic from the path'''
        pixmap = QtGui.QPixmap(path)
        if pixmap.isNull():
            return
        if not pixmap.hasAlpha():
            print " NO ALPHA"
            pixmap.setMask(self.mask)
        else:
            print "ALPHA DETECTED"
        self._fader.add_pixmap(pixmap)
#        self.setPixmap(pixmap.scaled(self.PIXMAPSIZE))
#        self.adjust_size()

    def _draw_pixmap(self, pixmap):
        '''Actually displays a pixmap. This is the callback method invoked by
        the PixmapFader when there's a new frame to display'''
        self.setPixmap(pixmap)
        self.adjust_size()

    def set_clickable(self, clickable):
        ''' enables or disables clicks '''
        self._clickable = clickable

    def is_clickable(self):
        ''' returns true if the widget is clickable, False otherwise'''
        return self._clickable

    def adjust_size(self):
        ''' resizes the display pic to the correct size'''
        self.setMinimumSize(self.FRAMESIZE)
        self.setMaximumSize(self.FRAMESIZE)
        
    # -------------------- QT_OVERRIDE

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
            self.clicked.emit()
            return True
        elif event.type() == QtCore.QEvent.MouseButtonPress and  \
             event.button() == Qt.LeftButton:
            self.setFrameShadow(QtGui.QFrame.Sunken)
            self.adjust_size()
            return True
        else:
            return False

class PixmapFader(QtCore.QObject):
    '''Class which provides a fading animation between QPixmaps'''
    def __init__(self, callback, pixmap_size, first_pic=None, parent=None):
        '''Constructor'''
        QtCore.QObject.__init__(self, parent)
        self._pixmaps = []
        self._size = pixmap_size
        self._rect = QtCore.QRect(QtCore.QPoint(0, 0), self._size)
        self._callback = callback
        # timer initialization
        self._timer = QtCore.QTimer(KdeGui.KApplication.instance())
        self._timer.timeout.connect(self._on_timeout)
        self._fpms = 0.12 # frames / millisencond
        self._duration = 1000.0 # millisecond
        self._frame_time = 1 / self._fpms
        self._alpha_step = self._frame_time / self._duration
        # pixmap painting initializations
        self._result = QtGui.QPixmap(gui.theme.logo)
        self._result.fill(Qt.transparent)
        self._painter = QtGui.QPainter(self._result)
        
    def __del__(self): 
        '''Destructor. Note: without this explicit destructor, we get a SIGABRT
        due to a failed assertion in xcb.'''
        self._painter.end()
        
    def add_pixmap(self, pixmap):
        '''Adds a pixmap to the pixmap stack'''
        if pixmap.isNull():
            return
        pixmap = pixmap.scaled(self._size)
        number_of_pixmaps = len(self._pixmaps)
        
        # no pixmap yet:        
        if number_of_pixmaps == 0:
            self._painter.save()
            self._pixmaps.append((pixmap, 1))
            self._painter.drawPixmap(self._rect, pixmap, self._rect)
            self._painter.restore()
            self._callback(self._result)
            return
       
        # the pixmap is the same as the last one:
        if pixmap.toImage() == self._pixmaps[-1][0].toImage():
            return
            
        # we have already one pixmap:     
        if number_of_pixmaps == 1:
            self._pixmaps.append((pixmap, 0))
            self._timer.start(self._frame_time)
            return
            
        # we have already two pixmap:
        if number_of_pixmaps == 2:
            self._pixmaps[0] = (self._result, 1)
            self._pixmaps[1] = (pixmap, 0)
            self._timer.start(self._frame_time)
        
        # ops...
        if number_of_pixmaps > 2:
            raise RuntimeError('[BUG] Too many pixmaps!')
        
        
    def _on_timeout(self):
        '''Compute a frame. This method is called by a QTimer 
        various times per second.'''
        old_pixmap, old_opacity = self._pixmaps[0]
        new_pixmap, new_opacity = self._pixmaps[1]
        
        if old_opacity < 0 and new_opacity > 1:
            self._timer.stop()
            self._pixmaps.remove(self._pixmaps[0])
            self._pixmaps[0] = (new_pixmap, 1)
            return
            
        old_opacity -= self._alpha_step
        new_opacity += self._alpha_step
         
        self._pixmaps[0] = (old_pixmap, old_opacity)
        self._pixmaps[1] = (new_pixmap, new_opacity)
            
        painter = self._painter
        painter.save()
        #painter.fillRect(self._rect, Qt.transparent)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_Source)
        painter.setOpacity(old_opacity)
        painter.drawPixmap(self._rect, old_pixmap, self._rect)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
        painter.setOpacity(new_opacity)
        painter.drawPixmap(self._rect, new_pixmap, self._rect)
        painter.restore()
        
        self._callback(self._result)
        
        
        
        


