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

import pynotify
if not pynotify.init("emesene"):
    raise ImportError

import logging
log = logging.getLogger('gui.common.PyNotification')

from gui.base import Plus
import gui.gtkui.utils as utils

NAME = 'PyNotification'
DESCRIPTION = 'Wrapper around pynotify for the notification system'
AUTHOR = 'arielj'
WEBSITE = 'www.emesene.org'

def PyNotification(title, text, picture_path=None, const=None,
                   callback=None, tooltip=None):
    if const == 'message-im':
        #In this case title is contact nick
        if title is None:
            title = ""

        title = Plus.msnplus_strip(title)
    notification = pynotify.Notification(title, text, picture_path)
    notification.set_icon_from_pixbuf(utils.safe_gtk_pixbuf_load(picture_path, (96, 96)))
    notification.set_hint_string("append", "allowed")
    notification.show()
