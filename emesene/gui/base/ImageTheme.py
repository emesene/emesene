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

class ImageTheme(object):
    '''a class that contains information of a image theme
    '''

    def __init__(self, path):
        '''constructor

        get information from the theme located in path
        '''
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
        
        self.load_information(path)

    def load_information(self, path):
        '''load the information of the theme on path
        '''
        self.av = os.path.join(path, "audiovideo.png")
        self.video = os.path.join(path, "video.png")
        self.call = os.path.join(path, "call.png")
        self.user = os.path.join(path, "user.png")
        self.user_def_image = os.path.join(path, "user_def_image.png")
        self.user_def_imagetool = os.path.join(path, "user_def_imagetool.png")
        self.email = os.path.join(path, "email.png")
        self.mailbox = os.path.join(path, "mailbox.png")
        self.users = os.path.join(path, "users.png")
        self.password = os.path.join(path, "password.png")
        self.logo = os.path.join(path, "logo.png")
        self.logo16 = os.path.join(path, "logo16.png")
        self.logo32 = os.path.join(path, "logo32.png")
        self.logo48 = os.path.join(path, "logo48.png")
        self.logo96 = self.logo
        self.throbber = os.path.join(path, "throbber.gif")
        self.connect = os.path.join(path, "connect.png")
        self.chat = os.path.join(path, "chat.png")
        self.group_chat = os.path.join(path, "group-chat.png")
        self.typing = os.path.join(path, "typing.png")
        self.new_message = os.path.join(path, "new-message.gif")
        self.blocked_overlay = os.path.join(path, "blocked-overlay.png")
        self.blocked_overlay_big = os.path.join(path, "blocked-overlay-big.png")
        self.transfer_success = os.path.join(path, "transfer_success.png")
        self.transfer_unsuccess = os.path.join(path, "transfer_unsuccess.png")
        self.service_msn = os.path.join(path, "msn.png")
        self.service_facebook = os.path.join(path, "facebook.png")
        self.service_gtalk = os.path.join(path, "gtalk.png")
        self.service_dummy = os.path.join(path, "dummy.png")
        self.favorite = os.path.join(path, "favorite.png")

        self.status_icons[status.ONLINE] = \
            os.path.join(path, "online.png")
        self.status_icons[status.OFFLINE] = \
            os.path.join(path, "offline.png")
        self.status_icons[status.BUSY] = \
            os.path.join(path, "busy.png")
        self.status_icons[status.AWAY] = \
            os.path.join(path, "away.png")
        self.status_icons[status.IDLE] = \
            os.path.join(path, "idle.png")

        # allow different icons for indicators/tray icons
        # note: a panel subdirectory requires six pics: 
        #logo.png, online.png, offline.png, busy.png, away.png, idle.png
        self.panel_path = path
        panel_path = os.path.join(path, "panel")
        if os.path.exists(panel_path):
            self.panel_path = panel_path
            self.logo_panel = os.path.join(panel_path, "logo.png")
            self.status_icons_panel[status.ONLINE] = \
                os.path.join(panel_path, "online.png")
            self.status_icons_panel[status.OFFLINE] = \
                os.path.join(panel_path, "offline.png")
            self.status_icons_panel[status.BUSY] = \
                os.path.join(panel_path, "busy.png")
            self.status_icons_panel[status.AWAY] = \
                os.path.join(panel_path, "away.png")
            self.status_icons_panel[status.IDLE] = \
                os.path.join(panel_path, "idle.png")
        else:
            self.status_icons_panel = self.status_icons.copy()
            self.logo_panel = self.logo.copy()

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
            self.tool_ublock = os.path.join(toolbar_path, "ublock.png")

    def has_custom_toolbar_icons(self):
        return self.toolbar_path != None

