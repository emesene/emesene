# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2005-2006 Ali Sabil <ali.sabil@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""MSN protocol special command : MSG"""

from papyon.gnet.message.HTTP import HTTPMessage
import papyon.util.debug as debug

from urllib import quote, unquote
import struct

__all__ = ['MessageAcknowledgement', 'Message']


class MessageAcknowledgement(object):
    """Message Acknowledgement"""
    FULL = 'A'
    """Acknowledgement required for both delivery success and failure"""
    MSNC = 'D'
    """Direct connection, no acknowledgment required from the server"""
    HALF = 'N'
    """Acknowledgment on delivery failures"""
    NONE = 'U'
    """No Acknowledgment"""

class Message(HTTPMessage):
    """Base Messages class.
    
        @ivar sender: sender
        @type sender: profile.Contact
        
        @ivar body: message body
        @type body: string
        
        @ivar headers: message headers
        @type headers: {header_name: string => header_value:string}
        
        @ivar content_type: the message content type
        @type content_type: tuple(mime_type, encoding)"""

    def __init__(self, sender=None, message=""):
        """Initializer
            
            @param message: The body of the message, it is put after the headers
            @type message: string"""
        HTTPMessage.__init__(self)
        self.sender = sender
        if message:
            self.parse(message)

    def __repr__(self):
        """Represents the payload of the message"""
        message = ''
        for header_name, header_value in self.headers.iteritems():
            message += '\t%s: %s\\r\\n\n' % (header_name, repr(header_value))
        message += '\t\\r\\n\n'
        if self.headers['Content-Type'] != "application/x-msnmsgrp2p":
            message += '\t' + debug.escape_string(self.body).\
                    replace("\r\n", "\\r\\n\n\t")
        else:
            tlp_header = self.body[:48]
            tlp_footer = self.body[-4:]
            tlp_session_id = struct.unpack("<L", self.body[0:4])[0]
            tlp_flags = struct.unpack("<L", self.body[28:32])[0]
            body = self.body[48:-4]

            message += "\t" + debug.hexify_string(tlp_header).replace("\r\n", "\n\t")

            if tlp_flags == 0 or tlp_session_id == 0:
                message += "\n\t" + debug.escape_string(body).\
                        replace("\r\n", "\\r\\n\n\t")
            elif len(body) > 0:
                message += "\n\t" + "[%d bytes of data]" % len(body)
            message += "\n\t" + debug.hexify_string(tlp_footer)

        return message.rstrip("\n\t")

    def __get_content_type(self):
        if 'Content-Type' in self.headers:
            content_type = self.headers['Content-Type'].split(';', 1)
            if len(content_type) == 1:
                return (content_type[0].strip(), 'UTF-8')
            mime_type = content_type[0].strip()
            encoding = content_type[1].split('=', 1)[1].strip()
            return (mime_type, encoding)
        return ('text/plain', 'UTF-8')
    
    def __set_content_type(self, content_type):
        if not isinstance(content_type, str):
            content_type = '; charset='.join(content_type)
        self.headers['Content-Type'] = content_type

    content_type = property(__get_content_type, __set_content_type,
            doc="a tuple specifying the content type")

