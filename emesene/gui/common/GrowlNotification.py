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

try:
    open("/usr/local/bin/growlnotify")
except IOError:
    raise ImportError

import subprocess

from gui.base import Plus
import logging
log = logging.getLogger('gui.gtkui.GrowlNotification')

NAME = 'GrowlNotification'
DESCRIPTION = 'Wrapper around growlnotify for the notification system'
AUTHOR = 'joshf'
WEBSITE = 'www.sidhosting.co.uk'
VERSION = '0.4'

def GrowlNotification(title, text, uri, picture_path=None, const=None, 
                      callback=None, tooltip=None):
    title = Plus.msnplus_strip(title)
    if uri == 'notification-message-im':
        subprocess.call(['/usr/local/bin/growlnotify', '-n', 'emesene', '-a', 'emesene', '-t', title, '-m', text])
    else:
        imagepath = uri.replace( "file:///", "/" )
        #BUG: In growl prefs, the emesene ticket will take on the last shown contact's picture
        subprocess.call(['/usr/local/bin/growlnotify', '-n', 'emesene', '--image', imagepath, '-t', title, '-m', text])
