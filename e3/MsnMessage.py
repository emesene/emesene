import urllib

import common

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

    def format(self):
        '''return the message formated to send it through the socket'''
        if self.type == Message.TYPE_MESSAGE:
            return self._format_message()
        elif self.type == Message.TYPE_TYPING:
            return self._format_typing()
        elif self.type == Message.TYPE_P2P:
            return self._format_p2p()
        elif self.type == Message.TYPE_NUDGE:
            return self._format_nudge()
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
        # TODO: dx will do it
        return ''

    def _format_nudge(self):
        '''format a message like a TYPE_NUDGE'''
        output = 'MIME-Version: 1.0\r\n'
        output += 'Content-Type: text/x-msnmsgr-datacast\r\n\r\n'
        output += 'ID: 1\r\n\r\n'

        return output

    @classmethod
    def parse(cls, command):
        '''parse a message from a command object and return a Message object'''
        parts = command.payload.split('\r\n\r\n')

        if len(parts) == 1:
            head = parts[0]
            body = ''
        elif len(parts) == 2:
            (head, body) = parts
        elif len(parts) == 3:
            head = parts[0]
            body = parts[1]
        else:
            print 'unknown message:', repr(parts)
            # (?)
            head = ''
            body = ''

        type_ = common.get_value_between(head, 'Content-Type: ', '\r\n')

        # if content type is the last line we should not use \r\n as terminator
        if type_ == '' and 'Content-Type: ' in head:
            type_ = head.split('Content-Type: ')[1]

        style = None
        
        if type_.startswith('text/plain'):
            mtype = Message.TYPE_MESSAGE
            font = urllib.unquote(common.get_value_between(head, 'FN=', ';'))
            effects = common.get_value_between(head, 'EF=', ';')
            color = common.get_value_between(head, 'CO=', ';', '000000')

            if color.startswith('#'):
                color = color[1:]

            if len(color) < 3:
                color += '0' * (3 - len(color))
            elif len(color) > 3 and len(color) < 6:
                color += '0' * (6 - len(color))

            color = Color.from_hex(color[4:6] + color[2:4] + color[0:2])

            bold = 'B' in effects
            italic = 'I' in effects
            underline = 'U' in effects
            strike = 'S' in effects

            style = Style(font, color, bold, italic, underline, strike)
        elif type_ == 'text/x-msmsgscontrol':
            mtype = Message.TYPE_TYPING
        elif type_ == 'application/x-msnmsgrp2p':
            mtype = Message.TYPE_P2P
        elif type_ == 'text/x-msnmsgr-datacast' and body == 'ID: 1':
            mtype = Message.TYPE_NUDGE
        else:
            mtype = Message.TYPE_UNK

        return cls(mtype, body, command.tid, style)

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

