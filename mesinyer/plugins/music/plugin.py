import gobject

import extension
import songretriever
import Preferences

from plugin_base import PluginBase

from gui.gtkui.AvatarManager import AvatarManager

#import handler_amarok2
#import handler_audacious2
#import handler_banshee
#import handler_gmusicbrowser
#import handler_guayadeque
import handler_mpd
#import handler_rhythmbox
#import handler_xmms2

class Plugin(PluginBase):
    def __init__(self):
        PluginBase.__init__(self)

    def start(self, session):
        '''start the plugin'''
        self.extensions_register()
        return True

    def extensions_register(self):
        extension.category_register('listening to', songretriever.MusicHandler)
        extension.register('listening to', handler_mpd.MpdHandler)


