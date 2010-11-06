# -*- coding: utf-8 -*-

'''This module contains the ChatInput class'''

import os
import math

import PyQt4.QtGui      as QtGui
import PyQt4.QtCore     as QtCore
from PyQt4.QtCore   import Qt

# Addition imports to improve developer's
# fingers life :)
from PyQt4.QtCore import QRect, QSize, QPoint

import e3
import gui


class ImageAreaSelector (QtGui.QWidget):
    
    selectionChanged = QtCore.pyqtSignal()
    
    def __init__(self, pixmap, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self._pixmap = pixmap
        
        self._selection_rect = QRect() 
        self._image_origin= QPoint()
        self._resize_start = None
        self._drag_start = None
        self._handle_size = QSize(-10, -10)
        self._painter = QtGui.QPainter()
        self._hl_color1 = QtGui.QPalette().color(QtGui.QPalette.Highlight)
        self._hl_color2 = QtGui.QPalette().color(QtGui.QPalette.Highlight)
        self._hl_color2.setAlpha(150)
        self._zoom = 2
        
        self.adjust_size()
        self.setBackgroundRole(QtGui.QPalette.Dark)
        self.setMouseTracking(True)
        self.setCursor(Qt.CrossCursor)
        

    def mousePressEvent (self, event):
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
        self._selection_rect = self._selection_rect.normalized()
        self._resize_start = None
        self._drag_start = None
        self.update()
        if not self._selection_rect.isNull():
            self.selectionChanged.emit()
        
    
    def paintEvent(self, event):
        QtGui.QWidget.paintEvent(self, event)
        self._painter.begin(self)
        pixmap_dest_rect = QRect(self._image_origin * self._zoom, 
                                 self._pixmap.size()*self._zoom)
        self._painter.drawPixmap(pixmap_dest_rect, self._pixmap)
        if not self._selection_rect.isNull():
            # preparing the darkened frame:
            sel_rect = self._selection_rect.normalized()
            frame = QtGui.QPixmap(event.rect().size()*self._zoom)
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
        new_size = event.size() / self._zoom
        pix_size = self._pixmap.size()
        
        dx = (new_size.width()  - pix_size.width() ) /2
        dy = (new_size.height() - pix_size.height()) /2
        
        new_image_origin = QPoint(dx, dy)
        self._selection_rect.translate(new_image_origin - self._image_origin)
        self._image_origin = new_image_origin
        print 'image origin: %s' % new_image_origin
        

        
    def select_unscaled(self):
        pix_size = self._pixmap.size()
        if pix_size.width() <= 96 and pix_size.height() <= 96:
            viewport_size = self.size()
            x =   (viewport_size.width () - 96) / 2
            y =   (viewport_size.height() - 96) / 2
            self._selection_rect.setTopLeft(QPoint(x, y))
            self._selection_rect.setSize(QSize(96, 96))
            self.update()
            
            
    def select_all(self):
        self._selection_rect.setTopLeft(self._image_origin)
        self._selection_rect.setSize(self._pixmap.size())
        self.update()
        
        
    def rotate_left(self):
        self._pixmap = self._pixmap.transformed(QtGui.QTransform().rotate(90))
        self.adjust_size()
        self.update()


    def rotate_right(self):
        self._pixmap = self._pixmap.transformed(QtGui.QTransform().rotate(-90))
        self.adjust_size()
        self.update()
        
    
    def adjust_size(self):
        pixmap = self._pixmap
        if pixmap.width() < 96 or pixmap.height() < 96:
            min_size = QSize(96, 96)
        else:
            min_size = pixmap.size()
            
        self.setMinimumSize(min_size*self._zoom)


    def make_selection_square(self):
        wid = self._selection_rect.width ()
        self._selection_rect.setSize(QSize(wid, wid))
        
    
    def set_zoom(self, zoomlevel):
        self._zoom = zoomlevel
        self.adjust_size()
        self.update()
        
        
    def fit_zoom(self):
        widget_wid = self.size().width ()
        widget_hei = self.size().height()
        
        pixmap_wid = self._pixmap.width ()
        pixmap_hei = self._pixmap.height()
        
        self._zoom = (min(widget_wid, widget_hei) / 
                      min(pixmap_wid, pixmap_hei))
                      
        self.adjust_size()
        self.update()
        
    def get_selected_pixmap(self):
        return self._pixmap.copy(self._selection_rect)
        
        
        







