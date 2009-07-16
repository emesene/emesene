import extension
from interfaces.bar import IBar
import plugin_base

class IFoo:
    '''this can extend bar'''
    def do_foo(self):
        '''you must implement it!'''
        raise NotImplementedError


@plugin_base.implements(IBar)
class Bar:
    print 'bar is parsed'
    def __init__(self):
        assert extension.is_implementation(Bar, IBar)
        print 'bar is running'
    def bar(self):
        print 'bar will bar'
        print ' # extension can be extended! ;)'
        for extra in extension.get_extensions('foo'):
            try:
                print 'foo', extra
                extra.do_foo()
            except Exception, reason:
                print 'NW', extra, reason

