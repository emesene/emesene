# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2005-2007 Ali Sabil <ali.sabil@gmail.com>
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

from SOAPService import *
from description.SingleSignOn.RequestMultipleSecurityTokens import LiveService

from papyon.errors import ClientError, ClientErrorType
from papyon.util.async import *

import base64
import struct
import time
import datetime
import sys
import Crypto.Util.randpool as randpool
from Crypto.Hash import HMAC, SHA
from Crypto.Cipher import DES3

__all__ = ['SingleSignOn', 'LiveService', 'RequireSecurityTokens']


class AuthenticationError(ClientError):
    "Authentication related errors"
    UNKNOWN = 0
    INVALID_USERNAME = 1
    INVALID_PASSWORD = 2
    INVALID_USERNAME_OR_PASSWORD = 3
    REDIRECT = 4

    def __init__(self, code, fault="", details=""):
        ClientError.__init__(self, ClientErrorType.AUTHENTICATION, code)
        self._fault = fault
        self._details = details

    @staticmethod
    def from_fault(fault):
        error_code = AuthenticationError.UNKNOWN
        if fault.faultcode.endswith("FailedAuthentication"):
            error_code = AuthenticationError.INVALID_USERNAME_OR_PASSWORD
        elif fault.faultcode.endswith("Redirect"):
            error_code = AuthenticationError.REDIRECT

        return AuthenticationError(error_code, fault.faultcode,
                fault.faultstring)

    def __str__(self):
        return "Authentication Error (%s): %s" % (self._fault, self._details)


class SecurityToken(object):
    
    def __init__(self):
        self.type = ""
        self.service_address = ""
        self.lifetime = [0, 0]
        self.security_token = ""
        self.proof_token = ""

    def is_expired(self):
        return datetime.datetime.utcnow() + datetime.timedelta(seconds=60) \
                >= self.lifetime[1]

    def mbi_crypt(self, nonce):
        WINCRYPT_CRYPT_MODE_CBC = 1
        WINCRYPT_CALC_3DES      = 0x6603
        WINCRYPT_CALC_SHA1      = 0x8004

        # Read key and generate two derived keys
        key1 = base64.b64decode(self.proof_token)
        key2 = self._derive_key(key1, "WS-SecureConversationSESSION KEY HASH")
        key3 = self._derive_key(key1, "WS-SecureConversationSESSION KEY ENCRYPTION")

        # Create a HMAC-SHA-1 hash of nonce using key2
        hash = HMAC.new(key2, nonce, SHA).digest()

        #
        # Encrypt nonce with DES3 using key3
        #

        # IV (Initialization Vector): 8 bytes of random data
        iv = randpool.RandomPool().get_bytes(8)
        obj = DES3.new(key3, DES3.MODE_CBC, iv)

        # XXX: win32's Crypt API seems to pad the input with 0x08 bytes
        # to align on 72/36/18/9 boundary
        ciph = obj.encrypt(nonce + "\x08\x08\x08\x08\x08\x08\x08\x08")

        blob = struct.pack("<LLLLLLL", 28, WINCRYPT_CRYPT_MODE_CBC,
                WINCRYPT_CALC_3DES, WINCRYPT_CALC_SHA1, len(iv), len(hash),
                len(ciph))
        blob += iv + hash + ciph
        return base64.b64encode(blob)

    def _derive_key(self, key, magic):
        hash1 = HMAC.new(key, magic, SHA).digest()
        hash2 = HMAC.new(key, hash1 + magic, SHA).digest()

        hash3 = HMAC.new(key, hash1, SHA).digest()
        hash4 = HMAC.new(key, hash3 + magic, SHA).digest()
        return hash2 + hash4[0:4]

    def __str__(self):
        return self.security_token

    def __repr__(self):
        return "<SecurityToken type=\"%s\" address=\"%s\" lifetime=\"%s\">" % \
                (self.type, self.service_address, str(self.lifetime))


class RequireSecurityTokens(object):
    def __init__(self, *tokens):
        assert(len(tokens) > 0)
        self._tokens = tokens

    def __call__(self, func):
        def sso_callback(tokens, object, user_callback, user_errback,
                user_args, user_kwargs):
            object._tokens.update(tokens)
            func(object, user_callback, user_errback, *user_args, **user_kwargs)

        def method(object, callback, errback, *args, **kwargs):
            callback = (sso_callback, object, callback, errback, args, kwargs)
            object._sso.RequestMultipleSecurityTokens(callback,
                    errback, *self._tokens)
        method.__name__ = func.__name__
        method.__doc__ = func.__doc__
        method.__dict__.update(func.__dict__)
        return method


class SingleSignOn(SOAPService):
    def __init__(self, username, password, proxies=None):
        # Passwords can only be up to 16 characters in length
        if len(password) > 16:
            password = password[0:16]

        self.__credentials = (username, password)
        self.__storage = {}

        self.__pending_response = False
        self.__pending_requests = []
        SOAPService.__init__(self, "SingleSignOn", proxies)

    def RequestMultipleSecurityTokens(self, callback, errback, *services):
        """Requests multiple security tokens from the single sign on service.
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
            @param services: one or more L{LiveService}"""

        #FIXME: we should instead check what are the common requested tokens
        # and if some tokens are not common then do a parallel request, needs
        # to be fixed later, for now, we just queue the requests
        if self.__pending_response:
            self.__pending_requests.append((callback, errback, services))
            return

        response_tokens = {}
        
        requested_services = services
        services = list(services)
        for service in services: # filter already available tokens
            service_url = service[0]
            if service_url in self.__storage:
                try:
                    token = self.__storage[service_url]
                except KeyError:
                    continue
                if not token.is_expired():
                    services.remove(service)
                    response_tokens[service] = token

        if len(services) == 0:
            self._HandleRequestMultipleSecurityTokensResponse(callback,
                    errback, [], (requested_services, response_tokens))
            return

        self.__pending_response = True
        method = self._service.RequestMultipleSecurityTokens
        self._soap_request(method, self.__credentials, services, callback,
                errback, (requested_services, response_tokens))
    
    def _HandleRequestMultipleSecurityTokensResponse(self, callback, errback,
            response, user_data):
        requested_services, response_tokens = user_data
        result = {}
        for node in response:
            token = SecurityToken()
            token.type = node.findtext("./wst:TokenType")
            token.service_address = node.findtext("./wsp:AppliesTo"
                    "/wsa:EndpointReference/wsa:Address")
            token.lifetime[0] = node.findtext("./wst:LifeTime/wsu:Created", "datetime")
            token.lifetime[1] = node.findtext("./wst:LifeTime/wsu:Expires", "datetime")
            
            try:
                token.security_token = node.findtext("./wst:RequestedSecurityToken"
                        "/wsse:BinarySecurityToken")
            except AttributeError:
                token.security_token = node.findtext("./wst:RequestedSecurityToken"
                        "/xmlenc:EncryptedData/xmlenc:CipherData"
                        "/xmlenc:CipherValue")

            try:
                token.proof_token = node.findtext("./wst:RequestedProofToken/wst:BinarySecret")
            except AttributeError:
                pass

            service = LiveService.url_to_service(token.service_address)
            assert(service != None), "Unknown service URL : " + \
                    token.service_address
            self.__storage[token.service_address] = token
            result[service] = token
        result.update(response_tokens)

        self.__pending_response = False

        run(callback, result)

        if len(self.__pending_requests):
            callback, errback, services = self.__pending_requests.pop(0)
            self.RequestMultipleSecurityTokens(callback, errback, *services)

    def DiscardSecurityTokens(self, services):
        for service in services:
            del self.__storage[service[0]]

    def _HandleSOAPFault(self, request_id, callback, errback,
             soap_response, user_data):
        error = AuthenticationError.from_fault(soap_response.fault)
        if error == AuthenticationError.REDIRECT:
            requested_services, response_tokens = user_data
            self._service.url = soap_response.fault.tree.findtext("psf:redirectUrl")
            self.__pending_response = False
            self.RequestMultipleSecurityTokens(callback, errback, *requested_services)
            return
        run(errback, error)


if __name__ == '__main__':
    import sys
    import getpass
    import signal
    import gobject
    import logging

    def sso_cb(tokens):
        print "Received tokens : "
        for token in tokens:
            print "token %s : %s" % (token, str(tokens[token]))

    logging.basicConfig(level=logging.DEBUG)

    if len(sys.argv) < 2:
        account = raw_input('Account: ')
    else:
        account = sys.argv[1]

    if len(sys.argv) < 3:
        password = getpass.getpass('Password: ')
    else:
        password = sys.argv[2]

    mainloop = gobject.MainLoop(is_running=True)
    
    signal.signal(signal.SIGTERM,
            lambda *args: gobject.idle_add(mainloop.quit()))

    sso = SingleSignOn(account, password)
    sso.RequestMultipleSecurityTokens((sso_cb,), None, LiveService.VOICE)

    while mainloop.is_running():
        try:
            mainloop.run()
        except KeyboardInterrupt:
            mainloop.quit()

