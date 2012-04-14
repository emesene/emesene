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
        self.cb_on_quit = cb_on_close
        self._state = 0

        self.connect('delete-event', self._on_delete_event)
        self.connect('key-press-event', self._on_key_press)
        self.connect('window-state-event', self._on_window_state_event)
        self.content = None

        self.content_type = 'empty'

    def set_icon(self, icon):
        '''set the icon of the window'''
        if utils.file_readable(icon):
            gtk.Window.set_icon(self,
                                utils.safe_gtk_image_load(icon).get_pixbuf())

    def clear(self):
        '''remove the content from the main window'''
        if self.get_child():
            self.remove(self.get_child())
            self.content = None

    def go_login(self, callback, on_preferences_changed,
                 config=None, config_dir=None, config_path=None,
                 proxy=None, use_http=None, session_id=None, 
                 cancel_clicked=False, no_autologin=False):

        '''draw the login window on the main window'''

        LoginWindow = extension.get_default('login window')

        self.content = LoginWindow(callback, on_preferences_changed,
            config, config_dir, config_path, proxy, use_http, session_id,
            cancel_clicked, no_autologin)
        if self.get_child() is None:
            self.add(self.content)

        self.content.show()
        self.content_type = 'login'

    def go_connect(self, callback, avatar_path, config):
        '''draw the login window on the main window'''
        ConnectingWindow = extension.get_default('connecting window')

        self.content = ConnectingWindow(callback, avatar_path, config)
        self.add(self.content)
        self.content.show()
        self.content_type = 'connecting'

    def go_main(self, session, on_new_conversation, quit_on_close=False):
        '''change to the main window'''
        MainWindow = extension.get_default('main window')
        self.content = MainWindow(session, on_new_conversation)
        self.content.set_accels(self)
        self.add(self.content)
        self.content.show()
        self.content_type = 'main'

        # hide the main window only when the user is connected
        if quit_on_close:
            self.cb_on_close = self.cb_on_quit
        else:
            self.cb_on_close = lambda *args: self.hide_on_delete()

    def on_disconnect(self, cb_on_close):
        '''called when the user is disconnected'''
        self.cb_on_close = cb_on_close

    def go_conversation(self, session):
        '''change to a conversation window'''
        ConversationManager = extension.get_default('conversation window')
        self.content = ConversationManager(session, self._on_last_tab_close)
        self.add(self.content)
        self.connect('focus-in-event', self.content._on_focus)
        self.connect('key-press-event', self.content._on_key_press)
        self.content.show()
        self.content_type = 'conversation'
        self.content.set_accels()

    def set_location(self, width=0, height=0, posx=None, posy=None):
        """place the window on the given coordinates
        """
        self.set_default_size(self.set_or_get_width(width),
                              self.set_or_get_height(height))
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

    def get_dimensions(self):
        """return width, height, posx, posy from the window
        """
        posx, posy = self.get_position()
        width, height = self.get_size()
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
        return self.cb_on_close(self.content)

    def _on_key_press(self, widget, event):
        '''called when a key is pressed on the window'''
        if self.content_type == 'main':
            if event.keyval == gtk.keysyms.Escape:
                self._on_delete_event(None, None)
            else:
                self.content._on_key_press(widget, event)

    def _on_last_tab_close(self):
        '''do the action when the last tab is closed on a conversation window
        '''
        self.cb_on_close(self.content)
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
        self.set_location()

    def present(self):
        '''override the method to set the position
        '''
        gtk.Window.present(self)
        self.set_location()

    def _on_window_state_event(self, window, state):
        '''callew when window state is changed
        '''
        self._state = state.new_window_state if state.new_window_state & gtk.gdk.WINDOW_STATE_WITHDRAWN == 0 else self._state

    def is_maximized(self):
        '''return True is window is maximized, False otherwise
        '''
        return self._state & gtk.gdk.WINDOW_STATE_MAXIMIZED == gtk.gdk.WINDOW_STATE_MAXIMIZED
