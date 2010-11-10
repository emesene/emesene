import urllib

import common
import e3

class Message(e3.Message):
    '''a class that represent a msn message'''

    def __init__(self, type_, body, account, style=None, dest=''):
        if not isinstance(body, basestring):
            body = ''
        e3.Message.__init__(self, type_, body.encode('utf-8'), account, style)

        self.dest = dest
        if style:
            self.style = Style(style.font, style.color, style.bold,
                style.italic, style.underline, style.strike)
        else:
            self.style = Style()

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
        output = ('MIME-Version: 1.0\r\n'
            'Content-Type: application/x-msnmsgrp2p\r\n'
            'P2P-Src: %s\r\n'  # WLM 9.0/14.0
            'P2P-Dest: %s\r\n\r\n%s')
        return output % (self.account, self.dest, self.body)

    def _format_nudge(self):
        '''format a message like a TYPE_NUDGE'''
        output = 'MIME-Version: 1.0\r\n'
        output += 'Content-Type: text/x-msnmsgr-datacast\r\n\r\n'
        output += 'ID: 1\r\n\r\n'

        return output

    @classmethod
    def parse(cls, command):
        '''parse a message from a command object and return a Message object'''
        parts = command.payload.split('\r\n\r\n', 1)
        if len(parts) == 1:
            head = parts[0]
            body = ''
        elif len(parts) == 2:
            (head, body) = parts

        type_ = common.get_value_between(head, 'Content-Type: ', '\r\n')

        # if content type is the last line we should not use \r\n as terminator
        if type_ == '' and 'Content-Type: ' in head:
            type_ = head.split('Content-Type: ')[1]

        style = None
        dest = ''

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

            color = e3.Color.from_hex(color[4:6] + color[2:4] + color[0:2])

            bold = 'B' in effects
            italic = 'I' in effects
            underline = 'U' in effects
            strike = 'S' in effects

            style = Style(font, color, bold, italic, underline, strike)
        elif type_ == 'text/x-msmsgscontrol':
            mtype = Message.TYPE_TYPING
        elif type_ == 'application/x-msnmsgrp2p':
            mtype = Message.TYPE_P2P
            dest = common.get_value_between(head, 'P2P-Dest: ', '\r\n')
        elif type_ == 'text/x-msnmsgr-datacast' and body.strip() == 'ID: 1':
            mtype = Message.TYPE_NUDGE
        else:
            mtype = Message.TYPE_UNK

        return cls(mtype, body, command.tid, style, dest)

class Style(e3.Style):
    '''a class that represents the style of a message'''

    def __init__(self, font='Arial', color=None, bold=False, italic=False,
        underline=False, strike=False):
        e3.Style.__init__(self, font, color, bold, italic,
            underline, strike)

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

        color = self.color.to_hex()
        color = color[4:6] + color[2:4] + color[0:2]

        return 'FN=%s; EF=%s; CO=%s; PF=0; RL=0' % (urllib.quote(self.font),
            effects, color)

