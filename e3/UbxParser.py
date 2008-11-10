# -*- coding: utf-8 -*-
'''parse the UBX command payload'''

#   This file is part of emesene.
#
#    Emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    emesene is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with emesene; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import xml.parsers.expat

class UbxParser(object):
    '''Get the PSM and CurrentMedia from the UBX command payload'''

    def __init__(self, xml_raw):
        '''init parser and setup handlers'''

        self.parser = xml.parsers.expat.ParserCreate()
        self.parser.buffer_text = True
        self.parser.returns_unicode = False

        self.current_tag = ''
        
        # external attributes
        self.psm = ''
        self.current_media = ''

        self.parser.StartElementHandler = self.start_element
        self.parser.CharacterDataHandler = self.char_data
        self.parser.Parse(xml_raw)

    def start_element(self, name, attrs):
        '''Start xml element handler'''
        self.current_tag = name

    def char_data(self, data):
        '''Char xml element handler.
        buffer_text is enabled, so this is the whole text element'''
        if self.current_tag == 'PSM':
            self.psm = data
        elif self.current_tag == 'CurrentMedia':
            self.current_media = parse_current_media(data)

def parse_current_media(media):
    mhead = media.find('\\0Music\\01\\0')

    if mhead != -1:
        media = media[mhead+12:]
        margs = media.split('\\0')
        media = margs[0]

        for args in range(1, len(margs)):
            media = media.replace('{%s}' % (args-1), margs[args])
        return media
    else:
        return ''

if __name__ == '__main__':
    UbxParser(open("asd.xml", "r").read())
