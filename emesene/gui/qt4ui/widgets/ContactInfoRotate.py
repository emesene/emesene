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
import extension

from PyQt4 import QtGui
from PyQt4 import QtCore
from gui.qt4ui.Utils import tr


class ContactInfoRotate(QtGui.QWidget):
    '''a widget that contains the display pictures of the contacts and our
    own display picture'''
    NAME = 'Contact info rotate'
    DESCRIPTION = 'The panel to show contact display pictures'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, session, members, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.session = session
        self.members = members

        lay = QtGui.QVBoxLayout()
        self.setLayout(lay)

        Avatar = extension.get_default('avatar')
        avatar_size = self.session.config.get_or_set('i_conv_avatar_size', 64)

        self.avatar = Avatar(self.session, size=avatar_size)
        if self.session.session_has_service(e3.Session.SERVICE_PROFILE_PICTURE):
            self.avatar.clicked.connect(self._on_avatar_click)
            self.avatar.setToolTip(tr('Click here to set your avatar'))

        self.his_avatar = Avatar(self.session, size=avatar_size)
        self.his_avatar.setToolTip(tr('Click to see informations'))
        self.avatar.clicked.connect(self._on_his_avatar_click)

        # Obtains his picture and details.
        contact = self.session.contacts.safe_get(None)
        if members is not None:
            account = members[0]
            contact = self.session.contacts.safe_get(account)

        self.his_avatar.set_from_file(contact.picture, contact.blocked)
        self.avatar.set_from_file(self.session.config.last_avatar)

        self.index = 0  # used for the rotate picture function
        self.timer = None

        if len(members) > 1:
            self.timer = QtCore.QTimer()
            self.timer.setSingleShot(False)
            self.timer.timeout.connect(self.rotate_picture)
            self.timer.start(5000)

        lay.setContentsMargins(1, 1, 1, 1)
        lay.addWidget(self.his_avatar)
        lay.addStretch()
        lay.addWidget(self.avatar)

    def _on_avatar_click(self):
        '''method called when user click on his avatar '''
        av_chooser = extension.get_and_instantiate('avatar chooser',
            self.session)
        av_chooser.exec_()

    def _on_his_avatar_click(self):
        '''method called when user click on the other avatar '''
        account = self.members[self.index - 1]
        contact = self.session.contacts.get(account)
        if contact:
            dialog = extension.get_default('dialog')
            dialog.contact_information_dialog(self.session, contact.account)

    def _on_avatarsize_changed(self, value):
        '''callback called when config.i_conv_avatar_size changes'''
        #FIXME: implement
        pass
#        self.avatarBox.remove(self.avatar)
#        self.his_avatarBox.remove(self.his_avatar)
#
#        self.avatar.set_property('dimension', value)
#        self.his_avatar.set_property('dimension', value)
#
#        self.avatarBox.add(self.avatar)
#        self.his_avatarBox.add(self.his_avatar)

    def rotate_picture(self):
        '''change the account picture in a multichat
           conversation every 5 seconds'''
        contact = self.session.contacts.get(self.members[self.index])

        if contact is None:
            self.index = (self.index + 1) % len(self.members)
            return True

        path = contact.picture
        if path != '':
            self.his_avatar.set_from_file(path, contact.blocked)

        self.index = (self.index + 1) % len(self.members)
        return True

    def destroy(self):
        #stop the group chat image rotation timer, if it's started
        if self.timer is not None:
            self.timer.stop()
            self.timer = None

        #stop the avatars animation... if any...
#FIXME:
#        self.avatar.stop()
#        self.his_avatar.stop()

    def set_sensitive(self, is_sensitive):
        self.avatar.setEnabled(is_sensitive)
        self.his_avatar.setEnabled(is_sensitive)

    def update_single(self, members):
        self.members = members
        if len(members) == 1 and self.timer is not None:
            self.timer.stop()
            self.timer = None

        account = members[0]
        contact = self.session.contacts.safe_get(account)
        if contact.picture:
            his_picture = contact.picture
            self.his_avatar.set_from_file(his_picture, contact.blocked)

    def update_group(self, members):
        self.members = members
        if len(members) > 1 and self.timer is None:
            self.timer = QtCore.QTimer()
            self.timer.setSingleShot(False)
            self.timer.timeout.connect(self.rotate_picture)
            self.timer.start(5000)
