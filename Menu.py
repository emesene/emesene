# -*- coding: utf-8 -*-

#   This file is part of emesene.
#
#    Emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
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
'''a gtk implementation of gui.Menu'''
import gtk

import stock
from gui.Menu import Accel
from gui.Menu import Image
from gui.Menu import MenuOption as BaseMenuOption
from gui.Menu import OptionGroup as BaseOptionGroup
from gui.Menu import MenuItem as BaseMenuItem

accel_group = gtk.AccelGroup()

class MenuOption(BaseMenuOption):
    '''an object representing a menu item that has two states and
    can be toggled
    '''

    def __init__(self, label, active=False, accel=None):
        '''constructor'''
        BaseMenuOption.__init__(self, label, active, accel)

    def build(self):
        '''build as a checkbox, you should implement
        this method for your toolkit'''
        self.gtk_item = gtk.CheckMenuItem(self.label)
        self.gtk_item.set_active(self.active)
        self.gtk_item.connect('toggled', self._toggled_cb)

        return self.gtk_item

    def _set_active(self, active):
        '''set the value of active, you must implement it on your toolkit
        to make it reflect the value on the widget
        WARNING! active changes the status of the item on the last widget that
        was built, not on all of them'''
        self._active = active

        if hasattr(self, 'gtk_item'):
            self.gtk_item.set_active(active)

        self.toggled.emit(active)

    def _toggled_cb(self, gtk_item):
        '''callback called when a Item is selected, emit the selected signal
        on Item'''
        self._active = gtk_item.get_active()
        self.toggled.emit(self.active)

class MenuItem(BaseMenuItem):
    '''an object representing a menu item'''

    def __init__(self, label=None, image=None, accel=None):
        '''constructor'''
        BaseMenuItem.__init__(self, label, image, accel)

    def build(self):
        '''build as a menu item, you should implement this
        this method for your toolkit'''
        if self.label == '-':
            return gtk.SeparatorMenuItem()

        gtk_menuitem = gtk.ImageMenuItem(self.label)

        if self.image is not None:
            if self.image.type == Image.TYPE_STOCK:
                image = gtk.image_new_from_stock(
                    stock.map_stock(self.image.value, gtk.STOCK_MISSING_IMAGE),
                        gtk.ICON_SIZE_MENU)
                gtk_menuitem.set_image(image)
            elif self.image.type == Image.TYPE_IMAGE:
                image = gtk.image_new_from_file(self.image.value)
                gtk_menuitem.set_image(image)

        if self.accel is not None:
            special_keys = 0

            if self.accel.ctrl:
                special_keys = special_keys | gtk.gdk.CONTROL_MASK
            if self.accel.alt:
                special_keys = special_keys | gtk.gdk.MOD1_MASK

            gtk_menuitem.add_accelerator('activate', accel_group,
                ord(self.accel.key), special_keys, gtk.ACCEL_VISIBLE)

        gtk_menuitem.connect('activate', self._activated_cb)

        if len(self._childs):
            gtk_menu = gtk.Menu()
            gtk_menuitem.set_submenu(gtk_menu)

            for child in self._childs:
                if type(child) == OptionGroup:
                    for option in child.build():
                        gtk_menu.add(option)
                else:
                    gtk_menu.add(child.build())

        return gtk_menuitem

    def build_as_popup(self):
        '''build as a popup, you should implement this
        this method for your toolkit'''
        gtk_menu = gtk.Menu()

        for child in self._childs:
            item = child.build()
            item.show()
            gtk_menu.add(item)
       
        return gtk_menu

    def build_as_menu_bar(self):
        '''build as a menu bar, you should implement this
        this method for your toolkit'''
        gtk_menubar = gtk.MenuBar()

        for child in self._childs:
            gtk_menubar.add(child.build())

        return gtk_menubar

    def build_as_toolbar(self, **kwds):
        '''build as a toolbar, you should implement this
        this method for your toolkit'''
        gtk_tb = gtk.Toolbar()

        if kwds.get('style', '') == 'only icons':
            gtk_tb.set_style(gtk.TOOLBAR_ICONS)

        tooltips = gtk.Tooltips()
        tooltips.enable()

        for child in self._childs:
            item = child._build_as_toolbutton(tooltips)
            item.show()
            gtk_tb.add(item)

        return gtk_tb

    def _build_as_toolbutton(self, tooltips=None):
        '''build this item as a toolbutton'''
        if len(self._childs):
            button = gtk.MenuToolButton(None, self.label.replace('_', ''))
        elif self.label == '-':
            return gtk.SeparatorToolItem()
        else:
            button = gtk.ToolButton()
        button.set_label(self.label.replace('_', ''))

        if self.image is not None:
            if self.image.type == Image.TYPE_STOCK:
                image = gtk.image_new_from_stock(
                    stock.map_stock(self.image.value, gtk.STOCK_MISSING_IMAGE),
                        gtk.ICON_SIZE_MENU)
                button.set_icon_widget(image)
            elif self.image.type == Image.TYPE_IMAGE:
                image = gtk.image_new_from_file(self.image.value)
                button.set_icon_widget(image)

        if self.accel is not None:
            special_keys = 0

            if self.accel.ctrl:
                special_keys = special_keys | gtk.gdk.CONTROL_MASK
            if self.accel.alt:
                special_keys = special_keys | gtk.gdk.MOD1_MASK

            button.add_accelerator('clicked', accel_group,
                ord(self.accel.key), special_keys, gtk.ACCEL_VISIBLE)

        button.connect('clicked', self._activated_cb)

        if tooltips:
            button.set_tooltip(tooltips, self.label)

        if len(self._childs):
            gtk_menu = gtk.Menu()
            button.set_menu(gtk_menu)

            for child in self._childs:
                if type(child) == OptionGroup:
                    for option in child.build():
                        option.show_all()
                        gtk_menu.add(option)
                else:
                    item = child.build()
                    item.show_all()
                    gtk_menu.add(item)

        return button

    def _activated_cb(self, gtk_item):
        '''callback called when a Item is selected, emit the selected signal
        on Item'''
        self.selected.emit()

class OptionGroup(BaseOptionGroup):
    '''a menu item that groups MenuOptions into a radio button group'''

    def __init__(self):
        '''constructor'''
        BaseOptionGroup.__init__(self)

    def build(self):
        '''build as a radio group, you should implement
        this method for your toolkit'''
        option_list = []
        gtk_option = gtk.RadioMenuItem(None, self._childs[0].label)
        self._childs[0].gtk_item = gtk_option

        gtk_option.connect('activate', self._option_cb, 0)
        gtk_option.set_active(True)
        option_list.append(gtk_option)

        for (count, opt) in enumerate(self._childs[1:]):
            gtk_opt = gtk.RadioMenuItem(gtk_option, opt.label)
            opt.gtk_item = gtk_opt

            if opt.active:
                gtk_opt.set_active(True)

            gtk_opt.connect('activate', self._option_cb, count + 1)
            option_list.append(gtk_opt)

        return option_list

    def _option_cb(self, gtk_item, count):
        option = self._childs[count]
        option._active = gtk_item.get_active()

        if option.active:
            self.toggled.emit(count)

        option.toggled.emit(option.active)

def __test():
    import gtk
    import sys
    import gui.components
    gui.components.Menu = sys.modules[__name__]
    components = gui.components.Components(None)

    window = gtk.Window()
    window.connect('delete-event', gtk.main_quit)
    vbox = gtk.VBox()
    window.add(vbox)
    vbox.pack_start(components.main_menu.build_as_menu_bar())
    vbox.pack_start(components.build_conversation_toolbar().build_as_toolbar(
        style='only icons'))
    window.show_all()
    gtk.main()

if __name__ == '__main__':
    __test()
