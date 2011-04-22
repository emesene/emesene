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

class Synch(object):

        def __init__(self):
            pass

        def initialize(self, session, end_callback, prog_callback, action_callback):
            self._session = session
            self._end_callback = end_callback
            self._prog_callback = prog_callback
            self._action_callback = action_callback
            self.__src_db_path = ""
            self.__dest_db_path = ""
            self.__src_db_path_copy = ""

        def set_user(self, user_account):
            pass

        def exists_source(self):
            return False

        def is_clean(self):
            return True

        def clean(self):
            pass

        def __create_safe_copy(self):
            pass

        def start_synch(self):
            pass

