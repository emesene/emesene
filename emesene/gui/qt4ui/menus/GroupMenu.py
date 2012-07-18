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

'''This module contains menu widgets' classes'''

import PyQt4.QtGui as QtGui

from gui.qt4ui.Utils import tr

import gui

ICON = QtGui.QIcon.fromTheme


class GroupMenu(QtGui.QMenu):
    '''A class that represents a menu to handle contact related information'''
    NAME = 'Group Menu'
    DESCRIPTION = 'The menu that displays all the group options'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''

    def __init__(self, handler, parent=None):
        """
        constructor

        handler -- a e3common.Handler.GroupHandler
        """
        QtGui.QMenu.__init__(self, tr('Group'), parent)
        self._handler = handler

        self.add = QtGui.QAction(ICON('list-add'), tr('Add'), self)
        self.remove = QtGui.QAction(ICON('list-remove'), tr('Remove'), self)
        self.rename = QtGui.QAction(ICON('document-edit'), tr('Rename'), self)

        self.addAction(self.add)
        self.addAction(self.remove)
        self.addAction(self.rename)

        self.setIcon(QtGui.QIcon(gui.theme.image_theme.users))

        self.add.triggered.connect(
            lambda *args: self._handler.on_add_group_selected())
        self.remove.triggered.connect(
            lambda *args: self._handler.on_remove_group_selected())
        self.rename.triggered.connect(
            lambda *args: self._handler.on_rename_group_selected())

        self.set_favorite = QtGui.QAction(QtGui.QIcon(gui.theme.image_theme.favorite),
            tr('Set as favorite'), self)
        self.set_favorite.triggered.connect(
                              lambda *args: self.on_favorite_group_selected())

        self.unset_favorite = QtGui.QAction(ICON('list-remove'),
            tr('Unset as favorite'), self)
        self.unset_favorite.triggered.connect(
            lambda *args: self.on_unset_favorite_group_selected())

        self.addAction(self.set_favorite)
        self.addAction(self.unset_favorite)

        self.update_items()

    def update_items(self):
        if self._handler.contact_list.is_favorite_group_selected():
            self.show_unset_favorite_item()
        else:
            self.show_set_favorite_item()

    def on_favorite_group_selected(self):
        ''' handle favorite group selection '''
        if not self._handler.is_by_group_view():
            return
        self._handler.on_favorite_group_selected()

    def on_unset_favorite_group_selected(self):
        ''' handle unset group as favorite '''
        if not self._handler.is_by_group_view():
            return
        self._handler.on_unset_favorite_group_selected()

    def show_set_favorite_item(self):
        '''
        Called when the user right clicks on a non favorite group.
        It hides the unset option and shows the set option.
        '''
        self.unset_favorite.setVisible(False)
        self.set_favorite.setVisible(True)

    def show_unset_favorite_item(self):
        '''
        Called when the user right clicks on a favorite group.
        It hides the set option and shows the unset option.
        '''
        self.set_favorite.setVisible(False)
        self.unset_favorite.setVisible(True)
