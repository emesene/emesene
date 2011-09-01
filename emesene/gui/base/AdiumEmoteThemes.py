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
import logging
log = logging.getLogger('gui.base.AdiumEmoteThemes')

import ThemesManager
import AdiumEmoteTheme

class AdiumEmoteThemes(ThemesManager.ThemesManager):
    '''a class to handle adium themes
    '''

    def __init__(self):
        '''constructor'''
        ThemesManager.ThemesManager.__init__(self, ".AdiumEmoticonset")
        self.default_path = os.path.join('themes', 'emotes', 'default.AdiumEmoticonset')

    def get(self, theme_path):
        '''return a Theme object instance
        returs True, theme_instance if the validation was ok
        False, reason if some validation failed
        '''
        status, message = self.validate(theme_path)

        if not status:
            log.warning(message)
            return status, message

        return True, AdiumEmoteTheme.AdiumEmoteTheme(theme_path)

    def get_emote_theme(self, emote_name):
        ''' return the instance of AdiumEmoteTheme corresponding to the
            emote_name or the default theme if isn't found
        '''
        emote_path = self.default_path

        for elem in self.list():
            if emote_name in elem:
                emote_path = elem

        theme = self.get(emote_path)

        if theme[0]:
            return theme[1]
        else:
            return self.get(self.default_path)[1]

    def validate(self, theme_path):
        '''validate a Theme directory structure
        '''

        if not os.path.isdir(theme_path):
            return False, _("%s is not a directory") % theme_path

        emote_config_file = os.path.join(theme_path, "Emoticons.plist")
        if not os.path.isfile(emote_config_file):
            return False, _("Emoticons.plist not found")
        return True, "ok"
