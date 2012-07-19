'''a module that contains a class that describes a image theme'''
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
from e3 import status
from e3.common.MetaData import MetaData

class ImageTheme(MetaData):
    '''a class that contains information of a image theme
    '''

    def __init__(self, path):
        '''constructor

        get information from the theme located in path
        '''
        MetaData.__init__(self, path)
        self.av                 = None
        self.video              = None
        self.call               = None
        self.user               = None
        self.user_def_image     = None
        self.user_def_imagetool = None
        self.email              = None
        self.mailbox            = None
        self.users              = None
        self.password           = None
        self.logo               = None
        self.logo16             = None
        self.logo32             = None
        self.logo48             = None
        self.logo96             = None
        self.throbber           = None
        self.connect            = None
        self.chat               = None
        self.group_chat         = None
        self.typing             = None
        self.new_message        = None
        self.blocked_overlay    = None
        self.blocked_overlay_big= None
        self.transfer_success   = None
        self.transfer_unsuccess = None
        self.service_msn        = None
        self.service_facebook   = None
        self.service_gtalk      = None
        self.service_webqq      = None
        self.service_dummy      = None
        self.favorite           = None

        self.status_icons = {}
        self.status_icons_panel = {}

        # allow theme-specific toolbar icons
        self.tool_font = None
        self.tool_font_color = None
        self.tool_emotes = None
        self.tool_nudge = None
        self.tool_invite = None
        self.tool_clean = None
        self.tool_file_transfer = None

        self.default_path = os.path.join(os.getcwd(), 'themes', 'images', 'default')

        self.load_information(path)

    def load_information(self, path):
        '''load the information of the theme on path
        '''
        self.av = self.get_image(path, "audiovideo.png")
        self.video = self.get_image(path, "video.png")
        self.call = self.get_image(path, "call.png")
        self.user = self.get_image(path, "user.png")
        self.user_def_image = self.get_image(path, "user_def_image.png")
        self.user_def_imagetool = self.get_image(path, "user_def_imagetool.png")
        self.email = self.get_image(path, "email.png")
        self.mailbox = self.get_image(path, "mailbox.png")
        self.users = self.get_image(path, "users.png")
        self.password = self.get_image(path, "password.png")
        self.logo = self.get_image(path, "logo.png")
        self.logo16 = self.get_image(path, "logo16.png")
        self.logo32 = self.get_image(path, "logo32.png")
        self.logo48 = self.get_image(path, "logo48.png")
        self.logo96 = self.logo
        self.throbber = self.get_image(path, "throbber.gif")
        self.connect = self.get_image(path, "connect.png")
        self.chat = self.get_image(path, "chat.png")
        self.group_chat = self.get_image(path, "group-chat.png")
        self.typing = self.get_image(path, "typing.png")
        self.new_message = self.get_image(path, "new-message.gif")
        self.blocked_overlay = self.get_image(path, "blocked-overlay.png")
        self.blocked_overlay_big = self.get_image(path, "blocked-overlay-big.png")
        self.transfer_success = self.get_image(path, "transfer_success.png")
        self.transfer_unsuccess = self.get_image(path, "transfer_unsuccess.png")
        self.service_msn = self.get_image(path, "msn.png")
        self.service_facebook = self.get_image(path, "facebook.png")
        self.service_gtalk = self.get_image(path, "gtalk.png")
        self.service_webqq = self.get_image(path, "webqq.png")
        self.service_dummy = self.get_image(path, "dummy.png")
        self.favorite = self.get_image(path, "favorite.png")

        self.status_icons[status.ONLINE] = \
            self.get_image(path, "online.png")
        self.status_icons[status.OFFLINE] = \
            self.get_image(path, "offline.png")
        self.status_icons[status.BUSY] = \
            self.get_image(path, "busy.png")
        self.status_icons[status.AWAY] = \
            self.get_image(path, "away.png")
        self.status_icons[status.IDLE] = \
            self.get_image(path, "idle.png")

        # allow different icons for indicators/tray icons
        # note: a panel subdirectory requires six pics: 
        #logo.png, online.png, offline.png, busy.png, away.png, idle.png
        self.panel_path = path
        panel_path = os.path.join(path, "panel")
        if os.path.exists(panel_path):
            self.panel_path = panel_path
            self.logo_panel = self.get_image(path, "panel", "logo.png")
            self.status_icons_panel[status.ONLINE] = \
                self.get_image(path, "panel", "online.png")
            self.status_icons_panel[status.OFFLINE] = \
                self.get_image(path, "panel", "offline.png")
            self.status_icons_panel[status.BUSY] = \
                self.get_image(path, "panel", "busy.png")
            self.status_icons_panel[status.AWAY] = \
                self.get_image(path, "panel", "away.png")
            self.status_icons_panel[status.IDLE] = \
                self.get_image(path, "panel", "idle.png")
        else:
            self.status_icons_panel = self.status_icons.copy()
            self.logo_panel = self.logo

        # allow theme-specific toolbar icons
        self.toolbar_path = None
        toolbar_path = os.path.join(path, "toolbar")
        if os.path.exists(toolbar_path):
            self.toolbar_path = toolbar_path
            self.tool_font = os.path.join(toolbar_path, "font.png")
            self.tool_font_color = os.path.join(toolbar_path, "font-color.png")
            self.tool_emotes = os.path.join(toolbar_path, "emotes.png")
            self.tool_nudge = os.path.join(toolbar_path, "nudge.png")
            self.tool_invite = os.path.join(toolbar_path, "invite.png")
            self.tool_clean = os.path.join(toolbar_path, "clean-chat.png")
            self.tool_file_transfer = os.path.join(toolbar_path, "file-transfer.png")
            self.tool_block = os.path.join(toolbar_path, "ublock.png")
            self.tool_unblock = os.path.join(toolbar_path, "user_unblock.png")

    def get_image(self, base_path, *paths):
        '''get the image path or else use the default image'''
        full_path = os.path.join(base_path, *paths)
        if os.path.isfile(full_path):
            return full_path
        else:
            return os.path.join(self.default_path, *paths)

    def has_custom_toolbar_icons(self):
        return self.toolbar_path is not None
