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

import e3
import gui
import extension

import PyQt4.QtGui as QtGui
import PyQt4.QtCore as QtCore

class StatusButton(QtGui.QToolButton):
    '''a button that when clicked displays a popup that allows the user to
    select a status'''
    NAME = 'Status Button'
    DESCRIPTION = 'A button to select the status'
    AUTHOR = 'Jose Rostagno'
    WEBSITE = 'www.emesene.org'

    def __init__(self, session=None):
        QtGui.QToolButton.__init__(self, None)
        self.session = session
        # a cache of gtk.Images to not load the images everytime we change
        # our status
        self.cache_imgs = {}

        self.setAutoRaise(True)
        StatusMenu = extension.get_default('menu status')
        self.menu = StatusMenu(self.set_status)

        self.invertStatus = {}
        for stat in e3.status.STATUS:
            self.invertStatus[unicode(e3.status.STATUS[stat])] = stat

        if self.session:
            self.status = self.session.account.status
        else:
            self.status = e3.status.OFFLINE

        self.set_status(self.status)
        self.menu.triggered.connect(self.statusactionchange)

        self.setMenu(self.menu)
        # show status menu on button click
        self.clicked.connect(self.showMenu)

    def statusactionchange(self, action):
        status = self.invertStatus[str(action.text())]
        self.set_status(status)

    def set_status(self, stat):
        '''load an image representing a status and store it on cache'''
        current_status = -1
  
        if self.session:
            current_status = self.session.account.status

        if stat not in self.cache_imgs:
            qt_icon = QtGui.QIcon(\
                gui.theme.image_theme.status_icons[stat])
            self.cache_imgs[stat] = qt_icon
        else:
            qt_icon = self.cache_imgs[stat]

        self.setIcon(qt_icon)
        if stat not in e3.status.ALL or stat == current_status:
            return

        self.status = stat
        if self.session:
            self.session.set_status(stat)

