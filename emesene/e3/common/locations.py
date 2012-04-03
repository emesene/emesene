'''a module that provides access to common locations'''
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
import sys
import subprocess

def downloads():
    '''
    return the location of the user's downloads folder

    on windows and mac os x return the desktop folder path
    '''

    if sys.platform.startswith('win'): # Windows
        #import ctypes
        #path = ctypes.c_wchar_p('')
        #ctypes.windll.shell32.SHGetFolderPathW(0, 0x0010, None, 0, path)
        #TODO: find another way to get the Desktop folder that don't break
        #things, see issue #417
        return os.environ.get('USERPROFILE')
    elif sys.platform.startswith('darwin'): # Mac OS X
        return os.path.expanduser('~/Desktop')
    else: # Linux
        path = os.environ.get("XDG_DOWNLOAD_DIR") or \
            get_command_output("xdg-user-dir", "DOWNLOAD")

        if path is not None:
            return path

        downloads = join_home("Downloads")

        if os.path.isdir(downloads):
            return downloads

        else:
            return join_home()

def get_command_output(*args):
    '''
    run a command in the system and return the output,
    return None if something fails
    '''
    try:
        return subprocess.Popen(args,
                stdout=subprocess.PIPE).communicate()[0].strip()
    except OSError:
        return None

def join_home(*paths):
    '''
    join the list of strings to the home folder

    return Nont if $HOME is not set expand ~ fails and xdg-user-dir doesn't exist (?)
    '''

    home = os.environ.get("HOME") or os.path.expanduser("~") or \
            get_command_output("xdg-user-dir")

    if home is None:
        return None

    return os.path.join(home, *paths)
