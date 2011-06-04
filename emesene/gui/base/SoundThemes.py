'''a module to handle sound themes'''
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
import SoundTheme

SOUND_FILES = ['alert.wav', 'nudge.wav', 'offline.wav', 'online.wav',
            'send.wav', 'type.wav']

__instance = None

def get_instance():
    '''singleton for Themes class
    '''
    global __instance

    if __instance is None:
        __instance = SoundThemes()

    return __instance


class SoundThemes(ThemesManager.ThemesManager):
    '''a class to handle sound themes
    '''

    def __init__(self):
        '''constructor'''
        ThemesManager.ThemesManager.__init__(self, "")

    def get(self, theme_path):
        '''return a Theme object instance
        returs True, theme_instance if the validation was ok
        False, reason if some validation failed
        '''
        status, message = self.validate(theme_path)

        if not status:
            return status, message

        return True, SoundTheme.SoundTheme(theme_path)

    def get_sound_theme (self, sound_name):
        ''' return the instance of SoundThemes corresponding to the
            sound_name or the default theme if isn't found
        '''
        sound_path = os.path.join('themes', 'sounds', 'default')

        for elem in self.list():
            if sound_name in elem:
                sound_path = elem

        return self.get(sound_path)[1]

    def validate(self, theme_path):
        '''validate a Theme directory structure
        '''

        if not os.path.isdir(theme_path):
            return False, "%s is not a directory" % (theme_path,)

        if not self.is_valid_theme(SOUND_FILES, theme_path):
            return False, "Sound theme incomplete"
        return True, "ok"

    def is_valid_theme(self, file_list, path):
        """
        return True if the path contains a valid theme
        """

        for file_name in file_list:
            if not os.path.isfile(os.path.join(path, file_name)):
                return False
        return True
