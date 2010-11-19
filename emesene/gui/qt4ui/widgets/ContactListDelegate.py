# -*- coding: utf-8 -*-

'''This module contains the ContactList class'''

from PyQt4      import QtCore
from PyQt4      import QtGui

import gui

from gui.qt4ui import Utils
from gui.qt4ui.widgets.ContactListModel import Role
from gui.qt4ui.widgets.ContactListModel import ContactListModel


class ContactListDelegate (QtGui.QStyledItemDelegate):
    '''A Qt Delegate to paint an item of the contact list'''
    # Consider implementing a caching mechanism, if it's worth
    # _PICTURE_SIZE = defaultPictureSize
    _PICTURE_SIZE = 50.0
    # _MIN_PICTURE_MARGIN = defaultPicture(Outer)Margin
    _MIN_PICTURE_MARGIN = 3.0
    
    def __init__(self, session, parent):
        '''Constructor'''
        QtGui.QStyledItemDelegate.__init__(self, parent)
        
        self._config = session.config
        self._PICTURE_SIZE = self._config.get_or_set('i_avatar_size', 50)
        self._pic_size = QtCore.QSizeF(self._PICTURE_SIZE, self._PICTURE_SIZE)
        self._format_nick  = (lambda nick:  nick )
        
        self._config.subscribe(self._on_template_change, 
                              'nick_template')
        self._config.subscribe(self._on_template_change,
                               'group_template')
    
    
    def set_nick_formatter(self, func):
        self._format_nick = func
        self.parent().update()
        
    def _on_template_change(self, *args):
        print "template changed"
        self.parent().repaint()
    
    def _build_display_role(self, index, is_group=False):
        '''Build a string to be used as item's display role'''
        model = index.model()
        data_role = model.data(index, Role.DataRole).toPyObject()
        if is_group:
            name = model.data(index, Role.DisplayRole).toPyObject()
            online = model.data(index, Role.OnlCountRole).toPyObject()
            total = model.data(index, Role.TotalCountRole).toPyObject()
            display_role = self._config.group_template
            display_role = replace_markup(display_role)
            display_role = display_role.replace('[$NAME]', name)
            display_role = display_role.replace('[$ONLINE_COUNT]', str(online))
            display_role = display_role.replace('[$TOTAL_COUNT]', str(total))
        else:
            display_role = self._format_nick(data_role)
            display_role = _format_contact_display_role(display_role)
    #        message = model.data(index, Role.MessageRole).toString()
    #        if not message.isEmpty():
    #            display_role += u'<p style="-qt-paragraph-type:empty; ' \
    #                            u'margin-top:5px; margin-bottom:0px; '  \
    #                            u'margin-left:0px; margin-right:0px; '  \
    #                            u'-qt-block-indent:0; text-indent:0px;"></p>'
    #            message = u'<i>' + message + u'</i>'
    #            display_role += _format_contact_display_role(message)
            # display_role = _format_contact_display_role(display_role)
            #display_role += '</table>'
        return display_role
        
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
        status = model.data(index, Role.StatusRole).toPyObject()
        text_doc = QtGui.QTextDocument()
        
        if not index.parent().isValid():
            # -> Start drawing the text_doc:
            text = self._build_display_role(index, True)
            painter.translate( QtCore.QPointF(option.rect.topLeft()) )
            # create the text_doc
            text_doc.setHtml(text)
            # draw the text_doc
            text_doc.drawContents(painter)
            
        else:
            top_left_point = QtCore.QPointF(option.rect.topLeft())
            # a little additional margin
            # TODO: try to do this for the highlighting too
            top_left_point.setX( top_left_point.x() + 5 )
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
            else:
                picture = Utils.pixmap_rounder(picture)
            # calculate the target position
            source = QtCore.QRectF( QtCore.QPointF(0.0, 0.0), 
                                    QtCore.QSizeF(picture.size()) )
            target = QtCore.QRectF( top_left_point + xy_pic_margin, 
                                    self._pic_size )
            # draw the picture
            painter.drawPixmap(target, picture, source)
    
            # -> start drawing the status emblem
            picture_path  = gui.theme.status_icons[
                            model.data(index, Role.StatusRole).toPyObject()]
            picture = QtGui.QPixmap(picture_path)
            source = QtCore.QRectF( QtCore.QPointF(0.0, 0.0), 
                                    QtCore.QSizeF(picture.size()) )
            x_emblem_offset = self._PICTURE_SIZE - picture.size().width()
            y_emblem_offset = self._PICTURE_SIZE - picture.size().height()
            xy_emblem_offset = QtCore.QPointF(x_emblem_offset, y_emblem_offset)
            target = QtCore.QRectF( top_left_point + xy_pic_margin + 
                                        xy_emblem_offset,
                                    QtCore.QSizeF(picture.size()) )
            painter.drawPixmap(target, picture, source)
            
            # -> start drawing the 'blocked' emblem
            if model.data(index, Role.BlockedRole).toPyObject():
                picture_path = gui.theme.blocked_overlay
                picture = QtGui.QPixmap(picture_path)
                source = QtCore.QRectF( QtCore.QPointF(0.0, 0.0),
                                        QtCore.QSizeF(picture.size()) )
                x_emblem_offset = 0
                y_emblem_offset = self._PICTURE_SIZE - picture.size().height()
                xy_emblem_offset = QtCore.QPointF(x_emblem_offset, 
                                                  y_emblem_offset)
                target = QtCore.QRectF( top_left_point + xy_pic_margin + 
                                                      xy_emblem_offset,
                                                  QtCore.QSizeF(picture.size()))
                painter.drawPixmap(target, picture, source)
        
            # -> Start setting up the text_doc:
            #text = _build_display_role(index)
            text = self._build_display_role(index)
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
            text = self._build_display_role(index, is_group=True)
            text_doc.setHtml(text)
            text_size = text_doc.size().toSize()
            return text_size
        else:
            text = self._build_display_role(index)
            text_doc.setHtml(text)
            text_size = text_doc.size().toSize()
            text_width  = text_size.width()
            text_height = text_size.height()
            return QtCore.QSize( text_width,
                          max(text_height, 
                              self._PICTURE_SIZE + 2*self._MIN_PICTURE_MARGIN))
                              
                              
    
            
        
                          
def _format_contact_display_role(text):
    '''Formats correctly a string part of a display role. Parses emotes, and
    scales them.'''
    # TODO: calculate smiley size from text's size.
    smiley_size = 16
    #if not text.contains('<i></i>'):
        #text.replace('<i>','<br><i>')
    text = replace_markup(text)
    text = Utils.parse_emotes(unicode(text))
    text = text.replace('<img src', '<img width="%d" height="%d" src' % 
                 (smiley_size, smiley_size))
    return text
    
def replace_markup(markup):
    '''replace the tags defined in gui.base.ContactList'''
    markup = markup.replace("[$NL]", "<br />")

    markup = markup.replace("[$small]", "<small>")
    markup = markup.replace("[$/small]", "</small>")

    markup = markup.replace("[$b]", "<b>")
    markup = markup.replace("[$/b]", "</b>")

    markup = markup.replace("[$i]", "<i>")
    markup = markup.replace("[$/i]", "</i>")
    return markup
    
