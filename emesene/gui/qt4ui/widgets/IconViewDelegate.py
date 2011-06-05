# -*- coding: utf-8 -*-

'''This module contains the ItemViewDelegate class'''

from PyQt4      import QtCore
from PyQt4      import QtGui
from PyQt4.QtCore      import Qt

import gui


class IconViewDelegate (QtGui.QStyledItemDelegate):
    '''A Qt Delegate to paint an item of the display pic chooser list'''
    # _PICTURE_SIZE = defaultPictureSize
    _PICTURE_SIZE = 50.0
    # _MIN_PICTURE_MARGIN = defaultPicture(Outer)Margin
    _MIN_PICTURE_MARGIN = 3.0
    
    def __init__(self, parent=None):
        '''Constructor'''
        QtGui.QStyledItemDelegate.__init__(self, parent)
        self._pic_size = QtCore.QSizeF(96.0, 96.0)
        self._xy_pic_margin = QtCore.QPointF(5, 5)
        self._item_size = QtCore.QSize(106, 106)
        
# -------------------- QT_OVERRIDE
        
    def paint(self, painter, option, index):
        '''Paints the contact'''
        # pylint: disable=C0103
        model = index.model()
        painter.save()
        painter.translate(0, 0)
        # -> Configure the painter
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        # especially useful for scaled smileys.
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)  
        painter.setClipRect(option.rect)
        painter.setClipping(True)
        
        # -> Draw the skeleton of a ItemView widget: highlighting, selection...
        QtGui.QApplication.style().drawControl(QtGui.QStyle.CE_ItemViewItem, 
                                               option, painter, option.widget)
        # -> Start drawing the decoration:
        # create the picture
        picture_path = model.data(index, Qt.DisplayRole).toString()
        picture = QtGui.QPixmap(picture_path)
        if picture.isNull():
            picture = QtGui.QPixmap(gui.theme.get_image_theme().user)
        picture = picture.scaled(96, 96, transformMode=Qt.SmoothTransformation)
        # calculate the target position
        top_left_point = QtCore.QPointF(option.rect.topLeft())
        target_point = top_left_point + self._xy_pic_margin
        # draw the picture
        painter.drawPixmap(target_point, picture)

        # -> It's done!
        painter.restore()
        

    def sizeHint(self, option, index):
        '''Returns a size hint for the contact'''
        # pylint: disable=C0103
        return self._item_size
                              
