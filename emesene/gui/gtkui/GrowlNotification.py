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

import Renderers
import logging
log = logging.getLogger('gui.gtkui.GrowlNotification')

NAME = 'GrowlNotification'
DESCRIPTION = 'Wrapper around growlnotify for the notification system'
AUTHOR = 'joshf'
WEBSITE = 'www.sidhosting.co.uk'
VERSION = '0.2'

def GrowlNotification(title, text, picture_path=None, const=None,
                   callback=None, tooltip=None):
        titlestripped = Renderers.msnplus_to_plain_text(title)
        title = titlestripped.replace( " ", "\ " )
        text = text.replace( " ", "\ " )
        os.system("/usr/local/bin/growlnotify -n emesene -a emesene -t emesene:\ """+title+""" -m """+text+"""""")