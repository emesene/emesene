'''
Plugin base class.

It will be inherited by every plugin.

'''

class PluginBase(object):
    _description = "No description"
    _authors = {}
    def __init__(self):
        self._started = False
        self._configure = None

    def start(self):
        raise NotImplementedError()

    def is_active(self):
        return self._started

    def stop(self):
        raise NotImplementedError()

    def category_register(self):
        #It's a placeholder. Can be safely called even if not implemented
        #(that means the plugin is old-style)
        return False

    def extension_register(self):
        #It's a placeholder. Can be safely called even if not implemented
        #(that means the plugin is old-style)
        return False
