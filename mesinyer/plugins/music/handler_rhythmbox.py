import songretriever

import DBusBase

SHELL_NAME = 'org.gnome.Rhythmbox.Shell'
SHELL_PATH = '/org/gnome/Rhythmbox/Shell'

class RhythmboxHandler(DBusBase.DBusBase):
    '''Handler for rhythmbox'''

    def __init__(self, iface_name = 'org.gnome.Rhythmbox',
                 iface_path='/org/gnome/Rhythmbox/Player'):
        DBusBase.DBusBase.__init__(self, iface_name, iface_path)

    def reconnect(self):
        '''method to attemp a reconnection, via dbus, this is only
        called if the bus object is not initialized'''
        if DBusBase.DBusBase.reconnect(self):
            rbshellobj   = self.bus.get_object(self.iface_name, SHELL_PATH)
            self.rbshell = self.module.Interface(rbshellobj, SHELL_NAME)
            return True

        return False

    def is_playing(self):
        '''Returns True if a song is being played'''
        if self.is_running():
            return bool(self.iface.getPlaying())

        return False

    def get_current_song(self):
        '''Returns the current song in the correct format'''
        if self.is_playing():
            uri  = self.iface.getPlayingUri()
            song = self.rbshell.getSongProperties(uri)

            return songretriever.Song(song['artist'],
                                      song['album'],
                                      song['title'])

songretriever.register('rhythmbox', RhythmboxHandler())
