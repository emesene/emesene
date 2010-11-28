import extension

from plugin_base import PluginBase

CATEGORY = 'listening to'

class Plugin(PluginBase):
    def __init__(self):
        PluginBase.__init__(self)

        self.session = None
        self.running = False

        self.player = None

    def stop(self):
        '''stop the plugin'''
        self.session = None
        self.running = False
        return True

    def start(self, session):
        '''start the plugin'''
        self.session = session

        self.category_register()
        self.extensions_register()

        self.running = True

        return True

    def config(self, session):
        '''config the plugin'''
        category = extension.get_category(CATEGORY)
        player = category.get_instance()

        if player != None:
            player.preferences()

        return True

    def category_register(self):
        import songretriever
        extension.category_register(CATEGORY, songretriever.MusicHandler, songretriever.MusicHandler, True)

        return True

    def extensions_register(self):
        import handler_amarok2
        import handler_audacious2
        import handler_banshee
        import handler_exaile
        import handler_gmusicbrowser
        import handler_guayadeque
        import handler_lastfm
        import handler_moc
        import handler_mpd
        import handler_mpris
        import handler_rhythmbox

        try:
            import handler_xmms2
            XMMSCLIENT = True
        except ImportError:
            XMMSCLIENT = False

        extension.register(CATEGORY, handler_amarok2.Amarok2Handler)
        extension.register(CATEGORY, handler_audacious2.Audacious2Handler)
        extension.register(CATEGORY, handler_banshee.BansheeHandler)
        extension.register(CATEGORY, handler_exaile.ExaileHandler)
        extension.register(CATEGORY, handler_gmusicbrowser.GMusicBrowserHandler)
        extension.register(CATEGORY, handler_guayadeque.GuayadequeHandler)
        extension.register(CATEGORY, handler_lastfm.LastfmHandler)
        extension.register(CATEGORY, handler_moc.MocHandler)
        extension.register(CATEGORY, handler_mpd.MpdHandler)
        extension.register(CATEGORY, handler_mpris.MprisHandler)
        extension.register(CATEGORY, handler_rhythmbox.RhythmboxHandler)

        if XMMSCLIENT:
            extension.register(CATEGORY, handler_xmms2.Xmms2Handler)

        handler_id = self.session.config.d_extensions.get(CATEGORY, None)

        if handler_id is None:
            handler_id = extension._get_class_name(handler_rhythmbox.RhythmboxHandler)
            self.session.config.d_extensions.get(CATEGORY, handler_id)

        extension.set_default_by_id(CATEGORY, handler_id)

