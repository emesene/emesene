import songretriever

import socket
from thirdparty import mpd

class MpdMusicHandlerConfig(songretriever.BaseMusicHandlerConfig):
    '''the panel to display/modify the config related to
    the 'listening to' extension for the mpd music handler'''

    def __init__(self, config):
        '''constructor'''
        songretriever.BaseMusicHandlerConfig.__init__(self, config)

        self.append_entry_default('Host', 'config.mpd_host', config.mpd_host)
        self.append_entry_default('Port', 'config.mpd_port', config.mpd_port)

class MpdHandler(songretriever.MusicHandler):
    '''a simple handler for mpd music player'''
    NAME = 'MPD'
    DESCRIPTION = 'Handler for mpd music player'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, main_window):
        songretriever.MusicHandler.__init__(self, main_window)

        # Use our specific config dialog
        self.config = main_window.session.config

        # set default values if not set
        self.config.get_or_set("mpd_host", "localhost")
        self.config.get_or_set("mpd_port", "6600")

        self.config_dialog_class = MpdMusicHandlerConfig

        self.client = None

        self.reconnect()

    def reconnect(self):
        '''reconnect, only call if disconnected.
        return True if connected'''
        try:
            self.client = mpd.MPDClient()
            self.client.connect(self.config.mpd_host,
                    int(self.config.mpd_port))
            return True
        except Exception as error:
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
            info.get('album', '?'), info.get('title', '?'),
            info.get('file', '?'))


