# -*- coding: utf-8 -*-

#    This file is part of emesene.
#
#    emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
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
    '''a class that represent a msn message'''
    (TYPE_MESSAGE, TYPE_TYPING, TYPE_NUDGE, TYPE_P2P, TYPE_UNK,
     TYPE_FLNMSG, TYPE_OLDMSG) = range(7)

    def __init__(self, type_, body, account, style=None, timestamp=None,
                 display_name=None):
        self.type = type_
        self.body = body
        self.account = account
        self.timestamp = timestamp
        self.display_name = display_name

        if style is not None:
            self.style = style
        else:
            self.style = Style()

    def __str__(self):
        '''return a string representation of a message'''
        return '<message from="%s" style="%s" type="%i">' % (self.account,
            str(self.style), self.type)

class Style(object):
    '''a class that represents the style of a message'''

    def __init__(self, font='Arial', color=None, bold=False, italic=False,
        underline=False, strike=False, size_=None):
        self.font = font
        self.size = size_

        if color is not None:
            self.color = color
        else:
            self.color = Color.from_hex('#000000')

        self.bold = bold
        self.italic = italic
        self.underline = underline
        self.strike = strike

    def __str__(self):
        '''return a string representation of the object'''
        return '<style font="%s" color="%s" b="%s" i="%s" u="%s" s="%s">' \
            % (self.font, str(self.color), self.bold, self.italic,
                self.underline, self.strike)

    def to_css(self):
        '''return a string representing the current style as CSS rules'''
        style = ''

        if self.font is not None:
            style += 'font-family: %s; ' % self.font

        if self.size is not None:
            style += 'font-size: %spt; ' % str(self.size)

        if self.color is not None:
            style += 'color: #%s; ' % self.color.to_hex()

        if self.bold:
            style += 'font-weight: bold; '

        if self.italic:
            style += 'font-style: italic; '

        if self.underline:
            style += 'text-decoration: underline; '

        if self.strike:
            style += 'text-decoration: line-through;'

        return style

class Color(object):
    '''a class representing a RGBA color'''

    def __init__(self, red=0, green=0, blue=0, alpha=255):
        '''class contructor'''

        self.red = red
        self.green = green
        self.blue = blue
        self.alpha = alpha

    def to_hex(self):
        '''return a hexa representation of the color, usefull for pango'''

        red = self.red
        if red > 255:
            red /= 256

        green = self.green
        if green > 255:
            green /= 256

        blue = self.blue
        if blue > 255:
            blue /= 256

        red = hex(red)[2:][-2:]
        green = hex(green)[2:][-2:]
        blue = hex(blue)[2:][-2:]

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

    def __iter__(self):
        '''return an iterator'''
        yield self.red
        yield self.green
        yield self.blue

    @classmethod
    def from_hex(cls, hex_str):
        '''return a color from an hexadecimal representation of type
        #rrggbb, rrggbb, #rgb, rgb'''

        if hex_str.startswith('#'):
            if hex_str == '#0': #some MSN clients define black as simply '#0'
                hex_str = '#000000'

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
