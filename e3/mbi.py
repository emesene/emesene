'''encyptation for mbi authentification policy'''
import hmac
import struct
import random
import base64
try:
    from hashlib import sha1
except ImportError:
    import sha
    sha1 = sha.new

import pydes

CALC_3DES = 0x6603
CALG_SHA1 = 0x8004

def encrypt(key, nonce):
    '''Return a base64 hash for mbi auth policy'''
    def derive_key(key, magic):
        hash1 = hmac.new(key, magic, sha1).digest()
        hash2 = hmac.new(key, hash1 + magic, sha1).digest()
        hash3 = hmac.new(key, hash1, sha1).digest()
        hash4 = hmac.new(key, hash3 + magic, sha1).digest()
        return hash2 + hash4[0:4]

    #hm = lambda k, m: hmac.new(k, m, sha1).digest()
    #lambda k, m: hm(k, hm(k, m) + m) + hm(k, hm(k, hm(k, m)) + m)[0:4]
    
    key1 = base64.standard_b64decode(key)
    key2 = derive_key(key1, "WS-SecureConversationSESSION KEY HASH")
    key3 = derive_key(key1, "WS-SecureConversationSESSION KEY ENCRYPTION")

    hash_ = hmac.new(key2, nonce, sha1).digest()

    iv = struct.pack("Q", random.getrandbits(8 * 8))  # 8 bytes

    ciph = pydes.triple_des(key3, pydes.CBC, iv).encrypt(nonce + \
        "\x08\x08\x08\x08\x08\x08\x08\x08")
  
    blob = struct.pack("<LLLLLLL", 28, pydes.CBC, CALC_3DES, CALG_SHA1,
                       len(iv), len(hash_), len(ciph)) + iv + hash_ + ciph
    return base64.standard_b64encode(blob)
