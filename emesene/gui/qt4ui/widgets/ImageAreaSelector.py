# -*- coding: utf-8 -*-

'''This module contains the ChatInput class'''

import os

import PyQt4.QtGui      as QtGui
import PyQt4.QtCore     as QtCore
from PyQt4.QtCore   import Qt

# Addition imports to improve developer's
# fingers life :)
from PyQt4.QtCore import QRect, QSize, QPoint

import e3
import gui


class ImageAreaSelector (QtGui.QWidget):
    
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
        
        self.adjust_size()
        self.setBackgroundRole(QtGui.QPalette.Dark)
        self.setMouseTracking(True)
        self.setCursor(Qt.CrossCursor)
        

    def mousePressEvent (self, event):
        mouse_pos = event.pos()
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
            resize_end = event.pos()
            sel_rect.setBottomRight(sel_rect.bottomRight() +
                                    (resize_end - self._resize_start))
            self._resize_start = resize_end
            self.update()
        elif self._drag_start is not None:
            drag_end = event.pos()
            sel_rect.translate(drag_end - self._drag_start)
            self._drag_start = drag_end
            self.update()
            
        # cursor shape:
        mouse_pos = event.pos()
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
        
    
    def paintEvent(self, event):
        QtGui.QWidget.paintEvent(self, event)
        self._painter.begin(self)
        self._painter.drawPixmap(self._image_origin, self._pixmap)
        if not self._selection_rect.isNull():
            # preparing the darkened frame:
            sel_rect = self._selection_rect.normalized()
            frame = QtGui.QPixmap(event.rect().size())
            frame.fill(QtGui.QColor(0, 0, 0, 127))
            frame_painter = QtGui.QPainter(frame)
            # erase the selected area from the frame:
            frame_painter.setCompositionMode(
                                QtGui.QPainter.CompositionMode_DestinationIn)
            frame_painter.fillRect(sel_rect, QtGui.QColor(0, 0, 0, 0))
            # draw selection border :
            frame_painter.setCompositionMode(
                                QtGui.QPainter.CompositionMode_SourceOver)
            frame_painter.setPen(self._hl_color1)
            frame_painter.drawRect(sel_rect)
            # draw the resize grip (if possible)
            if sel_rect.width() > 20 and sel_rect.height() > 20:
                handle_rect = QRect(sel_rect.bottomRight(), self._handle_size)
                frame_painter.fillRect(handle_rect, self._hl_color2)
                frame_painter.drawRect(handle_rect)
            frame_painter.end()
            # painting the darkened frame:
            self._painter.drawPixmap(0, 0, frame)
            
        self._painter.end()
        
        
    def resizeEvent(self, event):
        new_size = event.size()
        pix_size = self._pixmap.size()
        
        dx = (new_size.width()  - pix_size.width() ) /2
        dy = (new_size.height() - pix_size.height()) /2
        
        new_image_origin = QPoint(dx, dy)
        self._selection_rect.translate(new_image_origin - self._image_origin)
        self._image_origin = new_image_origin
        

        
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


    def rotate_right(self):
        self._pixmap = self._pixmap.transformed(QtGui.QTransform().rotate(-90))
        self.adjust_size()
        
    
    def adjust_size(self):
        pixmap = self._pixmap
        if pixmap.width() < 96 or pixmap.height() < 96:
            min_size = QSize(96, 96)
        else:
            min_size = pixmap.size()
            
        self.setMinimumSize(min_size)









