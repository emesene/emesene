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
import Signal

class Accel(object):
    '''an abstract class representing an accel (for example Ctrl+Q)'''

    def __init__(self, key, ctrl=True, alt=False):
        '''class constructor'''
        self.key = key
        self.ctrl = ctrl
        self.alt = alt

class Image(object):
    '''an object that represents an image on a menu item'''

    TYPE_STOCK = 1
    TYPE_IMAGE = 2
    def __init__(self, value, type_=2):
        '''constructor'''
        self.value = value
        self.type = type_

class MenuOption(object):
    '''an object representing a menu item that has two states and
    can be toggled
    '''

    def __init__(self, label, active=False, accel=None):
        '''constructor'''
        self.label = label
        self._active = active
        self.accel = accel

        self.toggled = Signal.Signal()

    def build(self):
        '''build as a checkbox, you should implement
        this method for your toolkit'''
        raise NotImplementedError("Not implemented")

    def __get_active(self):
        '''return the value of active'''
        return self._active

    def __set_active(self, active):
        '''set the value of active, you must implement it on your toolkit
        to make it reflect the value on the widget'''
        self._set_active(active)

    active = property(__get_active, __set_active)

    def _set_active(self, active):
        '''set the value of active, you must implement it on your toolkit
        to make it reflect the value on the widget'''
        raise NotImplementedError("Not implemented")


class MenuItem(object):
    '''an object representing a menu item'''

    def __init__(self, label=None, image=None, accel=None):
        '''constructor'''
        self.label = label
        self.image = image
        self.accel = accel
        self._childs = []

        self.selected = Signal.Signal()

    def add_child(self, child):
        '''add a menu item as child'''
        self._childs.append(child)

    def remove_child(self, child):
        '''remove a child menu item'''
        self._childs.remove(child)

    def build(self):
        '''build as a menu item, you should implement this
        this method for your toolkit'''
        raise NotImplementedError("Not implemented")

    def build_as_popup(self):
        '''build as a popup, you should implement this
        this method for your toolkit'''
        raise NotImplementedError("Not implemented")

    def build_as_menu_bar(self):
        '''build as a menu bar, you should implement this
        this method for your toolkit'''
        raise NotImplementedError("Not implemented")

    def build_as_toolbar(self, **kwds):
        '''build as a toolbar, you should implement this
        this method for your toolkit'''
        raise NotImplementedError("Not implemented")

    def _build_as_toolbutton(self, tooltips=None):
        '''build this item as a toolbutton'''
        raise NotImplementedError("Not implemented")


class OptionGroup(MenuItem):
    '''a menu item that groups MenuOptions into a radio button group'''

    def __init__(self):
        '''constructor'''
        MenuItem.__init__(self)
        self.toggled = Signal.Signal()

    def build(self):
        '''build as a checkbox, you should implement
        this method for your toolkit'''
        raise NotImplementedError("Not implemented")

