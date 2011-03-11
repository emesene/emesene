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

import time
import xml.sax.saxutils

import e3

class MessageFormatter(object):
    '''a class that holds the state of a conversation and
    format the messages according to the state and the
    format provided

    tag list:

    %NICK%: the nick of the account
    %ALIAS%: the alias of the account
    %ACCOUNT%: the account identifier
    %DISPLAYNAME%: the alias if exist otherwise the nick if exist
        otherwise the account
    %TIME%: the time of the message
    %MESSAGE%: the message with format
    %RAWMESSAGE%: the message without format
    %STATUS%: the status of the account
    %PERSONALMESSAGE%: the personal message of the account
    %NL%: new line

    some basic formating is allowed as html tags:
    b: bold
    i: italic
    u: underline
    br: new line
    '''

    def __init__(self, contact, new_line='<br/>'):
        '''constructor'''

        # the contact who sends the messages
        self.contact = contact
        self.last_message_sender = None
        self.last_message_time = None
        self.new_line = new_line

        # default formats
        self.incoming = '<div class="message-incomming">'\
            '<b>%DISPLAYNAME%</b>:%NL%    %MESSAGE%%NL%</div>'
        self.outgoing = '<div class="message-outgoing">'\
            '<b>%DISPLAYNAME%</b>:%NL%    %MESSAGE%%NL%</div>'
        self.consecutive_incoming = '<div class="consecutive-incomming">'\
            '    %MESSAGE%%NL%</div>'
        self.consecutive_outgoing = '<div class="consecutive-outgoing">'\
            '    %MESSAGE%%NL%</div>'
        self.offline_incoming = \
            '<i>(offline message)</i><b>%DISPLAYNAME%</b>:%NL%    %MESSAGE%%NL%'
        self.information = '<i>%MESSAGE%</i>%NL%'
        self.error = \
            '<span style="color: #A52A2A;"><b>%MESSAGE%</b></span>%NL%'
        self.nudge = \
            '<i>%DISPLAYNAME% sent you a nudge!</i>%NL%'
        self.outgoing_nudge = '<i>'+_('You just sent a nudge!')+'</i>%NL%'
        self.history = '<div class="message-history">'\
            '<b>%TIME% %NICK%</b>: %MESSAGE%%NL%</div>'



    def format_message(self, template, message):
        '''format a message from the template, include new line
        if new_line is True'''
        template = template.replace('%NL%', self.new_line)
        template = template.replace('%MESSAGE%', message)

        return template

    def format_error(self, message):
        '''format an error message from the template, include new line
        if new_line is True'''
        self.last_message_sender = None
        return self.format_message(self.error, message)

    def format_information(self, message):
        '''format an info message from the template, include new line
        if new_line is True'''
        self.last_message_sender = None
        return self.format_message(self.information, message)

    def format_history(self, timestamp, nick, message):
        '''format a history message from the templage'''
        template = self.history
        template = template.replace('%NL%', self.new_line)
        template = template.replace('%NICK%', nick)
        template = template.replace('%TIME%', timestamp)
        template = template.replace('%MESSAGE%', message)
        return template

    def format(self, contact, message_type=None, timestamp_override=None):
        '''format the message according to the template'''
        if message_type is None:
            message_type=e3.Message.TYPE_MESSAGE

        outgoing = False
        consecutive = False

        if self.contact.account == contact.account:
            outgoing = True

        if self.last_message_sender and \
            self.last_message_sender.account == contact.account:
            consecutive = True

        timestamp = time.time()
        self.last_message_sender = contact
        self.last_message_time = timestamp

        if message_type == e3.Message.TYPE_MESSAGE:
            if consecutive:
                if outgoing:
                    template = self.consecutive_outgoing
                else:
                    template = self.consecutive_incoming
            else:
                if outgoing:
                    template = self.outgoing
                else:
                    template = self.incoming

        if message_type == e3.Message.TYPE_FLNMSG:
            template = self.offline_incoming
            timestamp = timestamp_override

        if message_type == e3.Message.TYPE_NUDGE:
            if outgoing:
                template = self.outgoing_nudge
            else:
                template = self.nudge
                
            self.last_message_sender = None


        formated_time = time.strftime('%c', time.gmtime(timestamp))

        template = template.replace('%NICK%',
            escape(contact.nick))
        template = template.replace('%ALIAS%',
            escape(contact.alias))
        template = template.replace('%ACCOUNT%',
            escape(contact.account))
        template = template.replace('%DISPLAYNAME%',
            escape(contact.display_name))
        template = template.replace('%TIME%',
            escape(formated_time))
        template = template.replace('%STATUS%',
            escape(e3.status.STATUS[contact.status]))
        template = template.replace('%PERSONALMESSAGE%',
            escape(contact.message))
        template = template.replace('%NL%', self.new_line)

        is_raw = False

        if '%MESSAGE%' in template:
            (first, last) = template.split('%MESSAGE%')
        elif '%RAWMESSAGE%' in template:
            (first, last) = template.split('%RAWMESSAGE%')
            is_raw = True
        else:
            first = template
            last = ''

        return (is_raw, consecutive, outgoing, first, last)

dic = {
    '\"'    :    '&quot;',
    '\''    :    '&apos;'
}

dic_inv = {
    '&quot;'    :'\"',
    '&apos;'    :'\''
}

def escape(string_):
    '''replace the values on dic keys with the values'''
    return xml.sax.saxutils.escape(string_, dic)

def unescape(string_):
    '''replace the values on dic_inv keys with the values'''
    return xml.sax.saxutils.unescape(string_, dic_inv)

