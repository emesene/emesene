import songretriever

import DBusBase

class GuayadequeHandler(DBusBase.DBusBase):
    '''Handler for guayadeque'''

    def __init__(self, iface_name = 'org.mpris.guayadeque',
                 iface_path='/Player'):
        DBusBase.DBusBase.__init__(self, iface_name, iface_path)

    def is_playing(self):
        '''Returns True if a song is being played'''
        if self.is_running():
            status = self.iface.get_dbus_method("GetStatus", dbus_interface='org.freedesktop.MediaPlayer')()
            return status[0] == 0
        return False

    def get_current_song(self):
        '''Returns the current song in the correct format'''
        if self.is_playing():
            song = self.iface.get_dbus_method("GetMetadata", dbus_interface='org.freedesktop.MediaPlayer')()
            return songretriever.Song(song['artist'],
                                      song['album'],
                                      song['title'])

songretriever.register('guayadeque', GuayadequeHandler)
