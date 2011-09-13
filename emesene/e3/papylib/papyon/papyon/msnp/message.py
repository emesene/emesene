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
from papyon.util.debug import escape_string
from papyon.util.parsing import parse_account

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

        @ivar sender_guid: sender machine GUID (if any)
        @type sender_guid: uuid4"""

    def __init__(self, sender=None, message=""):
        """Initializer
            
            @param message: The body of the message, it is put after the headers
            @type message: string"""
        HTTPMessage.__init__(self)
        self.sender = sender
        if message:
            self.parse(message)
        self.sender_guid = self.parse_guid('P2P-Src')

    def __repr__(self):
        """Represents the payload of the message"""
        message = ''
        for header_name, header_value in self.headers.iteritems():
            message += '\t%s: %s\\r\\n\n' % (header_name, repr(header_value))
        if self.headers['Content-Type'] != "application/x-msnmsgrp2p":
            message += '\t\\r\\n\n'
            message += '\t' + escape_string(self.body).\
                    replace("\r\n", "\\r\\n\n\t")
        else:
            message += "\t[P2P message (%d bytes)]" % (len(self.body) - 4)
        return message.rstrip("\n\t")

    def parse_guid(self, header):
        if header not in self.headers:
            return None
        return parse_account(self.headers[header])[1]
