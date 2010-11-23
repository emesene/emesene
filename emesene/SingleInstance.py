#!/usr/bin/env python
'''Allow only one instance running, I don't know why someone would want that, but well...'''
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
import tempfile
import getpass

class SingleInstance:
    def __init__(self):

        self._bus_name = 'org.emesene.dbus'
        self._object_path = '/org/emesene/dbus'

        self.new_dbus = False
        self.have_dbus = False
        self.dbus = None

        if os.name == 'posix':
            try:
                import dbus, dbus.service
                dbus_version = getattr(dbus, 'version', (0, 0, 0))
                if dbus_version >= (0, 41, 0):
                    import dbus.glib
                if dbus_version >= (0, 80, 0):
                    from dbus.mainloop.glib import DBusGMainLoop
                    DBusGMainLoop(set_as_default=True)
                    self.new_dbus = True
                else:
                    import dbus.mainloop.glib
                    self.new_dbus = False
                self.have_dbus = True
                self.dbus = dbus
            except dbus.DBusException, error:
                self.have_dbus = False
                print 'Unable to use D-Bus: %s' % str(error)

        self.lock_file_name = os.path.normpath(tempfile.gettempdir() +
                            '/emesene-' + getpass.getuser() + '.lock')
        self.lock_file = None

    def emesene_is_running(self):
        '''Checks if emesene is already running'''
        if os.name == 'posix':
            import fcntl
            self.lock_file = open(self.lock_file_name, 'w')
            try:
                fcntl.lockf(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError:
                return True
            return False
        else:
            try:
                # if file already exists, we try to remove it
                # (in case a previous execution was interrupted)
                if os.path.exists(self.lock_file_name):
                    os.unlink(self.lock_file_name)
                self.lock_file =  os.open(self.lock_file_name,
                                 os.O_CREAT | os.O_EXCL | os.O_RDWR)
            except OSError, error:
                if error.errno == 13:
                    return True
                print error.errno
                return False
            return False
                
    def show(self):
        ''' tries to bring to front the instance of emesene
        that is already running'''
        if os.name == "posix":
            if not self.have_dbus:
                # Is there a no dbus way to do this?
                return
            try:
                emesene_bus = self.dbus.SessionBus()
                emesene_object = emesene_bus.get_object(self._bus_name, self._object_path)
                emesene_object.show()
            except self.dbus.DBusException, error:
                print "%s" % error
        else:
            try:
                # import win32api
                import win32con
                import win32gui
            except ImportError:
                print "Can't import win32"
                return

            def window_enumeration_handler(hwnd, result_list):
                '''Pass to win32gui.EnumWindows() to generate list of window handle, window text tuples.'''
                result_list.append((hwnd, win32gui.GetWindowText(hwnd)))

            window_text = "emesene"
            top_windows = []
            win32gui.EnumWindows(window_enumeration_handler, top_windows)
            print len(top_windows)
            for window in top_windows:
                if window[1] and window_text.lower() in window[1].lower():
                    print window[1]
                    win32gui.ShowWindow(window[0], win32con.SW_SHOW)
                    win32gui.SetForegroundWindow(window[0])

    def __del__(self):
        '''Be sure that the file will be closed and deleted'''
        '''This is a must in windows'''
        if os.name == 'nt':
            if hasattr(self, 'lock_file'):
                os.close(self.lock_file)
                os.unlink(self.lock_file_name)


