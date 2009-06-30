import extension
from plugin_base import PluginBase
import bar

class Plugin(PluginBase):
    def __init__(self):
        PluginBase.__init__(self)

    def start(self):
        self.extensions_register()
        try:
            f = self.resource.get_resource('xyz')
        except Exception, reason:
            print 'error because of: ', reason

        try:
            for line in f.xreadlines():
                print line,
        except Exception, reason:
            print 'error in reading', reason


    def extensions_register(self):
        extension.register('bar', bar.Bar)
        extension.category_register('foo', bar.IFoo)
