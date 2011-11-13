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
import pango
import gobject

import Renderers

class TextField(gtk.VBox):
    '''this class represent a widget that is a button and when clicked
    it shows a textfield until the text is set, then the button appears again'''

    __gsignals__ = {
        'text-changed': (gobject.SIGNAL_RUN_LAST, 
                gobject.TYPE_NONE, 
                (gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT))
        }

    def __init__(self, text, empty_text, allow_empty):
        '''class constructor, text is the text to show, empty_text is the
        text to display when no text is entered, allow_empty is a boolean
        that indicates if the user can enter an empty string'''
        gtk.VBox.__init__(self)

        self.entry = gtk.Entry()
        self.label = Renderers.SmileyLabel()
        #self.label.set_ellipsize(pango.ELLIPSIZE_END)
        self.button = gtk.Button()
        self.button.set_alignment(0.0, 0.5)
        self.button.set_relief(gtk.RELIEF_NONE)

        self._enabled = True
        self.dont_focus_out = False

        self._text = text
        self.empty_text = empty_text
        self.allow_empty = allow_empty

        self.pack_start(self.button, True, True)
        self.pack_start(self.entry, True, True)

        self.button.add(self.label)
        self.text = self._text or self.empty_text

        self.button.connect('clicked', self.on_button_clicked)
        self.entry.connect('activate', self.on_entry_activate)
        self.entry.connect('focus-out-event', self._on_focus_out)
        self.entry.connect('button-press-event', self._on_button_pressed)
        self.entry.connect('key-press-event', self._on_key_press)

    def on_button_clicked(self, button):
        '''method called when the button is clicked'''
        if (self.entry.get_text() == self.empty_text):
            self.entry.set_text("")
        self.button.hide()
        self.entry.show()
        self.entry.grab_focus()

    def on_entry_activate(self, entry):
        '''method called when the user press enter on the entry'''
        if not self.entry.get_text() and not self.allow_empty:
            self.entry.set_text(self.empty_text)
            self.entry.hide()
            self.button.show()

        new_text = self.entry.get_text()

        if new_text != self._text:
            old_text = self._text
            self.text = self.entry.get_text()
            self.emit('text-changed', old_text, self._text)

        self.entry.hide()
        self.button.show()

    def _on_button_pressed(self, widget, event):
        if event.button == 3:
            self.dont_focus_out = True

    def _on_focus_out(self, widget, event):
        '''called when the widget lost the focus'''
        if not self.dont_focus_out:
            self.on_entry_activate(self.entry)
        else:
            self.dont_focus_out = False

    def show(self):
        '''override show'''
        gtk.VBox.show(self)
        self.button.show()
        self.entry.hide()
        self.label.show()

    def show_all(self):
        '''override the show method to not show both widgets on a show_all
        call'''
        self.show()

    def _get_text(self):
        '''return the value of text'''
        return self._text

    def _set_text(self, value):
        '''set the value of text'''
        self._text = value
        self.label.set_markup(Renderers.msnplus_to_list(
            gobject.markup_escape_text(self._text or self.empty_text)))
        self.entry.set_text(self._text)

    text = property(fget=_get_text, fset=_set_text)

    def _set_enabled(self, value):
        '''set the value of enabled and modify the widgets to reflect the status
        '''
        self._enabled = value
        self.button.set_sensitive(value)

    def _get_enabled(self):
        '''return the value of the enabled property
        '''

        return self._enabled

    enabled = property(fget=_get_enabled, fset=_set_enabled)

    def _on_key_press(self, widget, event):
        ''' if escape key is pressed put old text in the entry and cancel edit
        '''
        if event.keyval == gtk.keysyms.Escape:
            self.entry.set_text(self._text)
            self.on_entry_activate(self.entry)
            return True
        return False

    def has_focus(self):
        return self.entry.is_focus()
