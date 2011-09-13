# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2007  Ole André Vadla Ravnås <oleavr@gmail.com>
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

import struct

"""Utility functions used for debug output processing"""

def escape_string(string):
    result = ""
    for c in string:
        v = ord(c)
        if (v >= 32 and v <= 127) or c in ("\t", "\r", "\n"):
            result += c
        else:
            result += "\\x%02x" % ord(c)

    return result

def hexify_string(string):
    result = ""
    for i, c in enumerate(string):
        if result:
            if i % 16 != 0:
                result += " "
            else:
                result += "\r\n"
        result += "%02x" % ord(c)
    return result

