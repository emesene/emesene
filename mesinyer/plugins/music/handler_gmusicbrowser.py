import songretriever
import DBusBase

class GMusicBrowserHandler(DBusBase.DBusBase):
    '''Handler for gmusicbrowser'''
    NAME = 'GMusicBrowser'
    DESCRIPTION = 'Music handler for gmusicbrowser'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, main_window = None,
                 iface_name = 'org.gmusicbrowser',
                 iface_path = '/org/gmusicbrowser'):
        DBusBase.DBusBase.__init__(self, main_window, iface_name, iface_path)

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


