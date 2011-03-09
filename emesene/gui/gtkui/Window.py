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

    def __init__(self, cb_on_close, height=410, width=250, posx=100, posy=100):
        gtk.Window.__init__(self)

        self.set_location(width, height, posx, posy)
        self.set_title("emesene")
        self.set_icon(gui.theme.logo)

        if cb_on_close is not None:
            self.cb_on_close = cb_on_close
        else: # we're the main window: close button only hides it
            self.cb_on_close = lambda *args: self.hide_on_delete()

        self.connect('delete-event', self._on_delete_event)
        self.connect('key-press-event', self._on_key_press)
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

    def go_login(self, callback,on_preferences_changed,
           config=None, config_dir=None, config_path=None,
           proxy=None, use_http=None, session_id=None, cancel_clicked=False,
           no_autologin=False):
        '''draw the login window on the main window'''

        LoginWindow = extension.get_default('login window')

        self.content = LoginWindow(callback, on_preferences_changed,
            config, config_dir, config_path, proxy, use_http, session_id,
            cancel_clicked, no_autologin)
        if self.get_child() == None:
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

    def go_main(self, session, on_new_conversation,
            on_close, on_disconnect):
        '''change to the main window'''
        MainWindow = extension.get_default('main window')
        self.content = MainWindow(session, on_new_conversation,
            on_close, on_disconnect)
        self.add(self.content)
        self.content.show()
        self.content_type = 'main'

    def go_conversation(self, session):
        '''change to a conversation window'''
        ConversationManager = extension.get_default('conversation window')
        self.content = ConversationManager(session, self._on_last_tab_close)
        self.add(self.content)
        self.connect('focus-in-event', self.content._on_focus)
        self.content.show()
        self.content_type = 'conversation'
        self.content._set_accels()

    def set_location(self, width=0, height=0, posx=None, posy=None):
        """place the window on the given coordinates
        """
        self.set_default_size(self.set_or_get_width(width), self.set_or_get_height(height))
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

    def _on_delete_event(self, widget, event):
        '''call the cb_on_close callback, if the callback return True
        then dont close the window'''
        width, height, posx, posy = self.get_dimensions()

        self.set_or_get_width(width)
        self.set_or_get_height(height)
        self.set_or_get_posx(posx)
        self.set_or_get_posy(posy)

        return self.cb_on_close(self.content)

    def _on_key_press(self, widget, event):
        '''called when a key is pressed on the window'''
        if self.content_type == 'main':
            self.content._on_key_press(widget, event)

    def _on_last_tab_close(self):
        '''do the action when the last tab is closed on a conversation window
        '''
        self.cb_on_close(self.content)
        self.hide()

    def hide(self):
        '''override the method to remember the position
        '''
        width, height, posx, posy = self.get_dimensions()
        self.set_or_get_width(width)
        self.set_or_get_height(height)
        self.set_or_get_posx(posx)
        self.set_or_get_posy(posy)
        gtk.Window.hide(self)

    def show(self):
        '''override the method to set the position
        '''
        gtk.Window.deiconify(self)
        gtk.Window.show(self)
        self.set_location()

