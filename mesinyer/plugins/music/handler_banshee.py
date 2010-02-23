import songretriever

import DBusBase

class BansheeHandler(DBusBase.DBusBase):
    '''Handler for Amarok2'''

    def __init__(self, iface_name = 'org.bansheeproject.Banshee',
                 iface_path='/org/bansheeproject/Banshee/PlayerEngine'):
        DBusBase.DBusBase.__init__(self, iface_name, iface_path)

    def is_running(self):
        '''Returns a True if the player is running'''
        try:
            return bool(self.iface)
        except:
            return self.reconnect()

    def is_playing(self):
        '''Returns True if a song is being played'''
        if self.is_running():
            status = self.iface.GetCurrentState()
            if status == 'playing':
                return True
        return False

    def get_current_song(self):
        '''Returns the current song in the correct format'''
        if self.is_playing():
            song = self.iface.GetCurrentTrack()
            return songretriever.Song(song['artist'],
                                      song['album'],
                                      song['name'],
                                      song['local-path'])

songretriever.register('Banshee', BansheeHandler())
