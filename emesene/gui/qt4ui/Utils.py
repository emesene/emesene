# -*- coding: utf-8 -*-

''' This module contains the utilities'''

import PyQt4.QtGui      as QtGui
import PyQt4.QtCore     as QtCore
from PyQt4.QtCore   import Qt



def pixmap_rounder(qpixmap, perc_radius=16.7):
    '''Return the given pixmap with corners 
    rounded by the given radius'''
    
    # create the clipping path:
    clip_path = QtGui.QPainterPath()
    clip_path.addRoundedRect( QtCore.QRectF( qpixmap.rect()), 
                              perc_radius, perc_radius, 
                              Qt.RelativeSize)
    
    # create the target pixmap, completerly tansparent
    rounded_pixmap = QtGui.QPixmap(qpixmap.size())
    rounded_pixmap.fill(Qt.transparent)
    
    # create the painter
    painter = QtGui.QPainter(rounded_pixmap)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
    
    # paints a black rounded rect. This will be the area where 
    # we will paint the original pixmap
    painter.fillPath(clip_path, Qt.black)
    
    # paints the original pixmap in the black area.
    painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
    rect = QtCore.QRect(QtCore.QPoint(0, 0), qpixmap.size())
    painter.drawPixmap(rect, qpixmap, rect)
    
    painter.end()
    return rounded_pixmap
