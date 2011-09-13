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

from papyon.errors import ParseError
from papyon.util.debug import hexify_string

import struct

__all__ = ['TLV', 'TLVParseError']

class TLVParseError(ParseError):
    """TLV Parsing Error"""
    def __init__(self, message, infos=''):
        ParseError.__init__(self, "TLV", message, infos)

class TLV(object):
    """Utility class to build and parse data in a TLV representation.
       Each TLV (type-length-value) element has a 1-byte field for the type,
       a 1-byte field for the length and a variant size field for the value.
       The data is padded with null byte (0x0) to the next 4-bytes boundary."""

    def __init__(self, length_dict):
        """Initialize a TLV object
           @param length_dict: dict of possible types with their length"""

        self._length_dict = length_dict
        self._data = {}
        self._formats = {1: "B", 2: "H", 4: "I", 8: "Q"}

    def size_to_packed_format(self, size):
        """Determine the correct format to unpack a value (as used by
           'struct' module)."""
        if size in self._formats:
            return self._formats[size]
        else:
            return "%ss" % size

    def get(self, key, default):
        """Get the value for the given type in the TLV or return the default
           value if this field is not present in the TLV."""
        return self._data.get(key, default)

    def update(self, key, value):
        """Update the value for this type. If the value is null, delete
           the sequence from the TLV."""
        if value:
            self._data[key] = value
        elif key in self._data:
            del self._data[key]

    def __len__(self):
        size = 0
        for (t, v) in self._data.items():
            size += 2 + self._length_dict[t]
        if (size % 4) != 0:
            size += 4 - (size % 4)
        return size

    def __str__(self):
        """Pack data in a string and add padding."""
        string = ""
        for (t, v) in self._data.items():
            if not t in self._length_dict: continue
            l = self._length_dict[t]
            f = self.size_to_packed_format(l)
            string += struct.pack(">BB%s" % f, t, l, v)
        if (len(string) % 4) != 0:
            string += '\x00' * (4 - (len(string) % 4))
        return string

    def parse(self, data, size):
        """Parse the given TLV data and add values to the internal dict."""
        offset = 0
        while offset < size:
            if ord(data[offset]) is 0: break # ignore padding bytes
            t = ord(data[offset])
            l = ord(data[offset + 1])
            f = self.size_to_packed_format(l)

            end = offset + 2 + l
            if end > size:
                raise TLVParseError("Overflow (%i > %i)" % (end, size))

            try:
                self._data[t] = struct.unpack(">%s" % f, data[offset + 2:end])[0]
            except:
                infos = hexify_string(data[offset + 2:end])
                raise TLVParseError("Couldn't unpack format %s" % f, infos)
            offset = end
