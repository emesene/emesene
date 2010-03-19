import socket

import songretriever
from thirdparty import mpd

class MpdHandler(songretriever.MusicHandler):
    '''a simple handler for mpd music player'''
    NAME = 'MPD Music Handler'
    DESCRIPTION = 'Handler for mpd music player'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, main_window):
        songretriever.MusicHandler.__init__(self, main_window)

        self.host = "localhost"
        self.port = 6600

        self.reconnect()

    def reconnect(self):
        '''reconnect, only call if disconnected.
        return True if connected'''
        try:
            self.client = mpd.MPDClient()
            self.client.connect(self.host, self.port)
            return True
        except mpd.ConnectionError:
            return False
        except socket.error:
            return False

    def is_running(self):
        '''returns True if the player is running'''
        try:
            self.client.status()
            return True
        except mpd.ConnectionError:
            return self.reconnect()

    def is_playing(self):
        '''returns True if the player is playing a song'''
        if not self.is_running():
            return False

        status = self.client.status()

        return status.get('state', None) == 'play'

    def get_current_song(self):
        '''returns the current song or None if no song is playing'''
        if not self.is_running() or not self.is_playing():
            return None

        info = self.client.currentsong()

        return songretriever.Song(info.get('artist', '?'),
                info.get('album', '?'),
                info.get('title', '?'),
                info.get('file', '?'))


