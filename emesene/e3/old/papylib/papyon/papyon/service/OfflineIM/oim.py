# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from papyon.msnp.challenge import _msn_challenge
from papyon.msnp.notification import ProtocolConstant
from papyon.service.OfflineIM.constants import *
from papyon.service.SOAPService import SOAPService
from papyon.service.SingleSignOn import *
from papyon.util.async import *

__all__ = ['OIM']

class OIM(SOAPService):
    def __init__(self, sso, proxies=None):
        self._sso = sso
        self._tokens = {}
        self.__lock_key = ""
        SOAPService.__init__(self, "OIM", proxies)

    def set_lock_key(self, lock_key):
        self.__lock_key = lock_key

    @RequireSecurityTokens(LiveService.MESSENGER_SECURE)
    def Store2(self, callback, errback, from_member_name, friendly_name, 
               to_member_name, session_id, message_number, message_type, message_content):
        import base64
        token = str(self._tokens[LiveService.MESSENGER_SECURE])
        fname = "=?utf-8?B?%s?=" % base64.b64encode(friendly_name)

        content = self.__build_mail_data(session_id, message_number, message_content)
        user_data = (from_member_name, friendly_name, to_member_name, session_id,
                message_number, message_type, message_content)

        self._soap_request(self._service.Store2,
                           (from_member_name, fname, 
                            ProtocolConstant.CVR[4],
                            ProtocolConstant.VER[0],
                            ProtocolConstant.CVR[5],
                            to_member_name,
                            message_number, 
                            token,
                            ProtocolConstant.PRODUCT_ID,
                            self.__lock_key),
                           (message_type, content),
                           callback, errback,
                           user_data)

    def _HandleStore2Fault(self, callback, errback, soap_response, user_data):
        error = OfflineMessagesBoxError.from_fault(soap_response.fault)
        if error == OfflineMessagesBoxError.AUTHENTICATION_FAILED:
            auth_policy = soap_response.fault.detail.findtext("./oim:RequiredAuthPolicy")
            lock_key_challenge = soap_response.fault.detail.findtext("./oim:LockKeyChallenge")

            if lock_key_challenge:
                self.__oim.set_lock_key(_msn_challenge(lock_key_challenge))
            if auth_policy:
                self._sso.DiscardSecurityTokens([LiveService.MESSENGER_SECURE])
                self.Store2(callback, errback, *user_data)
                return True

        return False

    def __build_mail_data(self, run_id, sequence_number, content):
        import base64
        mail_data = 'MIME-Version: 1.0\r\n'
        mail_data += 'Content-Type: text/plain; charset=UTF-8\r\n'
        mail_data += 'Content-Transfer-Encoding: base64\r\n'
        mail_data += 'X-OIM-Message-Type: OfflineMessage\r\n'
        mail_data += 'X-OIM-Run-Id: {%s}\r\n' % run_id
        mail_data += 'X-OIM-Sequence-Num: %s\r\n\r\n' % sequence_number
        mail_data += base64.b64encode(content)
        return mail_data

    def _HandleSOAPResponse(self, request_id, callback, errback, soap_response,
            user_data):
        run(callback)

    def _HandleSOAPFault(self, request_id, callback, errback, soap_response,
            user_data):
        error = OfflineMessagesBoxError.from_fault(soap_response.fault)
        run(errback, error)
