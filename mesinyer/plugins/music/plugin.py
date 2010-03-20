import gobject

import extension
import songretriever
import Preferences

from plugin_base import PluginBase

import handler_amarok2
import handler_audacious2
import handler_banshee
import handler_gmusicbrowser
import handler_guayadeque
import handler_lastfm
import handler_moc
import handler_mpd
import handler_rhythmbox
import handler_xmms2

CATEGORY = 'listening to'

class Plugin(PluginBase):
    def __init__(self):
        PluginBase.__init__(self)
        self.session = None

    def start(self, session):
        '''start the plugin'''
        self.session = session
        self.extensions_register()
        return True

    def config(self, session):
        '''config the plugin'''
        Preferences.Preferences(self._on_config, self.player,
                self.format).show()

    def _on_config(self, status, player, format):
        '''callback for the config dialog'''
        if status:
            self.player = player
            self.format = format

    def extensions_register(self):
        extension.category_register(CATEGORY, songretriever.MusicHandler)

        extension.register(CATEGORY, handler_amarok2.Amarok2Handler)
        extension.register(CATEGORY, handler_audacious2.Audacious2Handler)
        extension.register(CATEGORY, handler_banshee.BansheeHandler)
        extension.register(CATEGORY, handler_gmusicbrowser.GMusicBrowserHandler)
        extension.register(CATEGORY, handler_guayadeque.GuayadequeHandler)
        extension.register(CATEGORY, handler_lastfm.LastfmHandler)
        extension.register(CATEGORY, handler_moc.MocHandler)
        extension.register(CATEGORY, handler_mpd.MpdHandler)
        extension.register(CATEGORY, handler_rhythmbox.RhythmboxHandler)
        extension.register(CATEGORY, handler_xmms2.Xmms2Handler)

        extension.set_default(CATEGORY, handler_mpd.MpdHandler)


