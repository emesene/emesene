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
from gui.Menu import *

accel_group = gtk.AccelGroup()

def build(element):
    '''build an element with the defined toolkit and return it'''
    if type(element) is Menu:
        return _build_menu(element)
    elif type(element) is Item:
        return _build_menuitem(element)
    elif type(element) is Option:
        return _build_option(element)
    elif type(element) is CheckBox:
        return _build_checkbox(element)

    raise ValueError('Not valid type', type(element), Menu)

def build_menu_bar(menu):
    '''build a menu with the form of a menu bar'''
    gtk_menubar = gtk.MenuBar()

    for child in menu:
        gtk_menubar.add(build(child))
    
    menu.signal_connect("enabled", _set_sensitive, gtk_menubar, True)
    menu.signal_connect("disabled", _set_sensitive, gtk_menubar, False)

    return gtk_menubar

def build_pop_up(menu, x=0, y=0):
    '''build a pop up menu, if positions are given and needed by the toolkit
    will be used to show the pop up on that position'''
    gtk_menu = gtk.Menu()

    for child in menu:
        item = build(child)
        item.show()
        gtk_menu.add(item)
    
    menu.signal_connect("enabled", _set_sensitive, gtk_menu, True)
    menu.signal_connect("disabled", _set_sensitive, gtk_menu, False)

    return gtk_menu

def _set_sensitive(item, widget, enabled):
    '''set sensitive on widget to enabled'''
    widget.set_sensitive(enabled)

def _build_menu(menu):
    '''build a gtk.Menu from a gui.Menu.Menu'''

    gtk_menu = gtk.Menu()
    gtk_menu_item = gtk.MenuItem(menu.text)
    gtk_menu_item.set_submenu(gtk_menu)

    for item in menu:
        if type(item) is Item:
            if item.text == '-':
                gtk_menu.add(gtk.SeparatorMenuItem())
            else:
                gtk_menu.add(_build_menuitem(item))
        elif type(item) is Option:
            for option in _build_option(item):
                gtk_menu.add(option)
        else:
            gtk_menu.add(build(item))

    menu.signal_connect("enabled", _set_sensitive, gtk_menu_item, True)
    menu.signal_connect("disabled", _set_sensitive, gtk_menu_item, False)
            
    return gtk_menu_item

def _build_option(option):
    '''build an option object, return a list of gtk.RadioMenuItems'''
    option_list = []
    gtk_option = gtk.RadioMenuItem(None, option[0].text)

    if option.selected_index <= 0 or option.selected_index >= len(option):
        gtk_option.set_active(True)

    gtk_option.connect('activate', _option_cb, option[0], option)
    option_list.append(gtk_option)

    for (count, opt) in enumerate(option[1:]):
        gtk_opt = gtk.RadioMenuItem(gtk_option, opt.text)
        option.signal_connect("enabled", _set_sensitive, gtk_opt, True)
        option.signal_connect("disabled", _set_sensitive, gtk_opt, False)

        if option.selected_index == count + 1:
            gtk_opt.set_active(True)

        gtk_opt.connect('activate', _option_cb, opt, option)
        option_list.append(gtk_opt)
    
    option.signal_connect("enabled", _set_sensitive, gtk_option, True)
    option.signal_connect("disabled", _set_sensitive, gtk_option, False)

    return option_list

def _build_checkbox(checkbox):
    '''build a checkbox and return it'''
    gtk_checkbox = gtk.CheckMenuItem(checkbox.text)
    gtk_checkbox.set_active(checkbox.toggled)
    gtk_checkbox.connect('toggled', _checkbox_cb, checkbox)
    
    checkbox.signal_connect("enabled", _set_sensitive, gtk_checkbox, True)
    checkbox.signal_connect("disabled", _set_sensitive, gtk_checkbox, False)

    return gtk_checkbox

def _build_menuitem(menuitem):
    '''build a menu item from a gui.Menu.Item'''
    gtk_menuitem = gtk.ImageMenuItem(menuitem.text) 

    if menuitem.is_stock():
        image = gtk.image_new_from_stock(
            stock.map_stock(menuitem.image, gtk.STOCK_MISSING_IMAGE),
            gtk.ICON_SIZE_MENU)
        gtk_menuitem.set_image(image)
    elif menuitem.is_image_path():
        image = gtk.image_new_from_file(menuitem.get_image_path())
        gtk_menuitem.set_image(image)

    if menuitem.accel:
        special_keys = 0

        if menuitem.accel.ctrl:
            special_keys = special_keys | gtk.gdk.CONTROL_MASK
        if menuitem.accel.alt:
            special_keys = special_keys | gtk.gdk.MOD1_MASK

        gtk_menuitem.add_accelerator('activate', accel_group, 
            ord(menuitem.accel.key), special_keys, gtk.ACCEL_VISIBLE)

    gtk_menuitem.connect('activate', _menu_item_cb, menuitem)

    menuitem.signal_connect("enabled", _set_sensitive, 
        gtk_menuitem, True)
    menuitem.signal_connect("disabled", _set_sensitive, 
        gtk_menuitem, False)

    return gtk_menuitem

def _menu_item_cb(gtk_mitem, mitem):
    '''callback called when a Item is selected, emit the selected signal
    on Item'''
    mitem.signal_emit('selected')

def _option_cb(gtk_option, option, options):
    '''callback selected when an option is toggled'''
    option.toggled = gtk_option.get_active()
    option.signal_emit('toggled', option.toggled)

def _checkbox_cb(gtk_checkbox, checkbox):
    '''callback called when the checbox is toggled'''
    checkbox.toggled = gtk_checkbox.get_active()
    checkbox.signal_emit('toggled', checkbox.toggled)

def test():
    '''test the implementation'''
    import dialog
    import gui.MainMenu as MainMenu

    def quit_cb(item):
        '''method called when the quit item is selected'''
        gtk.main_quit()

    def status_cb(item, stat):
        '''method called when a status is selected'''
        print 'status', status.STATUS[stat], 'selected'

    window = gtk.Window()
    window.set_default_size(200, 200)
    window.connect('delete-event', gtk.main_quit)
    vbox = gtk.VBox()

    logged_in = True

    menu = MainMenu.MainMenu(dialog, None, None, None)
    vbox.pack_start(build_menu_bar(menu), False)
    vbox.pack_start(gtk.Label('test'), True, True)
    vbox.pack_start(gtk.Statusbar(), False)
    window.add(vbox)
    window.show_all()
    menu.status_item.enabled = False
    menu.order_option.enabled = False
    menu.quit_item.enabled = False
    menu.help_menu.enabled = False
    menu.show_by_nick_option.enabled = False
    gtk.main()

if __name__ == '__main__':
    test()
