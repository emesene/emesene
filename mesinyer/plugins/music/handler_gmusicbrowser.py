import songretriever

import DBusBase

class GMusicBrowserkHandler(DBusBase.DBusBase):
    '''Handler for gmusicbrowser'''

    def __init__(self, iface_name = 'org.gmusicbrowser',
                 iface_path='/org/gmusicbrowser'):
        DBusBase.DBusBase.__init__(self, iface_name, iface_path)

    def is_running(self):
        '''Returns a True if the player is running'''
        return self.is_name_active(self.iface_name)

    def is_playing(self):
        '''Returns True if a song is being played'''
        if self.is_running():
            return bool(self.iface.Playing())

        return False

    def get_current_song(self):
        '''Returns the current song in the correct format'''
        if self.is_playing():
            song = self.iface.CurrentSong()
            return songretriever.Song(song['artist'],
                                      song['album'],
                                      song['title'])

songretriever.register('gmusicbrowser', GMusicBrowserkHandler())
