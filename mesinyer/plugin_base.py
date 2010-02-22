'''
Plugin base class.

It will be inherited by every plugin.

'''

class PluginBase(object):
    '''base class for plugins'''
    _description = "No description"
    _authors = {}
    def __init__(self):
        self._started = False
        self._configure = None

    def start(self, session):
        '''method to start the plugin'''
        raise NotImplementedError()

    def is_active(self):
        '''returns True if the plugin is activated'''
        return self._started

    def stop(self):
        '''method to stop the plugin'''
        raise NotImplementedError()

    def config(self, session):
        '''method to config the plugin'''
        raise NotImplementedError()

    def category_register(self):
        '''It's a placeholder. Can be safely called even if not implemented
        (that means the plugin is old-style)'''
        return False

    def extension_register(self):
        '''It's a placeholder. Can be safely called even if not implemented
        (that means the plugin is old-style)'''
        return False
