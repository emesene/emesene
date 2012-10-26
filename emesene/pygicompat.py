'''PyGtk compat module'''
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

try:
    import gi
    gi.require_version('Gtk', '3.0')
    import gi.pygtkcompat
except (ImportError, ValueError) as ex:
    raise ImportError

import sys
from gi.repository import Gdk
from gi.repository import GdkPixbuf
from gi.repository import Gtk
from gi.repository import Pango

gi.pygtkcompat.enable()
gi.pygtkcompat.enable_gtk(version='3.0')

Pango.SCALE_SMALL = 0.8333333333333

if not Gdk.CONTROL_MASK == Gdk.ModifierType.CONTROL_MASK:
    #override control_mask due to bug in pygicompat
    Gdk.CONTROL_MASK = Gdk.ModifierType.CONTROL_MASK
    Gdk.SHIFT_MASK = Gdk.ModifierType.SHIFT_MASK

if not hasattr(Gdk, 'screen_width'):
    Gdk.screen_width = Gdk.Screen.width
    Gdk.screen_height = Gdk.Screen.height

    Gtk.AccelGroup.connect_group = Gtk.AccelGroup.connect
    Gtk.image_new_from_animation = Gtk.Image.new_from_animation
    Gtk.image_new_from_icon_set = Gtk.Image.new_from_icon_set
    Gtk.image_new_from_file = Gtk.Image.new_from_file

    Gtk.status_icon_position_menu = Gtk.StatusIcon.position_menu
    Gtk.StatusIcon.set_tooltip = Gtk.StatusIcon.set_tooltip_text
    Gtk.clipboard_get = Gtk.Clipboard.get

try:
    #newer pygobject versions has compat for indexed attrs
    GdkPixbuf.Pixbuf.get_formats()[0]['description']
    Gdk.pixbuf_get_formats = GdkPixbuf.Pixbuf.get_formats
except:
    orig_get_formats = GdkPixbuf.Pixbuf.get_formats
    def get_formats():
        formats = orig_get_formats()
        old_formats = []
        def make_dict(format_):
            temp = {}
            temp['description'] = format_.get_description()
            temp['name'] = format_.get_name()
            temp['mime_types'] = format_.get_mime_types()
            temp['extensions'] = format_.get_extensions()
            return temp
        for format_ in formats:
            old_formats.append(make_dict(format_))
        return old_formats
    Gdk.pixbuf_get_formats = get_formats

Gtk.SeparatorMenuItem = Gtk.SeparatorMenuItem.new

def new_with_model_and_entry(model, column):
    combo = Gtk.ComboBox.new_with_model_and_entry(model)
    combo.set_entry_text_column (0)
    return combo
Gtk.ComboBoxEntry = new_with_model_and_entry
Gtk.combo_box_new_text = Gtk.ComboBoxText

def get_active_text(self):
    if isinstance(self.get_children()[0], Gtk.CellView):
        iter_ = self.get_active_iter()
        if iter_ is None:
            return ""
        model = self.get_model()
        return model.get_value(iter_, 0)
    return self.get_children()[0].get_text()
Gtk.ComboBox.get_active_text = get_active_text

class PixbufAnimation(GdkPixbuf.PixbufAnimation):
    def __new__(self, filename):
        return GdkPixbuf.PixbufAnimation.new_from_file(filename)

    def save(self, filename, extension):
        GdkPixbuf.PixbufAnimation.savev(self, filename, extension, [],[])

Gdk.PixbufAnimation = PixbufAnimation

def save(self, filename, extension):
    GdkPixbuf.Pixbuf.savev(self, filename, extension, [], [])
Gdk.Pixbuf.save = save

class ImageMenuItem(Gtk.ImageMenuItem):
    def __new__(self, mnemonic=""):
        if mnemonic.startswith("gtk-"):
            return Gtk.ImageMenuItem.new_from_stock(mnemonic, None)
        item = Gtk.ImageMenuItem.new_with_mnemonic(mnemonic)
        item.set_use_underline(True)
        return item
Gtk.ImageMenuItem = ImageMenuItem

class CheckMenuItem(Gtk.CheckMenuItem):
    def __new__(self, mnemonic=""):
        item = Gtk.CheckMenuItem.new_with_mnemonic(mnemonic)
        item.set_use_underline(True)
        return item
Gtk.CheckMenuItem = CheckMenuItem

class MenuItem(Gtk.MenuItem):
    def __new__(self, mnemonic=""):
        item = Gtk.MenuItem.new_with_mnemonic(mnemonic)
        item.set_use_underline(True)
        return item
Gtk.MenuItem = MenuItem

def about_dialog_set_url_hook(hook):
    pass
def about_dialog_set_email_hook(hook):
    pass
Gtk.about_dialog_set_url_hook = about_dialog_set_url_hook
Gtk.about_dialog_set_email_hook = about_dialog_set_email_hook
Gtk.Expander = Gtk.Expander.new_with_mnemonic

class Frame(Gtk.Frame):
    def __new__(self, label=""):
        return Gtk.Frame.new(label)
Gtk.Frame = Frame

def set_tooltips(self, tooltips):
    pass
Gtk.Toolbar.set_tooltips = set_tooltips

class Colormap(object):
    def alloc_color(self, color):
        pass
def colormap_get_system():
    return Colormap()
Gdk.colormap_get_system = colormap_get_system

orig_append_page_menu = Gtk.Notebook.append_page_menu
def append_page_menu(self, widget, label, menu_label=None):
    return orig_append_page_menu(self, widget, label, menu_label)
Gtk.Notebook.append_page_menu = append_page_menu

orig_append_page = Gtk.Notebook.append_page
def append_page(self, widget, label=None):
    return orig_append_page(self, widget, label)
Gtk.Notebook.append_page = append_page

#XXX: this only work with
# treeViewColumn.set_attributes(cellText, text=1)
def set_attributes(self, cellText, text=0):
    self.add_attribute(cellText, 'text', text)
Gtk.TreeViewColumn.set_attributes = set_attributes
def set_blinking(self, blink):
    pass
Gtk.StatusIcon.set_blinking = set_blinking

class TreeView(Gtk.TreeView):
    @property
    def window(self):
        return Gtk.TreeView.get_parent_window(self)
Gtk.TreeView = TreeView

class EventBox(Gtk.EventBox):
    @property
    def window(self):
        return Gtk.EventBox.get_parent_window(self)
Gtk.EventBox = EventBox

orig_set_text = Gtk.Clipboard.set_text
def new_set_text(self, text, len=-1):
    orig_set_text(self, text, len)
Gtk.Clipboard.set_text = new_set_text

old_menu_popup = Gtk.Menu.popup
def new_menu_popup(self, parent_menu_shell, parent_menu_item, func, button, activate_time, data=None):
    old_menu_popup(self, parent_menu_shell, parent_menu_item, func, data, button, activate_time)
Gtk.Menu.popup = new_menu_popup
