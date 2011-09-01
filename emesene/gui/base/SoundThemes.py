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
import logging
log = logging.getLogger('gui.base.SoundThemes')

import ThemesManager
import SoundTheme

class SoundThemes(ThemesManager.ThemesManager):
    '''a class to handle sound themes
    '''

    def __init__(self):
        '''constructor'''
        ThemesManager.ThemesManager.__init__(self, ".AdiumSoundset")
        self.default_path = os.path.join('themes', 'sounds', 'default.AdiumSoundset')

    def get(self, theme_path):
        '''return a Theme object instance
        returs True, theme_instance if the validation was ok
        False, reason if some validation failed
        '''
        status, message = self.validate(theme_path)

        if not status:
            log.warning(message)
            return status, message

        return True, SoundTheme.SoundTheme(theme_path)

    def get_sound_theme(self, sound_name):
        ''' return the instance of SoundThemes corresponding to the
            sound_name or the default theme if isn't found
        '''
        sound_path = self.default_path

        for elem in self.list():
            if sound_name in elem:
                sound_path = elem

        theme = self.get(sound_path)

        if theme[0]:
            return theme[1]
        else:
            return self.get(self.default_path)[1]

    def validate(self, theme_path):
        '''validate a Theme directory structure
        '''
        if not os.path.isdir(theme_path):
            return False, _("%s is not a directory") % theme_path

        sound_config_file = os.path.join(theme_path, "Sounds.plist")
        if not os.path.isfile(sound_config_file):
            return False, _("Sounds.plist not found")
        return True, "ok"
