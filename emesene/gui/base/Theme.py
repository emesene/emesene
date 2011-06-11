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

from e3.common import ConfigDir
import AdiumThemes
import AdiumEmoteThemes
import SoundThemes
import ImagesThemes

class Theme(object):
    '''this class contains all the paths and information regarding a theme'''

    def __init__(self, image_name="default", emote_name="default",
            sound_name="default", conv_name='renkoo.AdiumMessageStyle', conv_variant = ''):
        '''class constructor'''
        self.emote_theme = None
        self.config_dir = ConfigDir.ConfigDir('emesene2')
        self.config_path = self.config_dir.join('')

        #check for themes in .config dir
        self.config_themes_path = os.path.join(self.config_path, "themes")
        self.ensure_dir_path(self.config_themes_path)

        self.config_conv_themes_path = os.path.join(self.config_themes_path, "conversations")
        self.ensure_dir_path(self.config_conv_themes_path)

        self.conv_themes_path = os.path.join(os.getcwd(), "themes", "conversations")
        self.conv_themes = AdiumThemes.AdiumThemes()
        self.conv_themes.add_themes_path(self.conv_themes_path)
        self.conv_themes.add_themes_path(self.config_conv_themes_path)


        self.config_sound_themes_path = os.path.join(self.config_themes_path, "sounds")
        self.ensure_dir_path(self.config_sound_themes_path)

        self.sound_theme_path = os.path.join("themes", "sounds")
        self.sound_themes = SoundThemes.SoundThemes()
        self.sound_themes.add_themes_path(self.sound_theme_path)
        self.sound_themes.add_themes_path(self.config_sound_themes_path)

        self.config_emotes_themes_path = os.path.join(self.config_themes_path, "emotes")
        self.ensure_dir_path(self.config_emotes_themes_path)

        self.emotes_themes_path = os.path.join(os.getcwd(), "themes", "emotes")
        self.emotes_themes = AdiumEmoteThemes.AdiumEmoteThemes()
        self.emotes_themes.add_themes_path(self.emotes_themes_path)
        self.emotes_themes.add_themes_path(self.config_emotes_themes_path)

        self.config_images_themes_path = os.path.join(self.config_themes_path, "images")
        self.ensure_dir_path(self.config_images_themes_path)

        self.image_path = os.path.join(os.getcwd(),"themes", "images")
        self.image_themes = ImagesThemes.ImagesThemes()
        self.image_themes.add_themes_path(self.image_path)
        self.image_themes.add_themes_path(self.config_images_themes_path)

        self.set_theme(image_name, emote_name, sound_name, conv_name, conv_variant)

    def set_theme(self, image_name, emote_name, sound_name, conv_name, conv_variant=''):
        '''set the theme name and change all the paths to reflect the change'''

        # conv_name is the name of the selected adium conversation theme
        self.conv_theme = self.conv_themes.get_conv_theme (conv_name, conv_variant)
        self.sound_theme = self.sound_themes.get_sound_theme (sound_name)
        self.image_theme = self.image_themes.get_image_theme (image_name)
        self.emote_theme = self.emotes_themes.get_emote_theme (emote_name)

    def get_emote_theme(self):
        ''' return the current emote theme '''
        return self.emote_theme

    def get_image_theme(self):
        ''' return the current emote theme '''
        return self.image_theme

    def get_image_themes(self):
        '''return a list of names for the image themes'''
        return self.image_themes.get_name_list()

    def get_emote_themes(self):
        '''return a list of names for the emote themes'''
        return self.emotes_themes.get_name_list()

    def get_sound_themes(self):
        '''return a list of names for the sound themes'''
        return self.sound_themes.get_name_list()

    def get_adium_themes(self):
        '''return a list of validated adium themes'''
        return self.conv_themes.get_name_list()

    def ensure_dir_path(self, dir_path):
        ''' check for a dir in .config and
        creates it if doesn't exist
        '''
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

