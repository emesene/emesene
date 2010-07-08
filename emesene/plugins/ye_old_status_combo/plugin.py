import extension
from plugin_base import PluginBase

import StatusCombo

class Plugin(PluginBase):
    def __init__(self):
        PluginBase.__init__(self)

    def start(self, session):
        self.extensions_register()

    def stop(self):
        pass

    def extensions_register(self):
        extension.register('below userlist', StatusCombo.StatusCombo)
