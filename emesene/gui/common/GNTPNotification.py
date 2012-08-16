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

import gntp.notifier

import gui
from gui.base import Plus

NAME = 'GNTPNotification'
DESCRIPTION = 'Wrapper around GNTP for the notification system'
AUTHOR = 'joshf'
WEBSITE = 'www.sidhosting.co.uk'
VERSION = '1.0'

def GNTPNotification(title, text, picture_path=None, const=None, 
                      callback=None, tooltip=None):

    title = Plus.msnplus_strip(title)

    appicon = open(gui.theme.image_theme.logo).read()
    imagepath = picture_path.replace( "file:///", "/" )
    icon = open(imagepath).read()

    growl = gntp.notifier.GrowlNotifier(
        applicationName = "emesene",
        applicationIcon = appicon,
        notifications = ["Generic Notification"],
        defaultNotifications = ["Generic Notification"],
        # hostname = "computer.example.com", # Defaults to localhost
        # password = "abc123" # Defaults to a blank password
    )

    growl.register()

    growl.notify(
        noteType = "Generic Notification",
        title = title,
        description = text,
        icon = icon,
        sticky = False,
        priority = 1,
    )
