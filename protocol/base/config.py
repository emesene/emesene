import ConfigParser

class Undefined(object):
    '''a class that represents a undefined value'''
    pass

class Invalid(object):
    '''a class that represents an invalid value'''
    pass

class Config(dict):
    '''a class that contains all the configurations of the user,
    the config keys follow a convention, all the names start with
    the type they have, for example:
    b_foo is boolean
    i_bar is int
    f_baz is float
    when you try to get an attribute, if it doesn't exist it will
    return Undefined, if the parse fails it will return Invalid,
    doing this allows you to get values and don't fill the code
    with try/excepts and validations, if the name doesn't contains
    one of those prefixes, it will return the value as string'''

    def __init__(self, **kwargs):
        '''constructor'''
        dict.__init__(self)
        self.__dict__ = kwargs

    def __getattr__(self, name):
        if name in self.__dict__:
            value = self.__dict__[name]

            try:
                if value.startswith('b_'):
                    return bool(value)
                elif value.startswith('i_'):
                    return (value)
                elif value.startswith('f_'):
                    return (value)
                else:
                    return value
            except ValueError:
                return Invalid
        else:
            return Undefined


    def load(self, path, clear=False, section='DEFAULT'):
        '''load the config file from path, clear old values if
        clear is set to True'''
        parser = ConfigParser.SafeConfigParser()
        files = parser.read(path)

        if len(files):
            for (name, value) in files[0].items(section):
                print name, value

        if clear:
            self.__dict__ = {}

    def save(self, path, section='DEFAULT'):
        '''save to a config file'''
        parser = ConfigParser.SafeConfigParser()

        for (key, value) in self.__dict__.iteritems():
            parser.set(section, key, str(value))
        
        parser.write(file(path, 'w'))

def test():
    '''test the implementation'''
    config = Config(foo=4, bar=False, baz="hello!", argh=2.3)
    config.save('test.ini')

if __name__ == '__main__':
    test()
