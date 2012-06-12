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

import gui

NAME = 'ThemeNotificationImage'
DESCRIPTION = 'Returns an image path depending on current theme'
AUTHORS = ['Andrea Stagi', 'arielj']
WEBSITE = 'www.emesene.org'

def ThemeNotificationImage(picture, const_value):
    ''' decides which theme picture to use '''

    if picture:
        if picture.startswith("file://"):
            return picture
    if const_value == 'mail-received':
        return "file://" + gui.theme.image_theme.email
    elif const_value == 'file-transf-completed':
        return "file://" + gui.theme.image_theme.transfer_success
    elif const_value == 'file-transf-canceled':
        return "file://" + gui.theme.image_theme.transfer_unsuccess
    elif const_value == 'logo':
        return "file://" + gui.theme.image_theme.logo
    elif const_value == 'message-im':
        return "file://" + gui.theme.image_theme.user_def_imagetool
    else:
        return "file://" + gui.theme.image_theme.user_def_imagetool
