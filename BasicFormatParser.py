import copy
import xml.parsers.expat

class BasicFormatParser(object):
    '''a class that parses basic format tags:

    b, i, u, s
    '''

    def __init__(self, text):
        '''constructor'''
        self.parser = xml.parsers.expat.ParserCreate()
        self.parser.buffer_text = True

        self.tag_status = {}
        self.tag_status['b'] = False
        self.tag_status['i'] = False
        self.tag_status['u'] = False
        self.tag_status['s'] = False

        self.result = []

        self.parser.StartElementHandler = self.start_element
        self.parser.EndElementHandler = self.end_element
        self.parser.CharacterDataHandler = self.char_data
        self.parser.Parse('<span>' + text + '</span>')

    def start_element(self, name, attrs):
        '''Start xml element handler'''
        if name in self.tag_status:
            self.tag_status[name] = True

    def end_element(self, name):
        '''End xml element handler'''
        if name in self.tag_status:
            self.tag_status[name] = False

    def char_data(self, data):
        '''Char xml element handler.
        buffer_text is enabled, so this is the whole text element'''

        format = copy.copy(self.tag_status)
        format['data'] = data
        self.result.append(format)


if __name__ == '__main__':
    import pprint

    def test():
        pprint.pprint(BasicFormatParser('<span><b>unnested</b> <i>test</i> <u>!</u><s>!</s></span>').result)
        pprint.pprint(BasicFormatParser('<span><b>simple nested <i>test</i> <u>!</u></b></span>').result)
        pprint.pprint(BasicFormatParser('<span><b>complex <i>nested <u>test <s>!</s></u></i></b></span>').result)

    test()
