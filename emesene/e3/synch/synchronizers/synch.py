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

from threading import Thread

class synch(Thread):

        def __init__(self):
            Thread.__init__(self)

        def start_synch(self, session):
            self._session = session
            self.start()

        def set_source_path(self,path):
            self.__srcpath=path

        def _start_synch(self):
            pass

        def run(self):
            self._start_synch()

        def set_destination_path(self,path):
            self.__destpath=path

        @property
        def dest_path(self):
            return self.__destpath

        @property
        def src_path(self):
            return self.__srcpath
