import extension
from plugin_base import PluginBase

import ExtensionsDownloader

class Plugin(PluginBase):
    def __init__(self):
        PluginBase.__init__(self)

    def start(self, session):
        self.session = session
        self.extensions_register()
        self.instance = ExtensionsDownloader.ExtensionsDownloader(self.session)
        self.instance.add_to_main_list()

    def stop(self):
        self.instance.remove_from_main_list()

    def extensions_register(self):
        extension.register('extension downloader', ExtensionsDownloader.ExtensionsDownloader)
