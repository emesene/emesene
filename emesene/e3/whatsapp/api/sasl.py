import uuid
from base64 import b64decode, b64encode
from hashlib import md5

DOMAIN = 's.whatsapp.net'
URI = 'xmpp/s.whatsapp.net'
NC = '00000001'
QOP = 'auth'

class SASL:
    """This class aims to provide the necessarry SASL mechanisms.

    Currently, only the DIGEST-MD5-1 used by WhatsApp is supported. This is
    mostly (if not completely) the same as DIGEST-MD5, as described in RFC 2617
    (http://tools.ietf.org/html/rfc2617)."""

    def __init__(self, username="", password="", mechanism="", uri="", realm="",
            method="AUTHENTICATE"):
        self.username = username
        self.password = password
        self.mechanism = mechanism
        self.uri = uri
        self.realm = realm
        self.method = method

    def get_response(self, challenge):
        """Generates a SASL response given a challenge.

        Both the input challenge and the output response are encoded in
        base64.

        The challenge string should at least include a nonce, qop and
        algorithm."""

        if self.mechanism != 'DIGEST-MD5-1':
            raise Exception("Unsupported SASL mechanism: %s" % self.mechanism)

        challenge = b64decode(challenge)

        print challenge

        cnonce = str(uuid.uuid4())
        nonce = None
        qop = None
        alg = None

        # Times this nonce has been used... Just always setting this to 1 works.
        nc = "%08x" % 1

        # Take the easy way out, just split on comma's (as far as I know, there
        # won't be any comman's inside quotes, otherwise this will fail).
        for pair in challenge.split(','):
            k, v = pair.split('=', 1)
            v = v.strip('"')

            if k == 'nonce':
                nonce = v
            elif k == 'qop':
                qop = v
            elif k == 'algorithm':
                alg = v

        if nonce is None:
            raise Exception("Did not find nonce in SASL challenge string.")

        if qop != "auth":
            raise Exception("Unsupported auth method: %s" % qop)

        if alg != "md5-sess":
            raise Exception("Unsupported algorithm: %s" % alg)

        A1_temp = "%s:%s:%s" % (self.username, self.realm, self.password)
        A1 = "%s:%s:%s" % (md5(A1_temp).digest(), nonce, cnonce)
        A2 = "%s:%s" % (self.method, self.uri)

        resphash = "%s:%s:%s:%s:%s:%s" % (md5(A1).hexdigest(),
                                          nonce,
                                          nc,
                                          cnonce,
                                          qop,
                                          md5(A2).hexdigest())
        resphash = md5(resphash).hexdigest()

        respdict = {'username': self.username,
                    'realm': self.realm,
                    'nonce': nonce,
                    'cnonce': cnonce,
                    'nc': nc,
                    'qop': qop,
                    'digest-uri': self.uri,
                    'response': resphash}

        resp = ','.join(["%s=%s" % i for i in respdict.items()])

        return b64encode(resp)

