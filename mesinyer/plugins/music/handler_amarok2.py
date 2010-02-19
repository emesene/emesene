import songretriever
import os

class AmarokHandler(object):
    '''Handler for Amarok2'''

    def __init__(self, iface_name = 'org.mpris.amarok', 
                 iface_path='/TrackList'):
        self.iface_name = iface_name
        self.iface_path = iface_path

        try:
            import dbus
            dbus_version = getattr(dbus, 'version', (0,0,0))
            if dbus_version >=(0,41,0) and dbus_version < (0, 80, 0):
                dbus.SessionBus()
                import dbus.glib
            elif dbus_version >= (0, 80, 0):
                from dbus.mainloop.glib import DBusGMainLoop
                DBusGMainLoop(set_as_default = True)
                dbus.SessionBus()
            else:
                print 'python-dbus is too old, please update'
                raise
        except Exception, e:
            print 'cannot start dbus, please check if dbus is installed'
        self.module = dbus 
        self.reconnect()

    def reconnect(self):
        self.bus = self.module.SessionBus()
        try:
            self.iface= self.bus.get_object(self.iface_name, self.iface_path)
            return True
        except:
            self.iface=None
            return False
    
    def is_running(self):
        try:
            is_running_iface = self.bus.get_object(self.iface_name, '/Player')
            if is_running_iface:
                return True
            else: 
                return False
        except:
           return self.reconnect()
    
    def is_playing(self):
        if self.is_running():
            is_playing_iface = self.bus.get_object(self.iface_name, '/Player')
            if is_playing_iface:
                status = is_playing_iface.GetStatus()
                if status[0]==0:
                    return True
        return False

    def get_current_song(self):
        if self.is_playing():
            track = self.iface.GetCurrentTrack()
            song = self.iface.GetMetadata(track)
            return songretriever.Song(song['artist'],
                                      song['album'],
                                      song['title'],
                                      song['location'])
songretriever.register('Amarok2', AmarokHandler())
