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
'''an abstract class to define menus, and their content'''

import protocol.base.Object as Object

class Accel(object):
    '''an abstract class representing an accel (for example Ctrl+Q)'''

    def __init__(self, key, ctrl=True, alt=False):
        '''class constructor'''
        self.key = key
        self.ctrl = ctrl
        self.alt = alt

class Base(Object.Object):
    '''the base class for the other items'''

    def __init__(self):
        Object.Object.__init__(self)
        self._enabled = True
        
        # this signals are emitted when the
        # element is enabled or disabled, the
        # implementation should connect to this
        # signal and do the stuff to change the
        # state of the element
        self.signal_add("enabled", 0)
        self.signal_add("disabled", 0)

    def _set_enabled(self, value):
        '''set the value of enabled to "value"'''
        self._enabled = value
        if value:
            self.signal_emit("enabled")
        else:
            self.signal_emit("disabled")

    def _get_enabled(self):
        '''return the value of self.enabled'''
        return self._enabled

    enabled = property(fset=_set_enabled, fget=_get_enabled)

class Selectable(Base):
    '''a base class that contains a text and a image representing an
    optional image to show. image is a tuple where the first element is
    a constant identifying the second value, the constant are defined on this 
    class (TYPE_STOCK, TYPE_IMAGE_PATH etc.)
    This class can emit the selected signal'''

    TYPE_NONE = 0
    TYPE_STOCK = 1
    TYPE_IMAGE_PATH = 2

    def __init__(self, text, image_type=TYPE_NONE, image=None, accel=None):
        '''class constructor'''
        Base.__init__(self)
        
        self.text = text
        self.image_type = image_type
        self.image = image
        self.accel = accel

        self.signal_add('selected', 0)

    def is_image_path(self):
        '''return True if image content is TYPE_IMAGE_PATH'''
        return self.image_type == Selectable.TYPE_IMAGE_PATH

    def is_stock(self):
        '''return True if image content is TYPE_STOCK'''
        return self.image_type == Selectable.TYPE_STOCK

    def get_image_path(self):
        '''return the image_path value if it's an image_path or None'''
        if self.is_image_path():
            return self.image

        return None

    def get_stock(self):
        '''return the stock value if it's a stock or None'''
        if self.is_stock():
            return self.image

        return None

class Menu(list, Selectable):
    '''a class that represent a container that can contain items or other
    menus'''

    def __init__(self, text='', image=None):
        '''class constructor'''
        Selectable.__init__(self, text, image)

class Option(list, Base):
    '''a class that can represent an option that can be selected deselected
    a group of items in which only one can be selected at a time.
     You must append Items to this object'''

    def __init__(self, selected_index=0):
        '''class constructor'''
        Base.__init__(self)

        self.selected_index = selected_index

class Item(Selectable):
    '''a nice name to identify an element that represent a label of text and
    a stock image that can be selected and emit the selected signal'''

    def __init__(self, text, image_type=Selectable.TYPE_NONE, image=None,
        accel=None):
        '''class constructor'''
        Selectable.__init__(self, text, image_type, image, accel)

class Togglable(Base): # Togglable? WTF? :P
    '''a class that represent an item that has a label and can be toggled'''

    def __init__(self, text, toggled=False):
        '''class constructor'''
        Base.__init__(self)

        self.text = text
        self.toggled = toggled

        # the new value of the toggled attribute
        self.signal_add('toggled', 1)

class CheckBox(Togglable):
    '''a nice name to a Togglable that is represented as a checkbox'''

    def __init__(self, text, toggled=False):
        '''class constructor'''
        Togglable.__init__(self, text, toggled)

class Radio(Togglable):
    '''a nice name to a Togglable that is represented as a radio'''

    def __init__(self, text):
        '''class constructor'''
        Togglable.__init__(self, text, False)

def build(element):
    '''build an element with the defined toolkit and return it'''
    raise NotImplementedError

def build_menu_bar(menu):
    '''build a menu with the form of a menu bar'''
    raise NotImplementedError

def build_pop_up(menu, x=0, y=0):
    '''build a pop up menu, if positions are given and needed by the toolkit
    will be used to show the pop up on that position'''
    raise NotImplementedError


