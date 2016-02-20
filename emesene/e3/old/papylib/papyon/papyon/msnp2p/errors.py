# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2010 Collabora Ltd.
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

from papyon.errors import ClientError, ClientErrorType, ParseError

class P2PError(ClientError):
    """P2P Error"""

    UNKNOWN = 0

    def __init__(self, message):
        ClientError.__init__(self, ClientErrorType.UNKNOWN, P2PError.UNKNOWN)
        self.message = message

    def __str__(self):
        return "P2P Error: %s" % self.message

class SLPParseError(ParseError):
    """SLP Parsing Error"""
    def __init__(self, message, infos=''):
        ParseError.__init__(self, "SLP", message, infos)

class TLPParseError(ParseError):
    """TLP Parsing Error"""
    def __init__(self, version, message, infos=''):
        ParseError.__init__(self, "TLPv%i" % version, message, infos)
        self.version = version

class FTParseError(ParseError):
    """File Transfer Context Parsing Error"""
    def __init__(self, context):
        ParseError.__init__(self, "FT Context", "invalid context", context)

class MSNObjectParseError(ParseError):
    """MSN Object Parsing Error"""
    def __init__(self, data):
        ParseError.__init__(self, "MSN Object", "invalid MSN Object", data)
