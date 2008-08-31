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
'''a group of methods and callable classes to validate values, used on 
ConfigDialog to validate the inputs, but also can be used on other places'''

import os

def not_empty(value):
    '''return True if not empty'''
    if value:
        return True
    else:
        return False

def is_file(value):
    '''return True if is file'''
    return os.path.isfile(value)

def is_dir(value):
    '''return True if is directory'''
    return os.path.isdir(value)

def is_int(value):
    '''return True if is an int or can be converted to an int'''
    try:
        int(value)
        return True
    except ValueError:
        return False

def is_float(value):
    '''return True if is a float or can be converted to a float'''
    try:
        float(value)
        return True
    except ValueError:
        return False

def is_bool(value):
    '''return True if the value is or can be converted to a bool'''
    try:
        bool(value)
        return True
    except ValueError:
        return False

def path_exists(value):
    '''return True if path exists'''
    return os.path.exists(value)

def readable(value):
    '''return True if the file exists and is readable'''
    if is_file(value) and os.access(value, os.R_OK):
        return True

    return False

def writable(value):
    '''return True if the file exists and is writeable'''
    if is_file(value) and os.access(value, os.W_OK):
        return True

    return False

class Range(object):
    '''a callable class that return True if the value parameter is 
    whitin the range including the extremes'''

    def __init__(self, min_val, max_val):
        '''class constructor'''
        self.min_val = min_val
        self.max_val = max_val

    def __call__(self, value):
        '''check if value is whitin the range, includint the extremes'''
        if self.min_val <= value <= self.max_val:
            return True

        return False

class InItems(object):
    '''a callable class that return True if the value is in the list of items
    '''

    def __init__(self, items):
        '''class constructor'''
        self.items = items

    def __call__(self, value):
        '''check if value is in items'''
        return value in self.items

