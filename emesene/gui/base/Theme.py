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
import re

import AdiumThemes
from e3 import status

import plistlib

class Theme(object):
    '''this class contains all the paths and information regarding a theme'''
    # if you add a smilie key twice you will have a nice stack overflow :D
    EMOTES = {} # Emotes defined under set_theme by the Emoticons.plist file found in the theme folder
    EMOTE_FILES = []

    EMOTE_REGEX_STR = ""
    EMOTE_REGEX = None

    SOUND_FILES = ['alert.wav', 'nudge.wav', 'offline.wav', 'online.wav',
            'send.wav', 'type.wav']
    IMAGE_FILES = ['audiovideo.png', 'away.png', 'busy.png', 'call.png', 'chat.png', 'connect.png',
        'email.png','group-chat.png', 'idle.png', 'logo.png', 'logo16.png', 'logo32.png', 'logo48.png', 'new-message.gif','mailbox.png',
        'offline.png', 'online.png', 'password.png', 'typing.png', 'transfer_success.png', 'user.png',
        'users.png', 'user_def_image.png', 'user_def_imagetool.png', 'video.png']

    def __init__(self, image_name="default", emote_name="default",
            sound_name="default", conv_name='renkoo.AdiumMessageStyle', conv_variant = ''):
        '''class constructor'''
        self.set_theme(image_name, emote_name, sound_name, conv_name, conv_variant)

    def set_theme(self, image_name, emote_name, sound_name, conv_name, conv_variant=''):
        '''set the theme name and change all the paths to reflect the change'''
        self.image_name = image_name
        self.emote_name = emote_name
        self.sound_name = sound_name
        # conv_name is the name of the selected adium conversation theme
        self.conv_name = conv_name
        self.adium_theme_variant= conv_variant

        self.theme_path = os.path.join(os.getcwd(),"themes", "images", self.image_name)
        self.conv_themes_path = os.path.join(os.getcwd(), "themes", "conversations")
        self.conv_themes = AdiumThemes.get_instance()
        self.conv_themes.add_themes_path(self.conv_themes_path)

        for elem in self.conv_themes.list():
            if conv_name in elem:
                self.adium_theme_path = elem

        self.conv_theme = self.conv_themes.get(self.adium_theme_path, variant=self.adium_theme_variant)[1]

        self.sound_theme_path = os.path.join("themes", "sounds",
                self.sound_name)

        self.av = os.path.join(self.theme_path, "audiovideo.png")
        self.video = os.path.join(self.theme_path, "video.png")
        self.call = os.path.join(self.theme_path, "call.png")
        self.user = os.path.join(self.theme_path, "user.png")
        self.user_def_image = os.path.join(self.theme_path, "user_def_image.png")
        self.user_def_imagetool = os.path.join(self.theme_path, "user_def_imagetool.png")
        self.email = os.path.join(self.theme_path, "email.png")
        self.mailbox = os.path.join(self.theme_path, "mailbox.png")
        self.users = os.path.join(self.theme_path, "users.png")
        self.password = os.path.join(self.theme_path, "password.png")
        self.logo = os.path.join(self.theme_path, "logo.png")
        self.logo16 = os.path.join(self.theme_path, "logo16.png")
        self.logo32 = os.path.join(self.theme_path, "logo32.png")
        self.logo48 = os.path.join(self.theme_path, "logo48.png")
        self.logo96 = self.logo
        self.throbber = os.path.join(self.theme_path, "throbber.gif")
        self.connect = os.path.join(self.theme_path, "connect.png")
        self.chat = os.path.join(self.theme_path, "chat.png")
        self.group_chat = os.path.join(self.theme_path, "group-chat.png")
        self.typing = os.path.join(self.theme_path, "typing.png")
        self.new_message = os.path.join(self.theme_path, "new-message.gif")
        self.blocked_overlay = os.path.join(self.theme_path, "blocked-overlay.png")
        self.blocked_overlay_big = os.path.join(self.theme_path, "blocked-overlay-big.png")
        self.transfer_success = os.path.join(self.theme_path, "transfer_success.png")
        self.transfer_unsuccess = os.path.join(self.theme_path, "transfer_unsuccess.png")
        self.service_msn = os.path.join(self.theme_path, "msn.png")
        self.service_facebook = os.path.join(self.theme_path, "facebook.png")
        self.service_gtalk = os.path.join(self.theme_path, "gtalk.png")
        self.service_dummy = os.path.join(self.theme_path, "dummy.png")
        self.favorite = os.path.join(self.theme_path, "favorite.png")

        self.sound_alert = os.path.join(self.sound_theme_path, "alert.wav")
        self.sound_nudge = os.path.join(self.sound_theme_path, "nudge.wav")
        self.sound_offline = os.path.join(self.sound_theme_path, "offline.wav")
        self.sound_online = os.path.join(self.sound_theme_path, "online.wav")
        self.sound_send = os.path.join(self.sound_theme_path, "send.wav")
        self.sound_type = os.path.join(self.sound_theme_path, "type.wav")

        self.status_icons = {}
        self.status_icons[status.ONLINE] = \
            os.path.join(self.theme_path, "online.png")
        self.status_icons[status.OFFLINE] = \
            os.path.join(self.theme_path, "offline.png")
        self.status_icons[status.BUSY] = \
            os.path.join(self.theme_path, "busy.png")
        self.status_icons[status.AWAY] = \
            os.path.join(self.theme_path, "away.png")
        self.status_icons[status.IDLE] = \
            os.path.join(self.theme_path, "idle.png")

        self.status_icons_panel = {}
        self.panel_path = self.theme_path
        # allow different icons for indicators/tray icons
        # note: a panel subdirectory requires six pics: 
        #logo.png, online.png, offline.png, busy.png, away.png, idle.png
        panel_path = os.path.join(self.theme_path, "panel")        
        if os.path.exists(panel_path):
            self.panel_path = panel_path
            self.status_icons_panel[status.ONLINE] = \
                os.path.join(self.panel_path, "online.png")
            self.status_icons_panel[status.OFFLINE] = \
                os.path.join(self.panel_path, "offline.png")
            self.status_icons_panel[status.BUSY] = \
                os.path.join(self.panel_path, "busy.png")
            self.status_icons_panel[status.AWAY] = \
                os.path.join(self.panel_path, "away.png")
            self.status_icons_panel[status.IDLE] = \
                os.path.join(self.panel_path, "idle.png")
        else:
            self.status_icons_panel = self.status_icons.copy()

        # allow theme-specific toolbar icons
        self.tool_font = None
        self.tool_font_color = None
        self.tool_emotes = None
        self.tool_nudge = None
        self.tool_invite = None
        self.tool_clean = None
        self.tool_file_transfer = None

        self.toolbar_path = None
        toolbar_path = os.path.join(self.theme_path, "toolbar")        
        if os.path.exists(toolbar_path):
            self.toolbar_path = toolbar_path
            self.tool_font = os.path.join(self.toolbar_path, "font.png")
            self.tool_font_color = os.path.join(self.toolbar_path, "font-color.png")
            self.tool_emotes = os.path.join(self.toolbar_path, "emotes.png")
            self.tool_nudge = os.path.join(self.toolbar_path, "nudge.png")
            self.tool_invite = os.path.join(self.toolbar_path, "invite.png")
            self.tool_clean = os.path.join(self.toolbar_path, "clean-chat.png")
            self.tool_file_transfer = os.path.join(self.toolbar_path, "file-transfer.png")
            self.tool_ublock = os.path.join(self.toolbar_path, "ublock.png")

        self.emote_path = os.path.join('themes', 'emotes', self.emote_name)
        self.emote_config_file = os.path.join(self.emote_path, "Emoticons.plist")

        if os.path.isfile(self.emote_config_file):
            emote_data=plistlib.readPlist(file(self.emote_config_file))
            for key, val in emote_data['Emoticons'].iteritems():
                Theme.EMOTE_FILES.append(key)
                pointer_name = val['Name']
                pointer_key = val['Equivalents'][0]
                Theme.EMOTES[pointer_key] = pointer_name
                for v in val['Equivalents'][1:]:
                    if v != "":
                        Theme.EMOTES[v] = Theme.EMOTES[pointer_key]
            for key2 in Theme.EMOTES:
                Theme.EMOTE_REGEX_STR += re.escape(key2) + "|"
            Theme.EMOTE_REGEX = re.compile("("+Theme.EMOTE_REGEX_STR+")")

    def emote_to_path(self, shortcut, remove_protocol=False):
        '''return a string representing the path to load the emote if it exist
        None otherwise'''

        if shortcut not in Theme.EMOTES:
            return None

        path = os.path.join(self.emote_path, Theme.EMOTES[shortcut]) + '.png'
        path = os.path.abspath(path)

        if os.access(path, os.R_OK) and os.path.isfile(path):
            path = path.replace("\\", "/")

            if remove_protocol:
                return path
            else:
                if os.name == "nt":
                    #if path[1] == ":":
                    #    path = path[2:]
                    path = "localhost/"+path

                return 'file://' + path

        return None

    def get_emotes_count(self):
        '''return the number of emoticons registered'''
        return len(set(Theme.EMOTES.values()))


    def is_valid_theme(self, file_list, path):
        """
        return True if the path contains a valid theme
        """

        for file_name in file_list:
            if not os.path.isfile(os.path.join(path, file_name)):
                return False

        return True

    def get_image_themes(self):
        '''return a list of names for the image themes'''
        themes = []

        for theme in self.get_child_dirs(os.path.join('themes', 'images')):
            if self.is_valid_theme(Theme.IMAGE_FILES,
                    os.path.join('themes', 'images', theme)):
                themes.append(theme)

        return themes

    def get_emote_themes(self):
        '''return a list of names for the emote themes'''
        themes = []
        pattern = re.compile(".AdiumEmoticonset", re.IGNORECASE)

        for theme in self.get_child_dirs(os.path.join('themes', 'emotes')):
            if os.path.isfile(os.path.join('themes','emotes',theme,'Emoticons.plist')):
                theme = pattern.sub('', theme)
                themes.append(theme)

        return themes

    def get_sound_themes(self):
        '''return a list of names for the sound themes'''
        themes = []

        for theme in self.get_child_dirs(os.path.join('themes', 'sounds')):
            if self.is_valid_theme(Theme.SOUND_FILES,
                    os.path.join('themes', 'sounds', theme)):
                themes.append(theme)

        return themes

    def get_adium_themes(self):
        '''return a list of validated adium themes'''
        themes = []
        AdiumThemesM = AdiumThemes.AdiumThemes()
        path_conv = os.path.join('themes', 'conversations')
        pattern = re.compile(".AdiumMessageStyle", re.IGNORECASE)

        for theme in self.get_child_dirs(path_conv):
            if AdiumThemesM.validate(
                                os.path.join(os.path.abspath(path_conv), theme))[0]:
                theme = pattern.sub('', theme)
                themes.append(theme)

        return themes

    def get_adium_theme_variants(self):
        '''return a list of adium theme variants'''
        return self.conv_theme.get_theme_variants()

    def get_child_dirs(self, dir_path):
        '''return a list of dirs inside a given path'''
        try:
            return os.walk(dir_path).next()[1]
        except StopIteration:
            return ()

    def split_smilies(self, text):
        '''split text in smilies, return a list of tuples that contain
        a boolean as first item indicating if the text is an emote or not
        and the text as second item.
        example : [(False, "hi! "), (True, ":)")]
        '''
        keys = Theme.EMOTES.keys()
        return [(item in keys, item) for item in Theme.EMOTE_REGEX.split(text)
                if item is not None]

