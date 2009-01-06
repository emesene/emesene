class Message(object):
    '''a class that represent a msn message'''
    (TYPE_MESSAGE, TYPE_TYPING, TYPE_NUDGE, TYPE_P2P, TYPE_UNK) = range(5)

    def __init__(self, type_, body, account, style=None):
        self.type = type_
        self.body = body
        self.account = account

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
        underline=False, strike=False):
        self.font = font

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

