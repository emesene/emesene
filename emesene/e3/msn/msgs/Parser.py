# -*- coding: utf-8 -*-
'''parse the xml files from the server'''

#   This file is part of emesene.
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

import time
import email
import xml.parsers.expat
from datetime import datetime

import e3.msn.common

months_names = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')
months_name_number = dict(zip(months_names,range(1,13)))

def string2datetime(datestring):
    '''returns a datestring from string'''
    datestring = datestring.replace('.', ' ').replace(':', ' ')
    (day, month, year, hours,
     minutes, seconds, microseconds) = datestring.split(' ')[:7]

    return datetime(int(year), months_name_number[month], int(day),
                 int(hours), int(minutes), int(seconds), int(microseconds))

class MailDataParser(object):
    '''Parse Mail Xml'''
    def __init__(self, xml_raw):
        '''init parser and setup handlers'''
        self.parser = xml.parsers.expat.ParserCreate()
        self.parser.buffer_text = True
        self.parser.returns_unicode = False

        self.mail_data = {}
        self.oims = []

        position = {}

        position['I'] = 'inbox_total'
        position['IU'] = 'inbox_unread'

        position['O'] = 'other_total'
        position['OU'] = 'other_unread'

        position['QTM'] = 'qtm'
        position['QNM'] = 'qnm'

        self._position = position

        message_pos = {}
        message_pos['I'] = 'id'
        message_pos['E'] = 'sender'
        message_pos['RT'] = 'timestamp'

        self.in_message = False

        self._message_pos = message_pos

        self.current_pos = ''

        self._oim = {}

        #connect handlers
        self.parser.StartElementHandler = self.start_element
        self.parser.EndElementHandler = self.end_element
        self.parser.CharacterDataHandler = self.char_data
        self.parser.Parse(xml_raw)
        del(xml_raw)

    def start_element(self, name, attrs):
        '''Start xml element handler'''
        self.current_pos = name
        if name == 'M':
            self.in_message = True

    def end_element(self, name):
        '''End xml element handler'''
        if name == 'M':
            self.in_message = False
            self.oims.append(self._oim)
            self._oim = {}

    def char_data(self, data):
        '''Char xml element handler'''
        if self.in_message and self.current_pos in self._message_pos:
            position = self._message_pos[self.current_pos]
            self._oim.update({position:data})

        elif self.current_pos in self._position:
            position = self._position[self.current_pos]
            self.mail_data[position] = int(data)

class OimParser(object):
    def __init__(self, response):
        '''handle the response'''
        body = e3.msn.common.get_value_between(response,
                                 '<GetMessageResult>',
                                 '</GetMessageResult>')

        oim = email.message_from_string(body)

        nick, mail = self.parse_from(oim.get('From'))
        message = oim.get_payload().decode('base64')

        #sent_date = email.Utils.parsedate_tz(oim.get('Date'))
        #sent_date = time.localtime(email.Utils.mktime_tz(sent_date))

        # datetime UTC with microseconds
        sent_date = string2datetime(oim.get('X-OriginalArrivalTime'))

        self.nick = nick
        self.mail = mail
        self.date = sent_date
        self.message = message

    def parse_from(self, oim_from):
        '''Parse encoded from'''
        data = oim_from.split('?')
        # oooohh shi-
        if len(data) < 3:
            mail = oim_from.replace('&lt;', '').replace('&gt;', '')
            return (mail, mail)

        if data[2] == 'B':
            nick = data[3].decode('base64').decode(data[1])
            mail = data[4][6:][:-4]
        elif data[2] == 'Q':
            #Quoted Messsage.. TODO
            nick = address = 'FIXME'
        return (nick, mail)
