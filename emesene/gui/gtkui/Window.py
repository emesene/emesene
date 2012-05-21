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
import glib

import os
import gui
import utils
import extension


class Window(gtk.Window):
    '''the class used to create all the windows of emesene'''

    NAME = 'Window'
    DESCRIPTION = 'The window used to contain all the content of emesene'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, cb_on_close, height=410, width=250,
                 posx=100, posy=100):
        gtk.Window.__init__(self)
        self.box = gtk.HPaned()
        # HACK! a bunch of properties/methods accessed by the outside
        self.box.add_accel_group = self.add_accel_group
        self.box.set_title = self.set_title
        self.box.set_icon = self.set_icon
        self.box.set_urgency_hint = self.set_urgency_hint
        self.box.present = self.present
        self.box.is_active = self.is_active
        self.box.get_dimensions = self.get_dimensions
        self.box.is_maximized = self.is_maximized

        self._content_main = None
        self._content_conv = None

        self.set_location(width, height, posx, posy)
        self.set_title("emesene")
        image_theme = gui.theme.image_theme
        try:
            gtk.window_set_default_icon_list(
                 utils.safe_gtk_image_load(image_theme.logo16).get_pixbuf(),
                 utils.safe_gtk_image_load(image_theme.logo32).get_pixbuf(),
                 utils.safe_gtk_image_load(image_theme.logo48).get_pixbuf(),
                 utils.safe_gtk_image_load(image_theme.logo96).get_pixbuf())
        except:
            gtk.window_set_default_icon(
                utils.safe_gtk_image_load(image_theme.logo).get_pixbuf())

        self.cb_on_close = cb_on_close
        self.cb_on_close_conv = cb_on_close
        self.cb_on_quit = cb_on_close

        self._state = 0
        self.accel_group = None

        self.add(self.box)
        self.connect('delete-event', self._on_delete_event)
        self.connect('window-state-event', self._on_window_state_event)

    def _get_content_main(self):
        '''content getter'''
        return self._content_main

    def _set_content_main(self, content_main):
        '''content setter'''
        if self._content_main:
            self.box.remove(self._content_main)
            if self.accel_group:
                self.remove_accel_group(self.accel_group)
                self.accel_group = None
            self._content_main.destroy()
            del self._content_main
        self._content_main = content_main
        self.box.pack1(self._content_main)

    content_main = property(_get_content_main, _set_content_main)

    def _get_content_conv(self):
        '''content getter'''
        return self._content_conv

    def _set_content_conv(self, content_conv):
        '''content setter'''
        w = self.box.get_position()
        if self._content_conv:
            self.box.remove(self._content_conv)
            if self.accel_group:
                self.remove_accel_group(self.accel_group)
                self.accel_group = None
            self._content_conv.destroy()
            del self._content_conv
        self._content_conv = content_conv
        if content_conv is not None:
            self.box.pack2(self._content_conv)
        else:
            self.resize(self.set_or_get_width(w),
                        self.set_or_get_height(0))

    content_conv = property(_get_content_conv, _set_content_conv)

    def set_icon(self, icon):
        '''set the icon of the window'''
        if utils.file_readable(icon):
            gtk.Window.set_icon(self,
                                utils.safe_gtk_image_load(icon).get_pixbuf())

    def go_login(self, callback, on_preferences_changed,
                 config=None, config_dir=None, config_path=None,
                 proxy=None, use_http=None, session_id=None,
                 cancel_clicked=False, no_autologin=False):
        '''draw the login window on the main window'''
        LoginWindow = extension.get_default('login window')

        self.content_main = LoginWindow(callback, on_preferences_changed,
            config, config_dir, config_path, proxy, use_http, session_id,
            cancel_clicked, no_autologin)
        self.content_main.show()

        self.content_main.check_autologin()

    def go_connect(self, callback, avatar_path, config):
        '''draw the window that handles logging in'''
        ConnectingWindow = extension.get_default('connecting window')

        self.content_main = ConnectingWindow(callback, avatar_path, config)
        self.content_main.show()

    def go_main(self, session, on_new_conversation, quit_on_close=False):
        '''change to the main window'''
        MainWindow = extension.get_default('main window')
        self.content_main = MainWindow(session, on_new_conversation)
        self.connect('key-press-event', self.content_main._on_key_press)
        self.content_main.show()
        self.content_main.set_accels()

        # hide the main window only when the user is connected
        if quit_on_close:
            self.cb_on_close = self.cb_on_quit
        else:
            self.cb_on_close = lambda *args: self.hide_on_delete()

    def on_disconnect(self, cb_on_close):
        '''called when the user is disconnected'''
        self.cb_on_close = cb_on_close

    def go_conversation(self, session, on_close_cb):
        '''change to a conversation window'''
        ConversationManager = extension.get_default('conversation window')
        self.content_conv = ConversationManager(session, self._on_last_tab_close)
        self.connect('focus-in-event', self.content_conv._on_focus)
        self.connect('key-press-event', self.content_conv._on_key_press)
        self.content_conv.show()
        self.content_conv.set_accels()

        self.cb_on_close_conv = on_close_cb

    def set_location(self, width=0, height=0, posx=None, posy=None, single_window=False):
        """place the window on the given coordinates
        """
        if single_window:
            w, h = self.get_size()
            def this_is_an_hax(*args):
                # Really, it is! And an ugly one!
                self.resize(self.set_or_get_width(width+w), 
                            self.set_or_get_height(height))
                self.box.set_position(w)
                return False
            glib.idle_add(this_is_an_hax)
        else:
            self.set_default_size(self.set_or_get_width(width),
                                  self.set_or_get_height(height))

            #if window isn't visible center on screen
            screen = self.get_screen()
            pwidth, pheight = screen.get_width(), screen.get_height()
            if posx > pwidth:
                posx = (pwidth - width) // 2
            if posy > pheight:
                posy = (pheight - height) // 2

            self.move(self.set_or_get_posx(posx), self.set_or_get_posy(posy))

    def set_or_get_height(self, height=0):
        self._height = height if height > 0 else self._height
        return self._height

    def set_or_get_width(self, width=0):
        self._width = width if width > 0 else self._width
        return self._width

    def set_or_get_posx(self, posx=None):
        self._posx = posx if posx != None and posx > -self._width else self._posx
        return self._posx

    def set_or_get_posy(self, posy=-1):
        self._posy = posy if posy != None and posy > -self._height else self._posy
        return self._posy

    def get_dimensions(self, conversation=False):
        """return width, height, posx, posy from the window
        """
        posx, posy = self.get_position()
        width, height = self.get_size()
        if conversation and self.content_main:
            width = width - self.box.get_position()
        elif not conversation and self.box.get_position():
            width = self.box.get_position()

        # when login window is minimized, posx and posy are -32000 on Windows
        if os.name == "nt":
            # make sure that the saved dimensions are visible
            if posx < (-width):
                posx = 0
            if posy < (-height):
                posy = 0

        return width, height, posx, posy

    def save_dimensions(self):
        '''save the window dimensions'''
        width, height, posx, posy = self.get_dimensions()

        self.set_or_get_width(width)
        self.set_or_get_height(height)
        self.set_or_get_posx(posx)
        self.set_or_get_posy(posy)

    def _on_delete_event(self, widget, event):
        '''call the cb_on_close callback, if the callback return True
        then dont close the window'''
        self.save_dimensions()
        if self.content_conv and not self.content_main:
            return self.cb_on_close_conv(self.content_conv)
        else:
            return self.cb_on_close()

    def _on_last_tab_close(self):
        '''do the action when the last tab is closed on a conversation window
        '''
        self.cb_on_close_conv(self.content_conv)
        self.content_conv = None
        if not self.content_main:
            self.hide()

    def hide(self):
        '''override the method to remember the position
        '''
        self.save_dimensions()
        gtk.Window.hide(self)

    def show(self):
        '''override the method to set the position
        '''
        gtk.Window.show(self)
        self.box.show()
        self.set_location()

    def present(self, b_single_window=False):
        '''override the method to set the position
        '''
        gtk.Window.present(self)
        if not b_single_window:
            self.set_location()

    def _on_window_state_event(self, window, state):
        '''callew when window state is changed
        '''
        self._state = state.new_window_state if state.new_window_state & gtk.gdk.WINDOW_STATE_WITHDRAWN == 0 else self._state

    def is_maximized(self):
        '''return True is window is maximized, False otherwise
        '''
        return self._state & gtk.gdk.WINDOW_STATE_MAXIMIZED == gtk.gdk.WINDOW_STATE_MAXIMIZED
