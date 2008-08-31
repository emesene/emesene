# -*- coding: utf-8 -*-
'''a module that defines a message object'''

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

class Message(object):
    '''this class defines an object that holds a message and information
    about that message'''

    def __init__(self, sender, body=None):
        '''constructor, sender is a contact object, 
        body is a list of objects that define a format
        all messages should be sent through a conversation
        thats why they dont have receivers'''

        self.sender = sender

        if body is None:
            self.body = []
        else:
            self.body = body

class Text(object):
    '''this class defines a chunck of text with some format'''

    def __init__(self, text, font=None, size=10, 
        fg=None, bg=None, bold=False, italic=False, 
        underline=False, strike=False, fg_end=None, bg_end=None):
        '''constructor, fg* and bg* are Color objects, *_end
        are used when the text has a transition between two colors'''

        self.text = text
        self.font = font
        self.size = size
        self.fg = fg
        self.bg = bg
        self.bold = bold
        self.italic = italic
        self.underline = underline
        self.strike = strike

        self.fg_end = fg_end
        self.bg_end = bg_end

class Color(object):
    '''a class representing a RGBA color'''

    def __init__(self, red=0, green=0, blue=0, alpha=0):
        '''class contructor'''

        self.red = red
        self.green = green
        self.blue = blue
        self.alpha = alpha

    def to_hex(self):
        '''return a hexa representation of the color, usefull for pango'''

        red = hex(self.red % 256)[2:]
        green = hex(self.green % 256)[2:]
        blue = hex(self.blue % 256)[2:]

        if len(red) == 1:
            red = '0' + red

        if len(green) == 1:
            green = '0' + green

        if len(blue) == 1:
            blue = '0' + blue

        return '%s%s%s' % (red, green, blue)

    def __str__(self):
        '''return a string representation of the object'''

        return '<Color red="%d" green="%d" blue="%d" alpha="%d">' % \
            (self.red, self.green, self.blue, self.alpha)

    @classmethod
    def from_hex(cls, hex_str):
        '''return a color from an hexadecimal representation of type
        #rrggbb, rrggbb, #rgb, rgb'''

        if hex_str.startswith('#'):
            if len(hex_str) not in (4, 7):
                raise ValueError('Invalid color format', hex_str)
            else:
                hex_str = hex_str[1:]
        elif len(hex_str) not in (3, 6):
            raise ValueError('Invalid color format', hex_str)
       
        if len(hex_str) == 3:
            hex_str = hex_str[0] * 2 + hex_str[1] * 2 + hex_str[2] * 2

        red = int(hex_str[0:2], 16)
        green = int(hex_str[2:4], 16)
        blue = int(hex_str[4:6], 16)

        return Color(red, green, blue)
