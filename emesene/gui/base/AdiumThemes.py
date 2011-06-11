'''a module to handle themes'''
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
import ThemesManager
import AdiumTheme

DIRECTORY, FILE = range(2)

REQUIRED_FILES = [
        {'name': 'Contents', 'type': DIRECTORY, 'childs': [
            {'name': 'Info.plist', 'type': FILE},
            {'name': 'Resources', 'type': DIRECTORY, 'childs': [
                #{'name': 'main.css', 'type': FILE},
                {'name': 'Status.html', 'type': FILE},
                {'name': 'Incoming', 'type': DIRECTORY, 'childs': [
                    {'name': 'Content.html', 'type': FILE},
                ]}
            ]}
        ]}]

class AdiumThemes(ThemesManager.ThemesManager):
    '''a class to handle adium themes
    '''

    def __init__(self):
        '''constructor'''
        ThemesManager.ThemesManager.__init__(self, ".AdiumMessageStyle")

    def get(self, theme_path, timefmt="%H:%M", variant=''):
        '''return a Theme object instance
        returs True, theme_instance if the validation was ok
        False, reason if some validation failed
        '''
        status, message = self.validate(theme_path)

        if not status:
            return status, message

        return True, AdiumTheme.AdiumTheme(theme_path, timefmt, variant)

    def get_conv_theme (self, conv_name, theme_variant):
        ''' return the instance of AdiumTheme corresponding to the
            conv_name or the default theme if isn't found
        '''
        conv_path = os.path.join('themes', 'conversations', 'renkoo.AdiumMessageStyle')

        for elem in self.list():
            if conv_name in elem:
                conv_path = elem

        return self.get(conv_path, variant=theme_variant)[1]

    def validate(self, theme_path):
        '''validate a Theme directory structure
        '''

        if not os.path.isdir(theme_path):
            return False, "%s is not a directory" % (theme_path,)

        return self.validate_structure(theme_path, REQUIRED_FILES)

    def validate_structure(self, base_path, structure):
        '''validate the required files and directories from base_path
        '''

        for item in structure:
            name = os.path.join(base_path, item['name'])

            if item['type'] == FILE:
                if not os.path.isfile(name):
                    return False, _("%s is not a file") % (name, )
                if not os.access(name, os.R_OK):
                    return False, _("%s is not readable") % (name, )
            elif item['type'] == DIRECTORY:
                if not os.path.isdir(name):
                    return False, _("%s is not a directory") % (name, )

                return self.validate_structure(name, item['childs'])

        return True, "ok"

