# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Collabora Ltd.
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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

import base64
import email.quoprimime
import email.base64mime
import re


PADDING = ('', '=', '==', 'A', 'A=', 'A==')

def fix_b64_padding(string):
    for pad in PADDING:
        try:
            base64.b64decode(string + pad)
            return string + pad
        except:
            continue
    return string

def b64_decode(string):
    for pad in PADDING:
        try:
            return base64.b64decode(string + pad)
        except:
            continue
    raise TypeError


# Match encoded-word strings in the form =?charset?q?Hello_World?=
ecre = re.compile(r'''
  =\?                   # literal =?
  (?P<charset>[^?]*?)   # non-greedy up to the next ? is the charset
  \?                    # literal ?
  (?P<encoding>[qb])    # either a "q" or a "b", case insensitive
  \?                    # literal ?
  (?P<encoded>.*?)      # non-greedy up to the next ?= is the encoded string
  \?=                   # literal ?=
  (?=[ \t]|$)           # whitespace or the end of the string
  ''', re.VERBOSE | re.IGNORECASE | re.MULTILINE)

def decode_rfc2047_string(string):
    """ Decode it according to RFC 2047. This code has been adapted from
        Python code (email.header.decode_header), except we don't strip the
        unencoded parts and we decode all the parts instead of just returning
        the encoded parts and charsets. """
    # If no encoding, just return the string
    if not ecre.search(string):
        return string

    decoded = u""

    try:
        for line in string.splitlines():
            parts = ecre.split(line)
            while parts:
                unenc = parts.pop(0)
                # don't append single spaces between encoded words to the result
                if not decoded or not parts or unenc != ' ':
                    decoded += unicode(unenc)
                if parts:
                    charset, encoding = [s.lower() for s in parts[0:2]]
                    encoded = parts[2]
                    dec = encoded
                    if encoding == 'q':
                        dec = email.quoprimime.header_decode(encoded)
                    elif encoding == 'b':
                        dec = email.base64mime.decode(encoded)

                    decoded += dec.decode(charset) if charset else dec
                del parts[0:3]
    except:
        return string

    if type(decoded) is unicode:
        decoded = decoded.encode("utf-8")
    return decoded
