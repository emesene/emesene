'''all the parsers for the adium themes'''

import xml.parsers.expat

class Plist(object):
    '''a class to parse the Info.plist file'''

    def __init__(self, file_):
        self.parser = xml.parsers.expat.ParserCreate()
        self.parser.buffer_text = True
        self.parser.returns_unicode = False

        self.info = {}
        self.current_key = None
        self.is_key = False
        self.is_value = False

        #connect handlers
        self.parser.StartElementHandler = self.start_element
        self.parser.EndElementHandler = self.end_element
        self.parser.CharacterDataHandler = self.char_data
        self.parser.ParseFile(file_)

    def start_element(self, name, attrs):
        '''Start xml element handler'''
        if name == 'key':
            self.is_key = True
        elif name in ('string', 'integer'):
            self.is_value = True
        elif name == 'true':
            self.info[self.current_key] = True
        elif name == 'false':
            self.info[self.current_key] = True

    def end_element(self, name):
        '''End xml element handler'''
        if name == 'key':
            self.is_key = False
        elif name in ('string', 'integer', 'true', 'false'):
            self.is_value = False

    def char_data(self, data):
        '''Char xml element handler'''
        if self.is_key:
            self.current_key = data
        elif self.is_value:
            self.info[self.current_key] = data

if __name__ == '__main__':
    def test():
        '''test the module'''
        import pprint
        info = Plist(file(
            'themes/renkoo.AdiumMessageStyle/Contents/Info.plist')).info
        pprint.pprint(info)
        info = Plist(file(
            'themes/Modern Bubbling.AdiumMessageStyle/Contents/Info.plist')
            ).info
        pprint.pprint(info)
        info = Plist(file(
            'themes/renkooNaked.AdiumMessageStyle/Contents/Info.plist')).info
        pprint.pprint(info)

    test()
