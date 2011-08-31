'''a module to handle themes collections'''
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

import os
import glob
import re

class ThemesManager(object):
    '''a class to handle adium themes
    '''

    def __init__(self, pattern):
        '''constructor'''

        # the paths to look for themes
        self.paths = []
        #If themes directory has a pattern in their name like ".AdiumMessageStyle"
        # in adium conversation themes
        self.extension = pattern
        self.pattern = re.compile(pattern, re.IGNORECASE)
        self.reg_pattern = "*" + pattern

    def add_themes_path(self, path):
        '''add a path to look for themes

        returns True if the path was added, False otherwise (the path doesn't
        exists or it isn't a directory)
        '''

        if path not in self.paths and os.path.isdir(path):
            self.paths.append(path)
            return True

        return False

    def list(self):
        '''return a list of all the available themes
        '''
        items = []

        for path in self.paths:
            items += glob.glob(os.path.join(path, self.reg_pattern))

        return items

    def get_name_from_path(self, path):
        '''return a name from a path as in list()
        '''
        name = os.path.basename(path)
        name = self.pattern.sub('', name)
        return name

    def get_name_list(self):
        '''return a list with the name of all the available themes
        '''
        items = []

        for item in self.list():
            item = get_name_from_path(item)
            items.append(item)

        return items

    def get(self, theme_path):
        '''return a Theme object instance
        returs True, theme_instance if the validation was ok
        False, reason if some validation failed
        '''
        raise NotImplementedError("This method is not implemented")

    def validate(self, theme_path):
        '''validate a Theme directory structure
        '''
        raise NotImplementedError("This method is not implemented")
