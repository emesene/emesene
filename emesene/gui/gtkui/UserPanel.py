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

import gtk
import e3
import gui

import TextField
import StatusButton

import extension

class UserPanel(gtk.VBox):
    '''a panel to display and manipulate the user information'''
    NAME = 'User Panel'
    DESCRIPTION = 'A widget to display/modify the account information on the main window'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, session):
        '''constructor'''
        gtk.VBox.__init__(self)

        self.session = session
        self.config_dir = session.config_dir
        self._enabled = True

        Avatar = extension.get_default('avatar')
        
        self.avatar = Avatar(cell_dimension=48)

        self.avatarBox = gtk.EventBox()
        self.avatarBox.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        if session.session_has_service(e3.Session.SERVICE_PROFILE_PICTURE):
            self.avatarBox.connect('button-press-event', self.on_avatar_click)
            self.avatarBox.set_tooltip_text(_('Click here to set your avatar'))
        self.avatarBox.add(self.avatar)
        self.avatarBox.set_border_width(4)

        self.avatar_path = self.config_dir.get_path("last_avatar")

        if not self.session.config_dir.file_readable(self.avatar_path):
            path = gui.theme.image_theme.user
        else:
            path = self.avatar_path
        self.avatar.set_from_file(path)

        self.nick = TextField.TextField(session.contacts.me.display_name, session.contacts.me.account, False)
        self.nick.set_tooltip_text(_('Click here to set your nick name'))
        self.status = StatusButton.StatusButton(session)
        self.status.set_tooltip_text(_('Click here to change your status'))
        self.status.set_status(session.contacts.me.status)
        self.search = gtk.ToggleButton()
        self.search.set_tooltip_text(_('Search (Ctrl+F)'))
        self.mail = gtk.Button(label="(0)")
        self.mail.set_tooltip_text(_('Click here to access your mail'))

        self.mail.get_settings().set_property( "gtk-button-images", True )

        self.mail.set_image(gtk.image_new_from_file(gui.theme.image_theme.mailbox))
        self.mail.set_relief(gtk.RELIEF_NONE)
        self.search.set_image(gtk.image_new_from_stock(gtk.STOCK_FIND,
            gtk.ICON_SIZE_MENU))
        self.search.set_relief(gtk.RELIEF_NONE)

        self.empty_message_text = _("Click here to set your message")
        self.message = TextField.TextField(session.contacts.me.message,
            '[I]' + self.empty_message_text + '[/I]',
            True)
        self.message.set_tooltip_text(self.empty_message_text)
        self.toolbar = gtk.HBox()

        hbox = gtk.HBox()
        hbox.set_border_width(1)
        hbox.pack_start(self.avatarBox, False)

        vbox = gtk.VBox()
        nick_hbox = gtk.HBox()
        nick_hbox.pack_start(self.nick, True, True)
        nick_hbox.pack_start(self.mail, False)
        nick_hbox.pack_start(self.search, False)

        # enable this code and you'll get a nice button which fires a signal        
        #def do_something_weird(item):
        #    from e3.base.Event import Event
        #    session.add_event(Event.EVENT_DISCONNECTED, 'Tested disconnection', 0)
        #test_btn=gtk.Button(label="(!)")
        #test_btn.connect('clicked', do_something_weird)
        #test_btn.show()
        #nick_hbox.pack_start(test_btn, False)
        self.userpanel_button = None

        vbox.pack_start(nick_hbox, False)
        self.message_hbox = gtk.HBox()
        self.message_hbox.pack_start(self.message, True, True)
        self.message_hbox.pack_start(self.status, False)
        vbox.pack_start(self.message_hbox, False)

        hbox.pack_start(vbox, True, True)

        self.pack_start(hbox, True, True)
        self.pack_start(self.toolbar, False)

        hbox.show()
        nick_hbox.show()
        self.message_hbox.show()
        vbox.show()

        self._add_subscriptions()

    def replace_userpanel_extension(self, main_window):
        #first remove current button
        if not self.userpanel_button is None:
            self.message_hbox.remove(self.userpanel_button)
            self.userpanel_button = None

        UserPanelButton = extension.get_default('userpanel button')
        if UserPanelButton is not None:
            #add new button
            self.userpanel_button = UserPanelButton(self, main_window)
            self.message_hbox.pack_start(self.userpanel_button, False)
            self.message_hbox.reorder_child(self.userpanel_button, 1)
            self.userpanel_button.show()

    def show(self):
        '''override show'''
        gtk.VBox.show(self)
        self.avatar.show()
        self.avatarBox.show()
        self.nick.show()
        self.message.show()
        if self.session.session_has_service(e3.Session.SERVICE_STATUS):
            self.status.show()
        else:
            self.status.hide()

        self.search.show()
        if self.userpanel_button:
            self.userpanel_button.show()
        self.mail.show()
        self.toolbar.show()

    def show_all(self):
        '''override show_all'''
        self.show()

    def _set_enabled(self, value):
        '''set the value of enabled and modify the widgets to reflect the status
        '''
        self.nick.enabled = value
        self.message.enabled = value
        self.status.set_sensitive(value)
        self.search.set_sensitive(value)
        if self.userpanel_button:
            self.userpanel_button.set_sensitive(value)
        self._enabled = value

    def _get_enabled(self):
        '''return the value of the enabled property
        '''
        return self._enabled

    enabled = property(fget=_get_enabled, fset=_set_enabled)

    def on_status_change_succeed(self, stat):
        '''callback called when the status has been changed successfully'''
        self.status.set_status(stat)

    def on_message_change_succeed(self, message):
        '''callback called when the message has been changed successfully'''
        if self.session.contacts.me.media is None or self.session.contacts.me.media is "":
            self.message.text = message
        else:
            self.message.text = '♫ ' + self.session.contacts.me.media

    def on_media_change_succeed(self, message):
        '''callback called when the message has been changed successfully'''
        if not message is None:
            self.message.text = message

    def on_contact_list_ready(self):
        '''callback called when the contact list is ready to be used'''
        self.enabled = True

    def on_picture_change_succeed(self, account, path):
        '''callback called when the picture of an account is changed'''
        # out account
        if account == self.session.account.account:
            self.avatar.set_from_file(path)

    def on_profile_update_succeed(self, nick, message):
        '''method called when information about our profile is obtained
        '''
        self.nick.text = nick
        if message is not '':
            self.message.text = message

    def on_avatar_click(self, widget, data):
        '''method called when user click on his avatar
        '''
        av_chooser = extension.get_and_instantiate('avatar chooser',  self.session)
        av_chooser.set_modal(True)
        av_chooser.show()

    def _add_subscriptions(self):
        '''subscribe all signals'''
        self.session.signals.message_change_succeed.subscribe(
            self.on_message_change_succeed)
        self.session.signals.media_change_succeed.subscribe(
            self.on_media_change_succeed)
        if self.session.session_has_service(e3.Session.SERVICE_STATUS):
            self.session.signals.status_change_succeed.subscribe(
                self.on_status_change_succeed)
        self.session.signals.contact_list_ready.subscribe(
            self.on_contact_list_ready)
        self.session.signals.picture_change_succeed.subscribe(
            self.on_picture_change_succeed)
        self.session.signals.profile_get_succeed.subscribe(
            self.on_profile_update_succeed)
        self.session.signals.profile_set_succeed.subscribe(
            self.on_profile_update_succeed)

    def remove_subscriptions(self):
        '''unsubscribe all signals'''
        self.session.signals.message_change_succeed.unsubscribe(
            self.on_message_change_succeed)
        self.session.signals.media_change_succeed.unsubscribe(
            self.on_media_change_succeed)
        if self.session.session_has_service(e3.Session.SERVICE_STATUS):
            self.session.signals.status_change_succeed.unsubscribe(
                self.on_status_change_succeed)
        self.session.signals.contact_list_ready.unsubscribe(
            self.on_contact_list_ready)
        self.session.signals.picture_change_succeed.unsubscribe(
            self.on_picture_change_succeed)
        self.session.signals.profile_get_succeed.unsubscribe(
            self.on_profile_update_succeed)
        self.session.signals.profile_set_succeed.unsubscribe(
            self.on_profile_update_succeed)
