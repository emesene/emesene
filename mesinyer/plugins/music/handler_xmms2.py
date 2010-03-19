import songretriever
from thirdparty import xmmsclient

class Xmms2Handler(object):
    '''a simple handler for xmms2 music player'''

    def __init__(self):
        self.client = None
        self.reconnect()

    def reconnect(self):
        '''reconnect, only call if disconnected.
        return True if connected'''
        try:
            self.client = xmmsclient.XMMS("emesene2")
            self.client.connect(None)
            return True
        except IOError:
            return False

    def is_running(self):
        '''returns True if the player is running'''
        if self.client != None:
            result = self.client.playback_current_id()
            result.wait()
            if result.iserror():
                return False
            return True
        else:
            return self.reconnect()

    def is_playing(self):
        '''returns True if the player is playing a song'''
        if not self.is_running():
            return False

        result = self.client.playback_current_id()
        result.wait()
        if result.iserror():
            return False    
        if result.value() == 0:
            return False
        return True

    def get_current_song(self):
        '''returns the current song or None if no song is playing'''
        if not self.is_running() or not self.is_playing():
            return None

        result = self.client.playback_current_id()
        result.wait()
        if result.iserror():
            return None
        id_song = result.value()

        result = self.client.medialib_get_info(id_song)
        result.wait()
        if result.iserror():
            return None
        info = result.value()

        return songretriever.Song(info["artist"],
                    info["album"], info["title"])

songretriever.register('xmms2', Xmms2Handler)

