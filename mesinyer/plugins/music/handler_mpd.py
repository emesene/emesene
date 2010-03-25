import songretriever

import socket
from thirdparty import mpd

class MpdMusicHandlerConfig(songretriever.BaseMusicHandlerConfig):
    '''the panel to display/modify the config related to
    the 'listening to' extension for the MPRIS Music Handler'''

    def __init__(self):
        '''constructor'''
        songretriever.BaseMusicHandlerConfig.__init__(self)

        self.host_default = "localhost"
        # This should be loaded from a config option
        self.host = self.host_default
        self.append_entry_default('Host', 'host', self.host_default)

        self.port_default = "6600"
        # This should be loaded from a config option
        self.port = self.port_default
        self.append_entry_default('Port', 'port', self.port_default)

class MpdHandler(songretriever.MusicHandler):
    '''a simple handler for mpd music player'''
    NAME = 'MPD'
    DESCRIPTION = 'Handler for mpd music player'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, main_window = None):
        songretriever.MusicHandler.__init__(self, main_window)

        # Use our specific config dialog
        self.config = MpdMusicHandlerConfig()

        self.client = None

        self.reconnect()

    def reconnect(self):
        '''reconnect, only call if disconnected.
        return True if connected'''
        try:
            self.client = mpd.MPDClient()
            self.client.connect(self.config.host, self.config.port)
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


