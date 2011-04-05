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

import Renderers
import logging
log = logging.getLogger('gui.gtkui.ThemeNotification')

NAME = 'ThemeNotification'
DESCRIPTION = 'Wrapper around pynotify for the notification system. Notifier depends by the current theme'
AUTHOR = 'Andrea Stagi'
WEBSITE = 'www.emesene.org'

def themeNotification(title, text, picturePath=None,const=None):
    
    def pictureFactory(picture,constValue):

        if(picture):
            if(picture[:7]=="file://"):
                return picture
        if(constValue=='mail-received'):
            return "file://" + gui.theme.email
        elif(constValue=='file-transf-completed'):
            return "file://" + gui.theme.transfer_success
        elif(constValue=='file-transf-canceled'):
            return "file://" + gui.theme.transfer_unsuccess
        elif(constValue=='message-im'):
            return "file://" + gui.theme.user_def_imagetool
        else:
            return "file://" + gui.theme.user_def_imagetool

    if (const=='message-im'):
        #In this case title is contact nick
        title = Renderers.msnplus_to_plain_text(title)
    n = pynotify.Notification(title, text, pictureFactory(picturePath,const)) 
    n.set_hint_string("append", "allowed")
    n.show()


