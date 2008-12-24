import time

import MarkupParser
import protocol.status

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

    def __init__(self, contact, new_line='\n'):
        '''constructor'''

        # the contact who sends the messages 
        self.contact = contact
        self.last_message_sender = None
        self.last_message_time = None
        self.new_line = new_line

        # default formats
        self.incoming = '<b>%DISPLAYNAME%</b>: %MESSAGE%%NL%'
        self.outgoing = self.incoming
        self.consecutive_incoming = '  %MESSAGE%%NL%'
        self.consecutive_outgoing = '  %MESSAGE%%NL%'
        self.offline_incoming = \
            '<i>(offline message)</i><b>%DISPLAYNAME%</b>: %MESSAGE%%NL%'

    def format(self, contact):
        '''format the message according to the template'''
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

        formated_time = time.strftime('%c', time.gmtime(timestamp)) 

        template = template.replace('%NICK%', 
            MarkupParser.escape(contact.nick))
        template = template.replace('%ALIAS%', 
            MarkupParser.escape(contact.alias))
        template = template.replace('%ACCOUNT%', 
            MarkupParser.escape(contact.account))
        template = template.replace('%DISPLAYNAME%', 
            MarkupParser.escape(contact.display_name))
        template = template.replace('%TIME%', 
            MarkupParser.escape(formated_time))
        template = template.replace('%STATUS%', 
            MarkupParser.escape(protocol.status.STATUS[contact.status]))
        template = template.replace('%PERSONALMESSAGE%', 
            MarkupParser.escape(contact.message))
        template = template.replace('%NL%', self.new_line)

        # TODO: ValueError will be raised if the theme doent 
        # contain a MESSAGE or RAWMESSAGE tags
        if '%MESSAGE%' in template:
            (first, last) = template.split('%MESSAGE%')
            is_raw = False
        else:
            (first, last) = template.split('%RAWMESSAGE%')
            is_raw = True
                
        return (is_raw, consecutive, outgoing, first, last) 

