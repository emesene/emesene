# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2005-2007 Ali Sabil <ali.sabil@gmail.com>
# Copyright (C) 2005-2006 Ole André Vadla Ravnås <oleavr@gmail.com>
# Copyright (C) 2007 Johann Prieur <johann.prieur@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from constants import ProtocolConstant

def _msn_challenge(data):
    """
    Compute an answer for MSN Challenge from a given data

        @param data: the challenge string sent by the server
        @type data: string
    """
    import struct
    import hashlib
    def little_endify(value, c_type="L"):
        """Transform the given value into little endian"""
        return struct.unpack(">" + c_type, struct.pack("<" + c_type, value))[0]

    md5_digest = hashlib.md5(data + ProtocolConstant.PRODUCT_KEY).digest()
    # Make array of md5 string ints
    md5_integers = struct.unpack("<llll", md5_digest)
    md5_integers = [(x & 0x7fffffff) for x in md5_integers]
    # Make array of chl string ints
    data += ProtocolConstant.PRODUCT_ID
    amount = 8 - len(data) % 8
    data += "".zfill(amount)
    chl_integers = struct.unpack("<%di" % (len(data)/4), data)
    # Make the key
    high = 0
    low = 0
    i = 0
    while i < len(chl_integers) - 1:
        temp = chl_integers[i]
        temp = (ProtocolConstant.CHL_MAGIC_NUM * temp) % 0x7FFFFFFF
        temp += high
        temp = md5_integers[0] * temp + md5_integers[1]
        temp = temp % 0x7FFFFFFF
        high = chl_integers[i + 1]
        high = (high + temp) % 0x7FFFFFFF
        high = md5_integers[2] * high + md5_integers[3]
        high = high % 0x7FFFFFFF
        low = low + high + temp
        i += 2
    high = little_endify((high + md5_integers[1]) % 0x7FFFFFFF)
    low = little_endify((low + md5_integers[3]) % 0x7FFFFFFF)
    key = (high << 32L) + low
    key = little_endify(key, "Q")
    longs = [x for x in struct.unpack(">QQ", md5_digest)]
    longs = [little_endify(x, "Q") for x in longs]
    longs = [x ^ key for x in longs]
    longs = [little_endify(abs(x), "Q") for x in longs]
    out = ""
    for value in longs:
        value = hex(long(value))
        value = value[2:-1]
        value = value.zfill(16)
        out += value.lower()
    return out

