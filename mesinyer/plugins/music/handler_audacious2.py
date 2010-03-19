import songretriever

import DBusBase

class Audacious2Handler(DBusBase.DBusBase):
    '''Handler for audacious2'''

    def __init__(self, iface_name = 'org.atheme.audacious',
                 iface_path='/org/atheme/audacious'):
        DBusBase.DBusBase.__init__(self, iface_name, iface_path)

    def is_playing(self):
        '''Returns True if a song is being played'''
        # Note: Can't use self.iface.Playing() because
        # returns True even if the song is paused
        if self.is_running():
            return self.iface.Status() == "playing"

        return False

    def get_current_song(self):
        '''Returns the current song in the correct format'''
        if self.is_playing():
            song_position = self.iface.Position()
            artist = self.iface.SongTuple(song_position, "artist") 
            album = self.iface.SongTuple(song_position, "album") 
            title = self.iface.SongTuple(song_position, "title") 
            return songretriever.Song(artist, album, title)

songretriever.register('audacious2', Audacious2Handler)
