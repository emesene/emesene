# Copyright 2005 James Bunton <james@delx.cjb.net>
# Licensed for distribution under the GPL version 2, check COPYING for details

import struct

try:
    import hashlib
    md5 = hashlib.md5
except ImportError:
    from md5 import md5

_PRODUCT_KEY = 'O4BG@C7BWLYQX?5G'
_PRODUCT_ID = 'PROD01065C%ZFN6F'
MSNP11_MAGIC_NUM = 0x0E79A9C1

def do_challenge(challenge_data):
    '''create the response to a challenge'''
    md5digest = md5(challenge_data + _PRODUCT_KEY).digest()

    # Make array of md5 string ints
    md5_ints = struct.unpack("<llll", md5digest)
    md5_ints = [(x & 0x7fffffff) for x in md5_ints]

    # Make array of chl string ints
    challenge_data += _PRODUCT_ID
    amount = 8 - len(challenge_data) % 8
    challenge_data += "".zfill(amount)
    chl_ints = struct.unpack("<%di" % (len(challenge_data)/4), challenge_data)

    # Make the key
    high = 0
    low = 0
    i = 0
    while i < len(chl_ints) - 1:
        temp = chl_ints[i]
        temp = (MSNP11_MAGIC_NUM * temp) % 0x7FFFFFFF
        temp += high
        temp = md5_ints[0] * temp + md5_ints[1]
        temp = temp % 0x7FFFFFFF

        high = chl_ints[i + 1]
        high = (high + temp) % 0x7FFFFFFF
        high = md5_ints[2] * high + md5_ints[3]
        high = high % 0x7FFFFFFF

        low = low + high + temp

        i += 2

    high = littleendify((high + md5_ints[1]) % 0x7FFFFFFF)
    low = littleendify((low + md5_ints[3]) % 0x7FFFFFFF)
    key = (high << 32L) + low
    key = littleendify(key, "Q")

    longs = [x for x in struct.unpack(">QQ", md5digest)]
    longs = [littleendify(x, "Q") for x in longs]
    longs = [x ^ key for x in longs]
    longs = [littleendify(abs(x), "Q") for x in longs]

    out = ""
    for long_ in longs:
        long_ = hex(long(long_))
        long_ = long_[2:-1]
        long_ = long_.zfill(16)
        out += long_.lower()

    return out

def littleendify(num, ccc="L"):
    '''return a number in little endian'''
    return struct.unpack(">" + ccc, struct.pack("<" + ccc, num))[0]
