import urllib

import ConfigParser

class Config(dict):
    '''a class that contains all the configurations of the user,
    the config keys follow a convention, all the names start with
    the type they have, for example:
    b_foo is boolean
    i_bar is int
    f_baz is float
    l_lala is list
    when you try to get an attribute, if it doesn't exist it will
    return None, if the parse fails the value will not be set,
    doing this allows you to get values and don't fill the code
    with try/excepts and validations, if the name doesn't contains
    one of those prefixes, it will return the value as string'''

    def __init__(self, **kwargs):
        '''constructor'''
        dict.__init__(self)
        self.__dict__ = kwargs

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        else:
            return None

    def load(self, path, clear=False, section='DEFAULT'):
        '''load the config file from path, clear old values if
        clear is set to True'''
        parser = ConfigParser.SafeConfigParser()
        parser.read(path)

        if clear:
            self.__dict__ = {}

        for (name, value) in parser.items(section):
            try:
                if name.startswith('b_'):
                    value = bool(value)
                elif name.startswith('i_'):
                    value = int(value)
                elif name.startswith('f_'):
                    value = float(value)
                elif name.startswith('l_'):
                    value = [urllib.unquote(x.replace('%%', '%')) 
                        for x in value.split(':')]

                setattr(self, name, value)
            except ValueError:
                print 'invalid config value', name, value

    def save(self, path, section='DEFAULT'):
        '''save to a config file'''
        parser = ConfigParser.SafeConfigParser()

        for (key, value) in self.__dict__.iteritems():
            if key.startswith('l_'):
                parser.set(section, key, 
                    ':'.join([urllib.quote(str(x)).replace('%', '%%') 
                        for x in value]))
            else:
                parser.set(section, key, str(value))
        
        parser.write(file(path, 'w'))


def test():
    '''test the implementation'''
    config = Config(i_foo=4, b_bar=False, baz="hello!", f_argh=2.3,
        l_lala=['sar:asa', 4, False, 2.3, None])
    config.save('test.ini')

    c = Config()
    c.load('test.ini')

    print c.i_foo, type(c.i_foo)
    print c.b_bar, type(c.b_bar)
    print c.baz, type(c.baz)
    print c.f_argh, type(c.f_argh)
    print c.l_lala, type(c.l_lala)
    # inexisting values
    print c.inexisting, type(c.inexisting)

    return c

if __name__ == '__main__':
    test()
