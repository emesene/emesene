'''This module provides a DBUS API for emesene'''
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

import logging

log = logging.getLogger("emesene.e3.common.DBus")

import extension
import e3
from e3.base import Action

ERROR = False
try:
    import dbus, dbus.service
    if getattr(dbus, 'version', (0,0,0)) >= (0,41,0):
        import dbus.glib
    if getattr(dbus, 'version', (0,0,0)) >= (0,80,0):
        import _dbus_bindings as dbus_bindings
        from dbus.mainloop.glib import DBusGMainLoop
        DBusGMainLoop(set_as_default=True)
    else:
        import dbus.mainloop.glib
        import dbus.dbus_bindings as dbus_bindings
except ImportError, e:
    log.warning('Failed some import on dbus: %s' % str(e))
    ERROR = True

if not ERROR:
    BUS_NAME = 'org.emesene.Service'
    OBJECT_PATH = '/org/emesene/Service'

    class DBusController():

        def __init__(self):
            self.__session = None
            self.__dbus_object = None
            self.__window = None

        #Public methods
        def set_new_session(self, session, window):
            self.__session = session
            self.__window = window
            if self.__dbus_object:
                self.__dbus_object.session = session
                self.__dbus_object.window = window
            else:
                self.__setup()

        def stop(self):
            self.__session.signals.status_change_succeed.unsubscribe(self.__on_status_changed)
            self.destroy_dbus_session()

        #Private methods
        def __setup(self):
            self.__start_dbus()
            self.__session.signals.status_change_succeed.subscribe(self.__on_status_changed)


        def __start_dbus(self):
            '''Start dbus session'''
            self.__destroy_dbus_session()
            self.__session_bus = dbus.SessionBus()
            self.__bus_name = dbus.service.BusName(BUS_NAME, \
                                                   bus=self.__session_bus)
            self.__dbus_object = EmeseneObject(self.__bus_name, OBJECT_PATH, \
                                               self.__session, self.__window)

        def __destroy_dbus_session(self):
            '''Destroy current dbus session'''
            if self.__dbus_object:
                try:
                    dbus.service.Object.remove_from_connection(self.__dbus_object)
                except AttributeError:
                    pass
                self.__dbus_object = None

        #Callback functions
        def __on_status_changed(self, status):
             self.__dbus_object.status_changed(status)


    extension.register('external api', DBusController)

    class EmeseneObject(dbus.service.Object):
        """
        The object that is exported via DBUS
        """
        def __init__(self, bus_name, object_path, session, window):
            try:
                dbus.service.Object.__init__(self, bus_name, object_path)
            except Exception, ex:
                print 'Emesene DBUS error: %s' % str(ex)

            self.__session = session
            self.__window = window

        def get_session(self):
            return self.__session

        def set_session(self, session):
            self.__session = session

        session = property(get_session, set_session)

        #Methods
        @dbus.service.method(BUS_NAME)
        def show_window(self):
            self.__window.present()

        @dbus.service.method(BUS_NAME)
        def get_status(self):
            return self.session.account.status

        @dbus.service.method(BUS_NAME, 'i')
        def set_status(self, status):
            if status == e3.status.DISCONNECTED:
                self.session.quit()
            else:
                self.session.add_action(Action.ACTION_CHANGE_STATUS, (status,))

        #Signals
        @dbus.service.signal(BUS_NAME, 'i')
        def status_changed(self, status):
            pass

else: #ERROR
    class DummyExternalAPI(object):
        provides=('external api', )
        def __init__(self):
            pass
        def set_new_session(self, session, window):
            pass

    extension.register('external api', DummyExternalAPI)

