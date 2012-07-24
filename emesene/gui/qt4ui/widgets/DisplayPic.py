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

''' This module contains the DisplayPic class'''

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import Qt

import gui
import os

from gui.qt4ui import Utils
from gui.qt4ui import PictureHandler


class DisplayPic (QtGui.QLabel):
    ''' A DisplayPic widget. Supports changing the displayPic, and emits
    a "clicked" signal.'''
    NAME = 'MainPage'
    DESCRIPTION = 'The widget used to to display avatars, aka display pictures'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''

    clicked = QtCore.pyqtSignal()

    def __init__(self, session=None,
                 size=96, clickable=True, parent=None, crossfade=True):
        '''constructor'''
        QtGui.QLabel.__init__(self, parent)

        self._session = session
        if size:
            self._size = QtCore.QSize(size, size)
        else:
            self._size = QtCore.QSize(96, 96)

        self._clickable = clickable

        self.blocked = False
        self.crossfade = crossfade
        self._movie = None
        self._last = None
        self._fader = PixmapFader(self.setPixmap, self._size,
                                  gui.theme.image_theme.user_def_imagetool,
                                  self)

        self.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        if clickable:
            self.setAttribute(Qt.WA_Hover)
            self.setFrameShadow(QtGui.QFrame.Plain)
        else:
            self.setFrameShadow(QtGui.QFrame.Sunken)
        self.setAlignment(Qt.AlignCenter)

        self.set_from_file('')
        self.installEventFilter(self)

        self._fader.movie_fadein_complete.connect(
                                        lambda: self.setMovie(self._movie))

    def _on_cc_avatar_size(self, *args):
        self._size = QtCore.QSize(self._session.config.i_conv_avatar_size,
                                  self._session.config.i_conv_avatar_size)
        self._fader.set_size(self._size)
        self.set_from_file(self._last)

    def set_from_file(self, filename, blocked=False):
        self.filename = filename
        self.blocked = blocked
        if filename and not os.path.exists(filename):
            if self._size.width() > 32:
                # use big fallback image
                self.filename = gui.theme.image_theme.user_def_imagetool
            else:
                self.filename = gui.theme.image_theme.user
        pic_handler = PictureHandler.PictureHandler(self.filename)
        if pic_handler.can_handle():
            pixmap = QtGui.QPixmap(self.filename)
            if pixmap.isNull():
                pixmap = QtGui.QPixmap(gui.theme.image_theme.user)

            pixmap = Utils.pixmap_rounder(pixmap.scaled(self._size,
                                        transformMode=Qt.SmoothTransformation))
            if self.crossfade:
                self._fader.add_pixmap(pixmap)
            else:
                self.setPixmap(pixmap)
        else:
            self._movie = QtGui.QMovie(self.filename)
            self._movie.setScaledSize(self._size)
            if self.crossfade:
                self._fader.add_pixmap(self._movie)
            else:
                self.setMovie(self._movie)

        if self.blocked:
            #FIXME: implement
            pass
        self._last = self.filename

    # -------------------- QT_OVERRIDE

    # TODO: consider sublcassing a button at this point.... -_-;;
    def eventFilter(self, obj, event):
        ''' custom event filter '''
        if not obj == self:
            return False
        if not self._clickable:
            return False
        elif event.type() == QtCore.QEvent.Enter:
            self.setFrameShadow(QtGui.QFrame.Raised)
            return True
        elif event.type() == QtCore.QEvent.Leave:
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
        return QtCore.QSize(self._size.width() + 10, self._size.height() + 10)


class PixmapFader(QtCore.QObject):
    '''Class which provides a fading animation between QPixmaps'''

    movie_fadein_complete = QtCore.pyqtSignal()

    def __init__(self, callback, pixmap_size,
                 first_pic, parent=None):
        '''Constructor'''
        QtCore.QObject.__init__(self, parent)
        self._elements = []
        self._size = pixmap_size
        self._rect = QtCore.QRect(QtCore.QPoint(0, 0), self._size)
        self._callback = callback
        # timer initialization
        self._timer = QtCore.QTimer(QtGui.QApplication.instance())
        self._timer.timeout.connect(self._on_timeout)
        self._fpms = 0.12  # frames / millisencond
        self._duration = 1000.0  # millisecond
        self._frame_time = 1 / self._fpms
        self._alpha_step = self._frame_time / self._duration
        # pixmap painting initializations
        self._result = QtGui.QPixmap(first_pic).scaled(self._size,
                                       transformMode=Qt.SmoothTransformation)
        self._result.fill(Qt.transparent)
        self._painter = QtGui.QPainter(self._result)
        #self._painter.setRenderHints(QtGui.QPainter.SmoothPixmapTransform)

    def set_size(self, qsize):
        self._size = qsize
        self._rect = QtCore.QRect(QtCore.QPoint(0, 0), self._size)
        self._result = self._result.scaled(self._size,
                                       transformMode=Qt.SmoothTransformation)

    def __del__(self):
        '''Destructor. Note: without this explicit destructor, we get a SIGABRT
        due to a failed assertion in xcb.'''
        self._painter.end()

    def add_pixmap(self, element):
        '''Adds a pixmap to the pixmap stack'''

        if isinstance(element, QtGui.QMovie):
            movie = element
            movie.setScaledSize(self._size)
            movie.start()
            pixmap = movie.currentPixmap()
        else:
            pixmap = element

        if pixmap.isNull():
            return

        mumber_of_elements = len(self._elements)
        # no pixmap yet:
        if mumber_of_elements == 0:
            self._painter.save()
            self._elements.append((element, 1))
            self._painter.drawPixmap(self._rect, pixmap, self._rect)
            self._painter.restore()
            self._callback(self._result)
            return

        # the pixmap is the same as the last one:
        if isinstance(self._elements[-1][0], QtGui.QPixmap) and \
           pixmap.toImage() == self._elements[-1][0].toImage():
            return

        # we have already one pixmap:
        if mumber_of_elements == 1:
            self._elements.append((element, 0))
            self._timer.start(self._frame_time)
            return

        # we have already two pixmap:
        if mumber_of_elements == 2:
            self._elements[0] = (self._result, 1)
            self._elements[1] = (element, 0)
            self._timer.start(self._frame_time)

        # ops...
        if mumber_of_elements > 2:
            raise RuntimeError('[BUG] Too many pixmaps!')

    def _on_timeout(self):
        '''Compute a frame. This method is called by a QTimer
        various times per second.'''
        old_element, old_opacity = self._elements[0]
        new_element, new_opacity = self._elements[1]
        old_pixmap = old_element
        new_pixmap = new_element
        if isinstance(old_pixmap, QtGui.QMovie):
            old_pixmap = old_element.currentPixmap()
        if isinstance(new_pixmap, QtGui.QMovie):
            new_pixmap = new_element.currentPixmap()

        if old_opacity < 0 and new_opacity > 1:
            self._timer.stop()
            if isinstance(new_element, QtGui.QMovie):
                self.movie_fadein_complete.emit()
            self._elements.remove(self._elements[0])
            self._elements[0] = (new_pixmap, 1)
            return

        old_opacity -= self._alpha_step
        new_opacity += self._alpha_step

        self._elements[0] = (old_element, old_opacity)
        self._elements[1] = (new_element, new_opacity)

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
