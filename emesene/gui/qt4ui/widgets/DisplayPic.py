# -*- coding: utf-8 -*-

''' This module contains the DisplayPic class'''

from PyQt4          import QtGui
from PyQt4          import QtCore
from PyQt4.QtCore   import Qt


import gui


class DisplayPic (QtGui.QLabel):
    ''' A DisplayPic widget. Supports changing the displayPic, and emits
    a "clicked" signal.'''

    clicked = QtCore.pyqtSignal()
    
    def __init__(self, session=None, default_pic=gui.theme.user, 
                 size=None, clickable=True, parent=None):
        '''constructor'''
        QtGui.QLabel.__init__(self, parent)
        self._session = session
        self._default_pic = default_pic
        if not size:
            # TODO: take this from options and subscribe
            self._size = QtCore.QSize(96, 96)
        self._clickable = clickable
        self._fader = PixmapFader(self.setPixmap, self._size,
                                  self._default_pic, self)
        
        self.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.setFrameStyle(QtGui.QFrame.StyledPanel)
        if clickable:
            self.setAttribute(Qt.WA_Hover)
            self.setFrameShadow(QtGui.QFrame.Plain)
        else:
            self.setFrameShadow(QtGui.QFrame.Sunken)
        self.setAlignment(Qt.AlignCenter)
        
        self.set_display_pic_from_file(default_pic)
        self.installEventFilter(self)
        
    def set_default_pic(self):
        '''Sets the default pic'''
        self.set_display_pic_from_file(self._default_pic)
    
    
    def set_display_pic_of_account(self, email=None):
        '''set a display pic from the account's name, the contact name, and pic
        name. If no contact is provided, the account's user's pic is set.
        If no pic is specified, then the last one is set'''
        if not self._session:
            raise RuntimeError('Trying to set display pic from account\'s'
                               'email, but no "session" provided') 
                               
        if not email:
            path = self._session.contacts.me.picture
        else:
            path = self._session.contacts.get(email).picture
        self.set_display_pic_from_file(path)

    def set_display_pic_from_file(self, path):
        ''' sets the display pic from the path'''
        pixmap = QtGui.QPixmap(path)
        if pixmap.isNull():
            return
        
        pixmap = gui.qt4ui.pixmap_rounder(pixmap)
        self._fader.add_pixmap(pixmap)
        

#    def set_clickable(self, clickable):
#        ''' enables or disables clicks '''
#        self._clickable = clickable
#
#    def is_clickable(self):
#        ''' returns true if the widget is clickable, False otherwise'''
#        return self._clickable
        
        
    # -------------------- QT_OVERRIDE

    # TODO: consider sublcassing a button at this point.... -_-;;
    def eventFilter(self, obj, event):
        ''' custom event filter '''
        # pylint: disable=C0103
        if not obj == self:
            return False
        if not self._clickable:
            return False
        elif event.type() == QtCore.QEvent.Enter:
            print "enter"
            self.setFrameShadow(QtGui.QFrame.Raised)
            return True
        elif event.type() == QtCore.QEvent.Leave:
            print "leave"
            self.setFrameShadow(QtGui.QFrame.Plain)
            return True
        elif event.type() == QtCore.QEvent.MouseButtonRelease and    \
             event.button() == Qt.LeftButton:
            self.setFrameShadow(QtGui.QFrame.Raised)
            self.clicked.emit()
            return True
        elif event.type() == QtCore.QEvent.MouseButtonPress and  \
             event.button() == Qt.LeftButton:
            self.setFrameShadow(QtGui.QFrame.Sunken)
            return True
        else:
            return False
            
    def sizeHint(self):
        '''Return an appropriate size hint'''
        # pylint: disable=C0103
        return QtCore.QSize(self._size.width()+10, self._size.height()+10)
        




class PixmapFader(QtCore.QObject):
    '''Class which provides a fading animation between QPixmaps'''
    def __init__(self, callback, pixmap_size, 
                 first_pic, parent=None):
        '''Constructor'''
        QtCore.QObject.__init__(self, parent)
        self._pixmaps = []
        self._size = pixmap_size
        self._rect = QtCore.QRect(QtCore.QPoint(0, 0), self._size)
        self._callback = callback
        # timer initialization
        self._timer = QtCore.QTimer(QtGui.QApplication.instance())
        self._timer.timeout.connect(self._on_timeout)
        self._fpms = 0.12 # frames / millisencond
        self._duration = 1000.0 # millisecond
        self._frame_time = 1 / self._fpms
        self._alpha_step = self._frame_time / self._duration
        # pixmap painting initializations
        self._result = QtGui.QPixmap(first_pic).scaled(self._size)
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
        
        
        
        


