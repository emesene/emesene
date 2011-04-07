# -*- coding: utf-8 -*-

#   This file is part of emesene.
#
#    Emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
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
#
#    Module written by Andrea Stagi <stagi.andrea(at)gmail.com>

class synch():

        def __init__(self):
            pass

        def start_synch(self, session, end_callback, prog_callback):
            self._session = session
            self._end_callback = end_callback
            self._prog_callback = prog_callback

        def set_source_path(self,path):
            self.__srcpath=path

        def _start_synch(self):
            pass

        def set_destination_path(self,path):
            self.__destpath=path

        @property
        def dest_path(self):
            return self.__destpath

        @property
        def src_path(self):
            return self.__srcpath
