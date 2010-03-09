import songretriever

ROOT_NAME = 'org.freedesktop.DBus'
ROOT_PATH = '/org/freedesktop/DBus'

class DBusBase(MusicHandler):
    '''Handler for music players that use DBus'''

    def __init__(self, iface_name,
                 iface_path):
        self.iface_name = iface_name
        self.iface_path = iface_path

        try:
            import dbus
            dbus_version = getattr(dbus, 'version', (0, 0, 0))
            if dbus_version >= (0, 41, 0) and dbus_version < (0, 80, 0):
                dbus.SessionBus()
                import dbus.glib
            elif dbus_version >= (0, 80, 0):
                from dbus.mainloop.glib import DBusGMainLoop
                DBusGMainLoop(set_as_default = True)
                dbus.SessionBus()
            else:
                print 'python-dbus is too old, please update'
                raise
        except:
            print 'cannot start dbus, please check if dbus is installed'

        #dbus session, this is set in reconnect.
        self.bus = None
        #dbus interface set in reconnect.
        self.iface = None
        self.module = dbus
        self.root = dbus.SessionBus().get_object(ROOT_NAME, ROOT_PATH)

    def reconnect(self):
        '''method to attemp a reconnection, via dbus, this is only
        called if the bus object is not initialized'''
        self.bus = self.module.SessionBus()
        try:
            self.iface = self.bus.get_object(self.iface_name, self.iface_path)
            return True
        except:
            self.iface = None
            return False

    def is_running(self):
        '''Returns a True if the player is running'''
        if self.is_name_active(self.iface_name):
            if self.iface is None:
                self.reconnect()
            return True
        else:
            self.iface = None
            return False

    def is_playing(self):
        '''Returns True if a song is being played'''
        return False

    def get_current_song(self):
        '''Returns the current song in the correct format'''
        return False

    def is_name_active(self, name):
        '''return True if the name is active on dbus'''
        return bool(self.root.NameHasOwner(name))

