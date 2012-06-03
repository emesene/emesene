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
import glib
from gui.gtkui import check_gtk3

class ContactInfoRotate(gtk.VBox):
    '''a widget that contains the display pictures of the contacts and our
    own display picture'''
    NAME = 'Contact info rotate'
    DESCRIPTION = 'The panel to show contact display pictures'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, session, members):
        gtk.VBox.__init__(self)
        self.set_border_width(2)
        self.session = session
        self.members = members

        self._first = None
        self._last = None
        self._first_alig = gtk.Alignment(xalign=0.5, yalign=0.0, xscale=1.0,
            yscale=0.0)
        self._last_alig = None
        self._last_alig = gtk.Alignment(xalign=0.5, yalign=1.0, xscale=1.0,
            yscale=0.0)
        
        self.pack_start(self._first_alig)
        self.pack_end(self._last_alig)

        Avatar = extension.get_default('avatar')

        avatar_size = self.session.config.get_or_set('i_conv_avatar_size', 64)

        self.avatarBox = gtk.EventBox()
        self.avatarBox.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        if self.session.session_has_service(e3.Session.SERVICE_PROFILE_PICTURE):
            self.avatarBox.connect('button-press-event', self._on_avatar_click)
            self.avatarBox.set_tooltip_text(_('Click here to set your avatar'))

        self.avatar = Avatar(cell_dimension=avatar_size)
        self.avatarBox.add(self.avatar)

        self.avatarBox.set_border_width(4)

        self.his_avatarBox = gtk.EventBox()
        self.his_avatarBox.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.his_avatarBox.connect('button-press-event', self._on_his_avatar_click)

        self.his_avatar = Avatar(cell_dimension=avatar_size)
        self.his_avatarBox.add(self.his_avatar)

        self.his_avatarBox.set_tooltip_text(_('Click to see informations'))
        self.his_avatarBox.set_border_width(4)

        if check_gtk3():
            #In gtk3 eventbox renders background, so make it transparent
            prov = gtk.CssProvider()
            prov.load_from_data("* {\n"
                "background-color: transparent;\n"
                "}");

            context = self.his_avatarBox.get_style_context()
            context.add_provider(prov, 600) #GTK_STYLE_PROVIDER_PRIORITY_APPLICATION
            context.save()

            context = self.avatarBox.get_style_context()
            context.add_provider(prov, 600) #GTK_STYLE_PROVIDER_PRIORITY_APPLICATION
            context.save()

        my_picture = self.session.config.last_avatar

        # Obtains his picture and details.
        contact = self.session.contacts.safe_get(None)
        if members is not None:
            account = members[0]
            contact = self.session.contacts.safe_get(account)

        self.first = self.his_avatarBox
        self.his_avatar.set_from_file(contact.picture, contact.blocked)

        self.last = self.avatarBox
        self.avatar.set_from_file(my_picture)

        self.index = 0 # used for the rotate picture function
        self.timer = None

        if len(members) > 1:
            self.timer = glib.timeout_add_seconds(5, self.rotate_picture)

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
        av_chooser = extension.get_and_instantiate('avatar chooser',  self.session)
        av_chooser.set_modal(True)
        av_chooser.show()

    def _on_his_avatar_click(self, widget, data):
        '''method called when user click on the other avatar '''
        account = self.members[self.index - 1]
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


    def rotate_picture(self):
        '''change the account picture in a multichat
           conversation every 5 seconds'''
        contact = self.session.contacts.get(self.members[self.index])

        if contact is None:
            self.index = (self.index+1)%len(self.members)
            return True

        path = contact.picture
        if path != '':
            self.his_avatar.set_from_file(path, contact.blocked)

        self.index = (self.index+1)%len(self.members)
        return True


    def destroy(self):
        #stop the group chat image rotation timer, if it's started
        if self.timer is not None:
            glib.source_remove(self.timer)
            self.timer = None

        #stop the avatars animation... if any...
        self.avatar.stop()
        self.his_avatar.stop()

    def set_sensitive(self, is_sensitive):
        self.avatarBox.set_sensitive(is_sensitive)
        self.his_avatarBox.set_sensitive(is_sensitive)

    def update_single(self, members):
        self.members = members
        if len(members) == 1 and self.timer is not None:
            glib.source_remove(self.timer)
            self.timer = None

        account = members[0]
        contact = self.session.contacts.safe_get(account)
        if contact.picture:
            his_picture = contact.picture
            self.his_avatar.set_from_file(his_picture, contact.blocked)

    def update_group(self, members):
        self.members = members
        if len(members) > 1 and self.timer is None:
            self.timer = glib.timeout_add_seconds(5, self.rotate_picture)
