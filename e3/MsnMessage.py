import urllib

class Message(object):
    '''a class that represent a msn message'''
    (TYPE_MESSAGE, TYPE_TYPING, TYPE_P2P, TYPE_UNK) = range(4)

    def __init__(self, type_, body, account, style=None):
        self.type = type_
        self.body = body
        self.account = account
        self.style = style

    def __str__(self):
        '''return a string representation of a message'''
        return '<message from="%s" style="%s" type="%i">' % (self.account, 
            str(self.style), self.type)

    def format(self):
        '''return the message formated to send it through the socket'''
        if self.type == Message.TYPE_MESSAGE:
            return self._format_message()
        elif self.type == Message.TYPE_TYPING:
            return self._format_typing()
        elif self.type == Message.TYPE_P2P:
            return self._format_p2p()
        else:
            raise ValueError('Invalid type formating message')

    def _format_message(self):
        '''format a message like a TYPE_MESSAGE'''
        output = 'MIME-Version: 1.0\r\n'
        output += 'Content-Type: text/plain; charset=UTF-8\r\n'
        output += 'X-MMS-IM-Format: %s\r\n\r\n%s'

        return output % (self.style.format(), self.body)

    def _format_typing(self):
        '''format a message like a TYPE_TYPING'''
        output = 'MIME-Version: 1.0\r\n'
        output += 'Content-Type: text/x-msmsgscontrol\r\n'
        output += 'TypingUser: %s\r\n\r\n'

        return output % (self.account,)

    def _format_p2p(self):
        '''format a message like a TYPE_P2P'''
        return ''

    @classmethod
    def parse(cls, command):
        '''parse a message from a command object and return a Message object'''
        (head, body) = command.payload.split('\r\n\r\n')

        type_ = get_value_between(head, 'Content-Type: ', '\r\n')
        style = None
        
        if type_.startswith('text/plain'):
            mtype = Message.TYPE_MESSAGE
            font = urllib.unquote(get_value_between(head, 'FN=', ';'))
            effects = get_value_between(head, 'EF=', ';')
            color = get_value_between(head, 'CO=', ';', '000000')

            if color.startswith('#'):
                color = color[1:]

            if len(color) < 3:
                color += '0' * 3 - len(color)
            elif len(color) > 3 and len(color) < 6:
                color += '0' * 6 - len(color)

            color = Color.from_hex(color)

            bold = 'B' in effects
            italic = 'I' in effects
            underline = 'U' in effects
            strike = 'S' in effects

            style = Style(font, color, bold, italic, underline, strike)
        elif type_ == 'text/x-msmsgscontrol':
            mtype = Message.TYPE_TYPING
        elif type_ == 'application/x-msnmsgrp2p':
            mtype = Message.TYPE_P2P
        else:
            mtype = Message.TYPE_UNK

        return cls(mtype, body, command.tid, style)

class Style(object):
    '''a class that represents the style of a message'''

    def __init__(self, font, color, bold=False, italic=False, underline=False, 
        strike=False):
        self.font = font
        self.color = color
        self.bold = bold
        self.italic = italic
        self.underline = underline
        self.strike = strike

    def __str__(self):
        '''return a string representation of the object'''
        return '<style font="%s" color="%s" b="%s" i="%s" u="%s" s="%s">' \
            % (self.font, str(self.color), self.bold, self.italic, 
                self.underline, self.strike)

    def format(self):
        '''format the object to be used on a message'''

        effects = ''

        if self.bold:
            effects += 'B'

        if self.italic:
            effects += 'I'

        if self.underline:
            effects += 'U'

        if self.strike:
            effects += 'S'

        return 'FN=%s; EF=%s; CO=%s; PF=0;RL=0' % (urllib.quote(self.font),
            effects, self.color.to_hex())

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

def get_value_between(string_, start, stop, default=''):
    '''get the value of string_ between start and stop, return default if
    the value cant be extracted. If multiple time appear start on string_
    just the first will be used, if start or stop are not found default will
    be returned'''
    parts = string_.split(start, 1)

    if len(parts) != 2:
        return default

    parts = parts[1].split(stop, 1)
    
    if len(parts) != 2:
        return default

    return parts[0]
