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
'''This module contains the ContactList class'''

import logging

from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4.QtCore import Qt

import e3
import gui
from gui.base import Plus
from gui.base import ContactList
from gui.base import MarkupParser

from gui.qt4ui import Utils
from gui.qt4ui.widgets.ContactListModel import Role
from gui.qt4ui.widgets.ContactListModel import ContactListModel


log = logging.getLogger('qt4ui.widgets.ContactListDelegate')


class ContactListDelegate (QtGui.QStyledItemDelegate):
    '''A Qt Delegate to paint an item of the contact list'''
    def __init__(self, contact_list, session):
        '''Constructor'''
        QtGui.QStyledItemDelegate.__init__(self, contact_list)

        self.session = session
        self.contact_list = contact_list

        #cached values to speed up rendering
        self._calculate_picture_size()
        self._MIN_PICTURE_MARGIN = 3.0

        self.session.config.subscribe(self._on_template_change, 'nick_template')
        self.session.config.subscribe(self._on_template_change, 'group_template')
        self.session.config.subscribe(self._on_avatar_size_change, 'i_avatar_size')

    def _on_template_change(self, *args):
        self.parent().repaint()

    def _generate_block_overlay(self):
        '''for small images uses small block pic but for big ones uses a scale version of 
            blocked_overlay_big'''
        if self._picture_size > 32:
            # use big fallback image
            blocked_overlay_path = gui.theme.image_theme.blocked_overlay_big
            blocked_pic = QtGui.QPixmap(blocked_overlay_path)

            #scale picture
            newdim = int(self._picture_size * 0.5)
            scaledsize = QtCore.QSize(newdim, newdim)
            self.blocked_pic = blocked_pic.scaled(scaledsize, Qt.KeepAspectRatio)
        else:
            self.blocked_pic = QtGui.QPixmap(gui.theme.image_theme.blocked_overlay)

    def _calculate_picture_size(self):
        '''calculate and cache some useful values to speed up rendering'''
        self._picture_size = self.session.config.get_or_set('i_avatar_size', 32)
        self._pic_sizef = QtCore.QSizeF(self._picture_size, self._picture_size)
        self._pic_size = QtCore.QSize(self._picture_size, self._picture_size)

        #recreate blocked overlay
        self._generate_block_overlay()

    def _on_avatar_size_change(self, *args):
        self._calculate_picture_size()
        self.parent().repaint()

    def plus_text_parse(self, item):
        '''parse plus in the contact list'''
        try:
            item = Plus.msnplus_parse(item)
        except Exception, error: # We really want to catch all exceptions
            log.exception("Text: '%s' made the parser go crazy, stripping. Error: %s" % (
                          item, error))
            try:
                item = Plus.msnplus_strip(item)
            except Exception, error: # We really want to catch all exceptions
                log.exception("Even stripping plus markup doesn't help. Error: %s" % error)
        return item

    def _build_display_role(self, index, is_group=False):
        '''Build a string to be used as item's display role'''
        model = index.model()
        data_role = model.data(index, Role.DataRole).toPyObject()

        if is_group:
            display_role = self.contact_list.format_group(data_role)
        else:
            display_role = self.contact_list.format_nick(data_role)

        text = self.plus_text_parse(display_role) if not is_group else display_role
        text = MarkupParser.replace_markup(text)
        if not is_group:
            text_list = MarkupParser.replace_emoticons(text)
            return text_list

        return [text]

    def _put_display_role(self, text_doc, text_list):
        '''Adds the data and sets the html in the QTextDocument'''
        text = ''
        for item in text_list:
            if type(item) == QtGui.QImage:
                text_doc.addResource(QtGui.QTextDocument.ImageResource,
                    QtCore.QUrl("mydata://%s" % item.cacheKey()), QtCore.QVariant(item))
                text += "<img src=\"mydata://%s\" />" % item.cacheKey()
            else:
                text += item

        text_doc.setHtml(text)

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
                                               option, painter, self.parent())
        status = model.data(index, Role.StatusRole).toPyObject()
        text_doc = QtGui.QTextDocument()

        origin = QtCore.QPointF(0.0, 0.0)

        if not index.parent().isValid():
            # -> Start drawing the text_doc:
            text_list = self._build_display_role(index, True)
            painter.translate( QtCore.QPointF(option.rect.topLeft()) )
            # create the text_doc
            self._put_display_role(text_doc, text_list)
            # draw the text_doc
            text_doc.drawContents(painter)
        else:
            top_left_point = QtCore.QPointF(option.rect.topLeft())
            # a little additional margin
            # TODO: try to do this for the highlighting too
            top_left_point.setX( top_left_point.x() + 5 )
            # -> Start drawing the decoration:
            # calc
            y_pic_margin = abs((option.rect.height() - self._picture_size)) / 2
            x_pic_margin = self._MIN_PICTURE_MARGIN
            xy_pic_margin = QtCore.QPointF(x_pic_margin, y_pic_margin)

            # create the picture
            picture_path = model.data(index, Role.DecorationRole).toString()
            picture = QtGui.QPixmap(picture_path)
            if picture.isNull():
                picture = QtGui.QPixmap(gui.theme.image_theme.user)
            else:
                picture = Utils.pixmap_rounder(picture)

            #FIXME: when we scale to big sizes status icon is lost by some reason
            #scale picture
            scaledpicture = picture.scaled(self._pic_size, transformMode=Qt.SmoothTransformation)

            # calculate the target position
            source = QtCore.QRectF( origin,
                                    QtCore.QSizeF(scaledpicture.size()))
            target = QtCore.QRectF( top_left_point + xy_pic_margin,
                                    self._pic_sizef)

            # draw the picture
            painter.drawPixmap(target, scaledpicture, source)

            # -> start drawing the 'blocked' emblem
            if model.data(index, Role.BlockedRole).toPyObject():
                source = QtCore.QRectF( origin,
                                        QtCore.QSizeF(self.blocked_pic.size()) )
                x_emblem_offset = self._picture_size - self.blocked_pic.size().width()
                y_emblem_offset = self._picture_size - self.blocked_pic.size().height()
                xy_emblem_offset = QtCore.QPointF(x_emblem_offset,
                                                  y_emblem_offset)
                target = QtCore.QRectF( top_left_point + xy_pic_margin +
                                                      xy_emblem_offset,
                                                  QtCore.QSizeF(self.blocked_pic.size()))
                painter.drawPixmap(target, self.blocked_pic, source)

            # -> set-up status picture for calculations
            picture_path  = gui.theme.image_theme.status_icons[
                            model.data(index, Role.StatusRole).toPyObject()]
            picture_status = QtGui.QPixmap(picture_path)

            # -> Start setting up the text_doc:
            text_list = self._build_display_role(index)
            # set the text into text_doc
            self._put_display_role(text_doc, text_list)
            # calculate the vertical offset, to center the text_doc vertically
            y_text_offset = \
                abs(option.rect.height() - text_doc.size().height()) / 2
            x_text_offset = 2 * x_pic_margin + self._picture_size
            xy_text_offset = QtCore.QPointF(x_text_offset, y_text_offset)

            # move the pointer to the text_doc zone:
            painter.translate(top_left_point + xy_text_offset)

            #calculate max text width = treeview width - status image width
            max_text_width = option.rect.width() - 3 * picture_status.size().width() - 2 * x_pic_margin

            #text width is the min between text_size and max_text_size
            x_size = min(max_text_width, text_doc.size().width())

            #calculate rect size
            target = QtCore.QRectF( origin,
                                    QtCore.QSizeF(x_size, text_doc.size().height()) )

            # draw the text_doc
            text_doc.drawContents(painter, target)

            # -> start drawing the status emblem
            source = QtCore.QRectF( origin,
                                    QtCore.QSizeF(picture_status.size()) )

            x_emblem_offset = max_text_width
            y_emblem_offset = abs((option.rect.height() - picture_status.size().height())) / 2
            xy_emblem_offset = QtCore.QPointF(max_text_width, y_emblem_offset)
            target = QtCore.QRectF( xy_emblem_offset,
                                    QtCore.QSizeF(picture_status.size()) )
            painter.drawPixmap(target, picture_status, source)

        # -> It's done!
        painter.restore()

    def sizeHint(self, option, index):
        '''Returns a size hint for the contact'''
        model = index.model()
        data_role = model.data(index, Role.DataRole).toPyObject()
        text_doc = QtGui.QTextDocument()
        text_list = self._build_display_role(index, isinstance(data_role, e3.base.Group))
        self._put_display_role(text_doc, text_list)
        text_height = text_doc.size().toSize().height()
        if isinstance(data_role, e3.base.Group):
            return QtCore.QSize(0, text_height)
        return QtCore.QSize(0, max(text_height, self._picture_size + 2 *self._MIN_PICTURE_MARGIN))

    def remove_subscriptions(self):
        self.session.config.unsubscribe(self._on_template_change, 'nick_template')
        self.session.config.unsubscribe(self._on_template_change, 'group_template')
        self.session.config.unsubscribe(self._on_avatar_size_change, 'i_avatar_size')
