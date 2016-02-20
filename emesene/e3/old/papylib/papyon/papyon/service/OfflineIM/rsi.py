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

from papyon.util.async import *
from papyon.util.element_tree import XMLTYPE
from papyon.service.OfflineIM.constants import *
from papyon.service.SingleSignOn import *
from papyon.service.SOAPService import SOAPService

import email

import logging

__all__ = ['RSI']

logger = logging.getLogger('papyon.service')

class RSI(SOAPService):
    def __init__(self, sso, proxies=None):
        self._sso = sso
        self._tokens = {}
        SOAPService.__init__(self, "RSI", proxies)

    def GetMetadata(self, callback, errback):
        self.__soap_request(callback, errback,
                            self._service.GetMetadata,
                            ())

    def _HandleGetMetadataResponse(self, callback, errback, response, user_data):
        run(callback, response.text)

    def GetMessage(self, callback, errback, message_id, mark_as_read):
        self.__soap_request(callback, errback,
                            self._service.GetMessage,
                            (message_id, XMLTYPE.bool.encode(mark_as_read)))

    def _HandleGetMessageResponse(self, callback, errback, response, user_data):
        m = email.message_from_string(response.text)
        run_id = m.get('X-OIM-Run-Id')[1:-1]
        seq_num = int(m.get('X-OIM-Sequence-Num'))
        if m.get_content_type().split('/')[1] == 'vnd.ms-msnipg':
            # FIXME : process the IPG data 
            # http://www.amsn-project.net/forums/viewtopic.php?p=21744
            # set a mobile sender flag
            return
        run(callback, run_id, seq_num, m.get_payload().decode('base64'))

    def DeleteMessages(self, callback, errback, message_ids):
        self.__soap_request(callback, errback,
                            self._service.DeleteMessages,
                            (message_ids,))

    @RequireSecurityTokens(LiveService.MESSENGER)
    def __soap_request(self, callback, errback, method, args):
        token = str(self._tokens[LiveService.MESSENGER])
        self._soap_request(method, (token,), args, callback, errback)

    def _HandleSOAPResponse(self, request_id, callback, errback,
            soap_response, user_data):
        run(callback)

    def _HandleSOAPFault(self, request_id, callback, errback,
            soap_response, user_data):
        error = OfflineMessagesBoxError.from_fault(soap_response.fault)
        run(errback, error)
