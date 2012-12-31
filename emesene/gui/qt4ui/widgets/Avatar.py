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

''' This module contains the Avatar class'''

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import Qt

import gui
import os

from gui.qt4ui import Utils
from gui.qt4ui import PictureHandler


class Avatar (QtGui.QWidget):
    ''' A Avatar widget'''
    NAME = 'Avatar'
    DESCRIPTION = 'The widget used to to display avatars'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''

    clicked = QtCore.pyqtSignal()

    def __init__(self, session=None,
                 size=96, clickable=True, parent=None, crossfade=True):
        '''constructor'''
        QtGui.QWidget.__init__(self, parent)

        self._session = session
        self._size = QtCore.QSize(size, size)
        self._clickable = clickable

        self.blocked = False
        self.crossfade = crossfade

        self._rect = QtCore.QRect(QtCore.QPoint(0, 0), self._size)

        # timer initialization
        self._timer = QtCore.QTimer(QtGui.QApplication.instance())
        self._timer.timeout.connect(self._on_timeout)
        self._fpms = 0.12  # frames / millisencond
        self._duration = 1000.0  # millisecond
        self._frame_time = 1 / self._fpms
        self._alpha_step = self._frame_time / self._duration

        # pixmap painting initializations
        self._prepare_fallback_image()
        self._back = (self._fallback, 0, self._get_fallback_image())
        self._front = (self._fallback, 0, self._get_fallback_image())
        self._generate_block_overlay()
        self.set_from_file('')
        self.installEventFilter(self)

    def _get_fallback_image(self):
        if self._size.width() > 32:
            # use big fallback image
            filename = gui.theme.image_theme.user_def_imagetool
        else:
            filename = gui.theme.image_theme.user
        return filename

    def _prepare_fallback_image(self):
        fallback = self._get_fallback_image()
        self._fallback = QtGui.QPixmap(fallback).scaled(self._size,
                                       transformMode=Qt.SmoothTransformation)

    def _generate_block_overlay(self):
        '''for small images uses small block pic but for big ones uses a scale version of 
            blocked_overlay_big'''
        if self._size > 32:
            # use big fallback image
            blocked_overlay_path = gui.theme.image_theme.blocked_overlay_big
            blocked_pic = QtGui.QPixmap(blocked_overlay_path)

            #scale picture
            newdim = int(self._size.width() * 0.5)
            scaledsize = QtCore.QSize(newdim, newdim)
            self.blocked_pic = blocked_pic.scaled(scaledsize, Qt.KeepAspectRatio)
        else:
            self.blocked_pic = QtGui.QPixmap(gui.theme.image_theme.blocked_overlay)

    def set_from_file(self, filename, blocked=False):
        self.blocked = blocked
        pixmap = self._fallback

        if filename is not None and os.path.exists(filename):
            self.filename = filename

            pic_handler = PictureHandler.PictureHandler(self.filename)
            if pic_handler.can_handle():
                pixmap = QtGui.QPixmap(self.filename)
                if not pixmap.isNull():
                    pixmap = Utils.pixmap_rounder(pixmap.scaled(self._size,
                                            transformMode=Qt.SmoothTransformation))
            else:
                self._movie = QtGui.QMovie(self.filename)
                self._movie.setScaledSize(self._size)
                self._movie.start()
                pixmap = self._movie
        else:
            filename = self._get_fallback_image()
        self.add_pixmap(pixmap, filename)

    # -------------------- QT_OVERRIDE
    def eventFilter(self, obj, event):
        ''' custom event filter '''
        if not obj == self:
            return False
        if not self._clickable:
            return False
        elif event.type() == QtCore.QEvent.MouseButtonRelease and    \
             event.button() == Qt.LeftButton:
            self.clicked.emit()
            return True
        else:
            return False

    def sizeHint(self):
        '''Return an appropriate size hint'''
        return QtCore.QSize(self._size.width() + 10, self._size.height() + 10)

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawWidget(qp)
        qp.end()

    def drawWidget(self, painter):
        painter.save()
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)

        old_pixmap, old_opacity, old_filename = self._back
        new_pixmap, new_opacity, new_filename = self._front
        if isinstance(self._back[0], QtGui.QMovie):
            old_pixmap = old_pixmap.currentPixmap()
        if isinstance(self._front[0], QtGui.QMovie):
            new_pixmap = new_pixmap.currentPixmap()
            new_pixmap = Utils.pixmap_rounder(new_pixmap.scaled(self._size,
                            transformMode=Qt.SmoothTransformation))

        if not self.crossfade:
            painter.drawPixmap(self._rect, new_pixmap, self._rect)
        else:
            painter.fillRect(self._rect, Qt.transparent)
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_Source)
            #FIXME: old pixmap fading isn't working correctly
#            painter.setOpacity(old_opacity)
            painter.setOpacity(0)
            painter.drawPixmap(self._rect, old_pixmap, self._rect)
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
            painter.setOpacity(new_opacity)
            painter.drawPixmap(self._rect, new_pixmap, self._rect)

        if self.blocked:
            origin = QtCore.QPointF(0.0, 0.0)
            source = QtCore.QRectF(origin,
                                    QtCore.QSizeF(self.blocked_pic.size()) )
            x_emblem_offset = self._size.width() - self.blocked_pic.size().width()
            y_emblem_offset = self._size.height() - self.blocked_pic.size().height()
            xy_emblem_offset = QtCore.QPointF(x_emblem_offset,
                                                y_emblem_offset)
            target = QtCore.QRectF(origin + xy_emblem_offset,
                                QtCore.QSizeF(self.blocked_pic.size()))
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
            painter.drawPixmap(target, self.blocked_pic, source)

        painter.restore()

    def _on_timeout(self):
        '''Compute a frame. This method is called by a QTimer
        various times per second.'''
        old_element, old_opacity, old_filename = self._back
        new_element, new_opacity, new_filename = self._front
        old_pixmap = old_element
        new_pixmap = new_element

        if old_opacity < 0 and new_opacity > 1:
            if not isinstance(new_element, QtGui.QMovie):
                self._timer.stop()
                return

        old_opacity -= self._alpha_step
        new_opacity += self._alpha_step

        self._back = (old_element, old_opacity, old_filename)
        self._front = (new_element, new_opacity, new_filename)
        self.repaint()

    def add_pixmap(self, element, filename):
        '''Adds a pixmap to the pixmap stack'''
        self._back = (self._front[0], 1, self._front[2])
        self._front = (element, 0, filename)
        # always start timer for movies because we need to update the picture
        if self.crossfade or isinstance(element, QtGui.QMovie):
            self._timer.start(self._frame_time)
        self.repaint()

    def set_size(self, new_size):
        self._size = QtCore.QSize(new_size, new_size)
        self._rect = QtCore.QRect(QtCore.QPoint(0, 0), self._size)
        self._generate_block_overlay()
        self._prepare_fallback_image()
        self._back = (self._rescale_picture(self._back[0], self._back[2]), self._back[1], self._back[2])
        self._front = (self._rescale_picture(self._front[0], self._front[2]), self._front[1], self._front[2])


    def _rescale_picture(self, picture, filename):
        if isinstance(picture, QtGui.QMovie):
            return picture.setScaledSize(self._size)
        else:
            pixmap = QtGui.QPixmap(filename)
            if not pixmap.isNull():
                pixmap = Utils.pixmap_rounder(pixmap.scaled(self._size,
                                    transformMode=Qt.SmoothTransformation))
            return pixmap

    def stop(self):
        '''stop the animation'''
        self._timer.stop()
