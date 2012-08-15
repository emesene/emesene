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

'''This module contains the ChatInput class'''

import PyQt4.QtGui as QtGui
import PyQt4.QtCore as QtCore
from PyQt4.QtCore import Qt
from PyQt4.QtCore import QRect, QSize, QPoint

import logging
log = logging.getLogger('qt4ui.widgets.ImageAreaSelector')


class ImageAreaSelector (QtGui.QWidget):
    '''This widget provides means to visually crop a portion of
    an image by selecting it'''
     # pylint: disable=W0612
    NAME = 'ImageAreaSelector'
    DESCRIPTION = 'A widget used to select part of an image'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''
    # pylint: enable=W0612
    
    selection_changed = QtCore.pyqtSignal()
    
    def __init__(self, pixmap, parent=None):
        '''Constructor'''
        QtGui.QWidget.__init__(self, parent)
        self._pixmap = pixmap
        
        self._selection_rect = QRect() 
        self._image_origin = QPoint()
        self._resize_start = None
        self._drag_start = None
        self._handle_size = QSize(-10, -10)
        self._painter = QtGui.QPainter()
        self._hl_color1 = QtGui.QPalette().color(QtGui.QPalette.Highlight)
        self._hl_color2 = QtGui.QPalette().color(QtGui.QPalette.Highlight)
        self._hl_color2.setAlpha(150)
        self._zoom = 1.0
        
        self.adjust_minum_size()
        self.setBackgroundRole(QtGui.QPalette.Dark)
        self.setMouseTracking(True)
        self.setCursor(Qt.CrossCursor)
        
# -------------------- [BEGIN] QT_OVERRIDE

    def mousePressEvent (self, event):
        '''Overrides QWidget's mousePressEvent. Handles starting
        a new selection, starting a drag operation'''
        # pylint: disable=C0103
        mouse_pos = event.pos() / self._zoom
        sel_rect = self._selection_rect
        
        if not event.button() == Qt.LeftButton:
            return
        
        if (not sel_rect.isNull()) and sel_rect.contains(mouse_pos, True):
            handle_rect = QRect(sel_rect.bottomRight(), self._handle_size)
            if handle_rect.contains(mouse_pos):
                self._resize_start = mouse_pos
            else:
                self._drag_start = mouse_pos
        else:
            self._resize_start = mouse_pos
            sel_rect.setTopLeft    (mouse_pos)
            self._selection_rect.setSize(QSize(0, 0))
        

    
    def mouseMoveEvent (self, event):
        '''Overrides QWidget's mouseMoveEvent. Handles resizing
        and dragging operations on selection'''
        # pylint: disable=C0103
        sel_rect = self._selection_rect
        if self._resize_start:
            resize_end = event.pos() / self._zoom
            sel_rect.setBottomRight(sel_rect.bottomRight() +
                                    (resize_end - self._resize_start))
            self._resize_start = resize_end
            self.make_selection_square()
            self.update()
        elif self._drag_start is not None:
            drag_end = event.pos() / self._zoom
            sel_rect.translate(drag_end - self._drag_start)
            self._drag_start = drag_end
            self.update()
            
        # cursor shape:
        mouse_pos = event.pos() / self._zoom
        if (not sel_rect.isNull()) and sel_rect.contains(mouse_pos, True):
            handle_rect = QRect(sel_rect.bottomRight(), self._handle_size)
            if handle_rect.contains(mouse_pos):
                self.setCursor(Qt.SizeFDiagCursor)
            else:
                self.setCursor(Qt.OpenHandCursor)
                
        else:
            self.setCursor(Qt.CrossCursor)
        
            
    
    def mouseReleaseEvent (self, event):
        '''Overrides QWidget's mouseReleaseEvent. Handles ending a resizing or
        draggin operation on the selection'''
        # pylint: disable=C0103
        self._selection_rect = self._selection_rect.normalized()
        self._resize_start = None
        self._drag_start = None
        self.update()
        if not self._selection_rect.isNull():
            self.selection_changed.emit()
        
    
    def paintEvent(self, event):
        '''Overrides QWidtget's paintEvent.'''
        # pylint: disable=C0103
        QtGui.QWidget.paintEvent(self, event)
        self._painter.begin(self)
        pixmap_dest_rect = QRect(self._image_origin * self._zoom, 
                                 self._pixmap.size()*self._zoom)
        self._painter.drawPixmap(pixmap_dest_rect, self._pixmap)
        if not self._selection_rect.isNull():
            # preparing the darkened frame:
            sel_rect = self._selection_rect.normalized()
            frame = QtGui.QPixmap(event.rect().size())
            frame.fill(QtGui.QColor(0, 0, 0, 127))
            frame_painter = QtGui.QPainter(frame)
            # erase the selected area from the frame:
            frame_painter.setCompositionMode(
                                QtGui.QPainter.CompositionMode_DestinationIn)
            sel_rect_scaled = QRect(sel_rect.topLeft() * self._zoom,
                                    sel_rect.size() * self._zoom)
            frame_painter.fillRect(sel_rect_scaled, QtGui.QColor(0, 0, 0, 0))
            # draw selection border :
            frame_painter.setCompositionMode(
                                QtGui.QPainter.CompositionMode_SourceOver)
            frame_painter.setPen(self._hl_color1)
            frame_painter.drawRect(sel_rect_scaled)
            # draw the resize grip (if possible)
            if sel_rect_scaled.width() > 20 and sel_rect_scaled.height() > 20:
                handle_rect = QRect(sel_rect_scaled.bottomRight(), 
                                    self._handle_size)
                frame_painter.fillRect(handle_rect, self._hl_color2)
                frame_painter.drawRect(handle_rect)
            frame_painter.end()
            # painting the darkened frame:
            self._painter.drawPixmap(0, 0, frame)
            
        self._painter.end()
        
        
    def resizeEvent(self, event):
        '''Overrides QWidget's resizeEvent. Handles image centering.'''
        # pylint: disable=C0103
        self.adjust_image_origin()
        
# -------------------- [END] QT_OVERRIDE

    def adjust_image_origin(self):
        '''Recalculates the top left corner's image position, so the
        image is painted centered'''
        # pylint: disable=C0103
        new_size = self.size() / self._zoom
        pix_size = self._pixmap.size()
        
        dx = (new_size.width()  - pix_size.width() ) /2
        dy = (new_size.height() - pix_size.height()) /2
        
        new_image_origin = QPoint(dx, dy)
        self._selection_rect.translate(new_image_origin - self._image_origin)
        self._image_origin = new_image_origin
        log.info('image origin: %s' % new_image_origin)
        
    def select_unscaled(self):
        '''Selects, if possible, a 96 x 96 square centered around the original
        image. In this way the image won't be scaled but won't take up all the 
        96 x 96 area.'''
        # pylint: disable=C0103
        pix_size = self._pixmap.size()
        if pix_size.width() <= 96 and pix_size.height() <= 96:
            viewport_size = self.size()
            x =   (viewport_size.width () - 96) / 2
            y =   (viewport_size.height() - 96) / 2
            self._selection_rect.setTopLeft(QPoint(x, y))
            self._selection_rect.setSize(QSize(96, 96))
            self.update()
            self.selection_changed.emit()
            
            
    def select_all(self):
        '''Selects the whole image. Currently broken for images taller
        than wide.'''
        # TODO: make me work!
        self._selection_rect.setTopLeft(self._image_origin)
        self._selection_rect.setSize(self._pixmap.size())
        self.update()
        self.selection_changed.emit()
        
        
    def rotate_left(self):
        '''Rotates the image counterclockwise.'''
        self._pixmap = self._pixmap.transformed(QtGui.QTransform().rotate(-90))
        self.adjust_minum_size()
        self.adjust_image_origin()
        self.update()
        self.selection_changed.emit()


    def rotate_right(self):
        '''Rotates the image clockwise'''
        self._pixmap = self._pixmap.transformed(QtGui.QTransform().rotate(90))
        self.adjust_minum_size()
        self.adjust_image_origin()
        self.update()
        self.selection_changed.emit()
        
    
    def adjust_minum_size(self):
        '''Sets the new minimum size, calculated upon the image size
        and the _zoom factor.'''
        pixmap = self._pixmap
        if pixmap.width() < 96 or pixmap.height() < 96:
            min_size = QSize(96, 96)
        else:
            min_size = pixmap.size()
            
        self.setMinimumSize(min_size*self._zoom)


    def make_selection_square(self):
        '''Modify the selected area making it square'''
        wid = self._selection_rect.width ()
        self._selection_rect.setSize(QSize(wid, wid))
        
    
    def set_zoom(self, zoomlevel):
        '''Sets the specified zoomlevel'''
        self._zoom = zoomlevel
        self.adjust_minum_size()
        self.adjust_image_origin()
        self.update()
        self.selection_changed.emit()
        
        
    def fit_zoom(self):
        '''Chooses a zoomlevel that makes visible the entire image.
        Currently broken.'''
        widget_wid = self.size().width ()
        widget_hei = self.size().height()
        
        pixmap_wid = self._pixmap.width ()
        pixmap_hei = self._pixmap.height()
        
        self._zoom = (min(widget_wid, widget_hei) / 
                      min(pixmap_wid, pixmap_hei))
                      
        self.adjust_minum_size()
        self.adjust_image_origin()
        self.update()
        self.selection_changed.emit()
        
    def get_selected_pixmap(self):
        '''Returns the pixmap contained in the selection rect.
        Currently doesn't handle transparency correctly'''
        sel_rect_scaled = QRect(self._selection_rect.topLeft() * self._zoom,
                                self._selection_rect.size() * self._zoom)
        return QtGui.QPixmap.grabWidget(self, sel_rect_scaled)
