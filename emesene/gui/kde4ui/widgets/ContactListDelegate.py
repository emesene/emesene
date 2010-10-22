# -*- coding: utf-8 -*-

'''This module contains the ContactList class'''

#from amsn2.ui.front_ends.kde4.adaptationLayer import KFELog
#
#from contactListModel   import KFERole
#
#from amsn2.ui.front_ends.kde4.adaptationLayer import KFEThemeManager

import PyKDE4.kdeui     as KdeGui
from PyKDE4.kdecore import i18n
import PyQt4.QtGui      as QtGui
import PyQt4.QtCore     as QtCore
from PyQt4.QtCore   import Qt

import e3
import gui

from ContactListModel import Role

class ContactListDelegate (QtGui.QStyledItemDelegate):
    '''A Qt Delegate to paint an item of the contact list'''
    # Consider implementing a caching mechanism, if it's worth
    # _PICTURE_SIZE = defaultPictureSize
    _PICTURE_SIZE = 50.0
    # _MIN_PICTURE_MARGIN = defaultPicture(Outer)Margin
    _MIN_PICTURE_MARGIN = 3.0
    
    def __init__(self, parent):
        '''Constructor'''
        QtGui.QStyledItemDelegate.__init__(self, parent)
        self._pic_size = QtCore.QSizeF(self._PICTURE_SIZE, self._PICTURE_SIZE)
        
# -------------------- QT_OVERRIDE
        
    def paint(self, painter, option, index):
        '''Paints the contact'''
        # pylint: disable=C0103
        model = index.model()
        painter.save()
        # -> Configure the painter
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        # especially useful for scaled smileys.
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)  
        painter.setClipRect(option.rect)
        painter.setClipping(True)
        # -> Draw the skeleton of a ItemView widget: highlighting, selection...
        QtGui.QApplication.style().drawControl(QtGui.QStyle.CE_ItemViewItem, 
                                               option, painter, option.widget)
        status = model.data(index, Role.StatusRole).toPyObject()
        text_doc = QtGui.QTextDocument()
        text = model.data(index, Role.DisplayRole).toString() #+ \
               #'<b>[' + e3.status.STATUS[status] + ']</b>'
        
        if not index.parent().isValid():
            # -> Start drawing the text_doc:
            text = "<b>"+text+"</b>"
            painter.translate( QtCore.QPointF(option.rect.topLeft()) )
            # create the text_doc
            text_doc.setHtml(text)
            # draw the text_doc
            text_doc.drawContents(painter)
            
        else:
            top_left_point = QtCore.QPointF(option.rect.topLeft())
            # -> Start drawing the decoration:
            # calc
            y_pic_margin = abs((option.rect.height() - self._PICTURE_SIZE)) / 2
            x_pic_margin = self._MIN_PICTURE_MARGIN
            xy_pic_margin = QtCore.QPointF(x_pic_margin, y_pic_margin)
            # create the picture
            picture_path = model.data(index, Role.DecorationRole).toString()
            picture = QtGui.QPixmap(picture_path)
            if picture.isNull():
                picture = QtGui.QPixmap(gui.theme.user)
            # calculate the target position
            source = QtCore.QRectF( QtCore.QPointF(0.0, 0.0), 
                                    QtCore.QSizeF(picture.size()) )
            target = QtCore.QRectF( top_left_point + xy_pic_margin, 
                                    self._pic_size )
            # draw the picture
            painter.drawPixmap(target, picture, source)
    
            # -> start drawing the emblem
            picture_path  = gui.theme.status_icons[
                            model.data(index, Role.StatusRole).toPyObject()]
            picture = QtGui.QPixmap(picture_path)
            source = QtCore.QRectF( QtCore.QPointF(0.0, 0.0), 
                                    QtCore.QSizeF(picture.size()) )
            x_emblem_offset = self._PICTURE_SIZE - picture.size().width()
            y_embmel_offset = self._PICTURE_SIZE - picture.size().height()
            xy_emblem_offset = QtCore.QPointF(x_emblem_offset, y_embmel_offset)
            target = QtCore.QRectF( top_left_point + xy_pic_margin + 
                                        xy_emblem_offset,
                                    QtCore.QSizeF(picture.size()) )
            painter.drawPixmap(target, picture, source)
        
            # -> Start setting up the text_doc:
            text = _format_contact_display_role(text)
            # set the text into text_doc
            text_doc.setHtml(text)
            # calculate the vertical offset, to center the text_doc vertically
            y_text_offset = \
                abs(option.rect.height() - text_doc.size().height()) / 2
            x_text_offset = 2 * x_pic_margin + self._PICTURE_SIZE
            xy_text_offset = QtCore.QPointF(x_text_offset, y_text_offset)
            # move the pointer to the text_doc zone:
            painter.translate(top_left_point + xy_text_offset)
            # draw the text_doc
            text_doc.drawContents(painter)

        # -> It's done!
        painter.restore()
        

    def sizeHint(self, option, index):
        '''Returns a size hint for the contact'''
        # pylint: disable=C0103
        text = index.model().data(index, Role.DisplayRole).toString()
        text_doc = QtGui.QTextDocument()
        if not index.parent().isValid():
            text = "<b>"+text+"</b>"
            text_doc.setHtml(text)
            text_size = text_doc.size().toSize()
            return text_size
        else:
            text = _format_contact_display_role(text)
            text_doc.setHtml(text)
            text_size = text_doc.size().toSize()
            text_width  = text_size.width()
            text_height = text_size.height()
            return QtCore.QSize( text_width,
                          max(text_height, 
                              self._PICTURE_SIZE + 2*self._MIN_PICTURE_MARGIN))
                          
def _format_contact_display_role(text):
    '''Formats correctly the html string which represents the contact's
    display role'''
    smiley_size = 16
    #if not text.contains('<i></i>'):
        #text.replace('<i>','<br><i>')
    text.replace('<img src', '<img width="%d" height="%d" src' % 
                 (smiley_size, smiley_size))
    return text
