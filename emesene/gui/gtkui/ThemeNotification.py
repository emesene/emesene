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
import pynotify
import os
if not pynotify.init("emesene"):
    raise ImportError

import logging
log = logging.getLogger('gui.gtkui.ThemeNotification')

NAME = 'ThemeNotification'
DESCRIPTION = 'Wrapper around pynotify for the notification system. Notifier depends by the current theme'
AUTHOR = 'Andrea Stagi'
WEBSITE = 'www.emesene.org'

def localThemeEl(el):
    return "file://"+ os.path.join(os.getcwd() , el)

def pictureFactory(constValue):
    if(constValue=='notification-message-email'):
        return localThemeEl(gui.theme.email)
    elif(constValue=='notification-message-im'):
        return localThemeEl(gui.theme.user_def_image)
    else:
        return constValue

def themeNotification(title, text, picturePath=None):
    n = pynotify.Notification(title, text, pictureFactory(picturePath)) 
    n.set_hint_string("append", "allowed")
    n.show()
