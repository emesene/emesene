# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2007 Ole André Vadla Ravnås <oleavr@gmail.com>
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

__all__ = ['ProtocolError', 'ParseError', 'SLPError', 'SLPSessionError']

class Error(Exception):
    """Generic exception type"""
    def __init__(self, code, message):
        Exception.__init__(self)
        self.code = code
        self.message = message

    def __str__(self):
        return str(self.code) + ':' + str(self.message)

class ProtocolError(Error):
    """Protocol Error, it should never be thrown"""
    def __init__(self, message):
        Error.__init__(self, 0, message)

    def __str__(self):
        return self.message

class ParseError(Error):
    """Parsing Error"""
    def __init__(self, message, infos=''):
        Error.__init__(self, 1, message)
        self.infos = infos

    def __str__(self):
        return self.message

class SLPError(Error):
    """MSNSLP error, used by the msnp2p protocol"""
    def __init__(self, message):
        Error.__init__(self, 2, message)

class SLPSessionError(Error):
    """SLP Session error, used by the msnp2p protocol"""
    def __init__(self, message):
        Error.__init__(self, 2, message)

