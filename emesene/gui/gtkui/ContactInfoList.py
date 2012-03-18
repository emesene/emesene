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
import gtk
import gui
import extension
import utils
import Tooltips

import pango

class ContactInfoList(gtk.VBox):
    '''A widget that contains the display picture of the contact in single chat.
       If multi chat, it shows more information about contacts.
       It also contains our own display picture.'''

    NAME = 'Contact info list'
    DESCRIPTION = 'A panel to show contacts info as a list'
    AUTHOR = 'Ariel Juodziukynas (arielj)'
    WEBSITE = 'www.arieljuod.com.ar'

    def __init__(self, session, members):
        gtk.VBox.__init__(self)
        self.set_border_width(2)
        self.session = session

        #layout
        self._first = None
        self._last = None
        self._first_alig = gtk.Alignment(xalign=0.5, yalign=0.0, xscale=1.0,
            yscale=0.0)
        self._last_alig = None
        self._last_alig = gtk.Alignment(xalign=0.5, yalign=1.0, xscale=0.0,
            yscale=0.0)
        self.pack_start(self._first_alig)
        self.pack_end(self._last_alig)

        Avatar = extension.get_default('avatar')
        avatar_size = self.session.config.get_or_set('i_conv_avatar_size', 64)

        #our avatar
        self.avatarBox = gtk.EventBox()
        self.avatarBox.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        if self.session.session_has_service(e3.Session.SERVICE_PROFILE_PICTURE):
            self.avatarBox.connect('button-press-event', self._on_avatar_click)

        self.avatar = Avatar(cell_dimension=avatar_size)
        self.avatarBox.add(self.avatar)

        self.avatarBox.set_tooltip_text(_('Click here to set your avatar'))
        self.avatarBox.set_border_width(4)

        last_avatar = self.session.config.last_avatar
        if self.session.config_dir.file_readable(last_avatar):
            my_picture = last_avatar
        else:
            my_picture = gui.theme.image_theme.user

        self.last = self.avatarBox
        self.avatar.set_from_file(my_picture)

        #contact's avatar if single chat
        self.his_avatarBox = gtk.EventBox()
        self.his_avatarBox.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.his_avatarBox.connect('button-press-event', self._on_his_avatar_click)

        self.his_avatar = Avatar(cell_dimension=avatar_size)
        self.his_avatarBox.add(self.his_avatar)

        self.his_avatarBox.set_tooltip_text(_('Click to see informations'))
        self.his_avatarBox.set_border_width(4)

        #contacts list if multichat
        self._model = None
        self._contact_list = gtk.TreeView()
        self._contact_list.set_can_focus(False)
        avatar = gtk.CellRendererPixbuf()
        nick = extension.get_and_instantiate('nick renderer')
        status = gtk.CellRendererPixbuf()

        nick.set_property('ellipsize', pango.ELLIPSIZE_END)
        column = gtk.TreeViewColumn()
        column.set_expand(True)
        column.pack_start(avatar, False)
        column.pack_start(nick, True)
        column.pack_start(status, False)
        column.add_attribute(avatar, 'pixbuf', 0)
        column.add_attribute(nick, 'markup', 2)
        column.add_attribute(status, 'pixbuf', 3)
        self._contact_list.append_column(column)
        self.tooltips = Tooltips.Tooltips()
        self._contact_list.connect('motion-notify-event', self.tooltips.on_motion)
        self._contact_list.connect('leave-notify-event', self.tooltips.on_leave)

        if len(members) == 1:
            self.update_single(members)
        elif len(members) > 1:
            self.update_group(members)
        #else: can members by 0?

    def _set_first(self, first):
        '''set the first element and add it to the widget (remove the
        previous if not None'''
        if self._first is not None:
            self._first_alig.remove(self._first)
        self._first = first
        self._first_alig.add(self._first)
        self._first_alig.show_all()

    def _get_first(self):
        '''return the first widget'''
        return self._first

    first = property(fget=_get_first, fset=_set_first)

    def _set_last(self, last):
        '''set the last element and add it to the widget (remove the
        previous if not None'''
        if self._last is not None:
            self._last_alig.remove(self._last)
        self._last = last
        self._last_alig.add(self._last)
        self._last_alig.show_all()

    def _get_last(self):
        '''return the last widget'''
        return self._last

    last = property(fget=_get_last, fset=_set_last)

    def _on_avatar_click(self, widget, data):
        '''method called when user click on his avatar '''
        av_chooser = extension.get_default('avatar chooser')(self.session)
        av_chooser.set_modal(True)
        av_chooser.show()

    def _on_his_avatar_click(self, widget, data):
        '''method called when user click on the other avatar '''
        account = self.members[0]
        contact = self.session.contacts.get(account)
        if contact:
            dialog = extension.get_default('dialog')
            dialog.contact_information_dialog(self.session, contact.account)

    def _on_avatarsize_changed(self, value):
        '''callback called when config.i_conv_avatar_size changes'''
        self.avatarBox.remove(self.avatar)
        self.his_avatarBox.remove(self.his_avatar)

        self.avatar.set_property('dimension',value)
        self.his_avatar.set_property('dimension',value)

        self.avatarBox.add(self.avatar)
        self.his_avatarBox.add(self.his_avatar)

    def destroy(self):
        #stop the avatars animation... if any...
        self.avatar.stop()
        self.his_avatar.stop()

    def set_sensitive(self, is_sensitive):
        self.avatarBox.set_sensitive(is_sensitive)
        self.his_avatarBox.set_sensitive(is_sensitive)

    def update_single(self, members):
        ''' sets the avatar of our contact '''
        self.members = members
        account = members[0]
        contact = self.session.contacts.get(account)
        his_picture = gui.theme.image_theme.user
        if contact and contact.picture:
            his_picture = contact.picture
        self.his_avatar.set_from_file(his_picture)
        self._first_alig.set(0.5,0.0,1.0,0.0)
        self.set_size_request(-1,-1)
        self.first = self.his_avatarBox

    def update_group(self, members):
        ''' sets the contacts list instead of a contact's avatar '''
        self._contact_list.set_model(None)
        del self._model
        self._model = gtk.ListStore(gtk.gdk.Pixbuf, object, str, gtk.gdk.Pixbuf)
        self.members = members
        for member in self.members:
            contact = self.session.contacts.get(member)
            picture = contact.picture or gui.theme.image_theme.user
            contact_data = (utils.safe_gtk_pixbuf_load(picture,(15,15)),
              contact, contact.nick, utils.safe_gtk_pixbuf_load(
              gui.theme.image_theme.status_icons[contact.status],(15,15)))
            self._model.append(contact_data)
            self._contact_list.set_model(self._model)
        self._contact_list.show_all()
        self._first_alig.set(0.5,0.0,1.0,2.0)
        self.first = self._contact_list
        self.set_size_request(200,-1)
