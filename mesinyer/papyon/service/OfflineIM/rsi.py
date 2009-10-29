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

from papyon.util.element_tree import XMLTYPE
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

    @RequireSecurityTokens(LiveService.MESSENGER)
    def GetMetadata(self, callback, errback):
        self.__soap_request(self._service.GetMetadata, (), 
                            callback, errback)

    def _HandleGetMetadataResponse(self, callback, errback, response, user_data):
        callback[0](response.text, *callback[1:])

    @RequireSecurityTokens(LiveService.MESSENGER)
    def GetMessage(self, callback, errback, message_id, mark_as_read):
        self.__soap_request(self._service.GetMessage, 
                            (message_id, XMLTYPE.bool.encode(mark_as_read)), 
                            callback, errback)

    def _HandleGetMessageResponse(self, callback, errback, response, user_data):
        m = email.message_from_string(response.text)
        run_id = m.get('X-OIM-Run-Id')[1:-1]
        seq_num = int(m.get('X-OIM-Sequence-Num'))
        if m.get_content_type().split('/')[1] == 'vnd.ms-msnipg':
            # FIXME : process the IPG data 
            # http://www.amsn-project.net/forums/viewtopic.php?p=21744
            # set a mobile sender flag
            return
        callback[0](run_id, seq_num, m.get_payload().decode('base64'), 
                    *callback[1:])

    @RequireSecurityTokens(LiveService.MESSENGER)
    def DeleteMessages(self, callback, errback, message_ids):
        self.__soap_request(self._service.DeleteMessages, (message_ids,),
                            callback, errback)
    
    def _HandleDeleteMessagesResponse(self, callback, errback, response, user_data):
        callback[0](*callback[1:])

    def __soap_request(self, method, args, callback, errback):
        token = str(self._tokens[LiveService.MESSENGER])

        http_headers = method.transport_headers()
        soap_action = method.soap_action()
        
        soap_header = method.soap_header(token)
        soap_body = method.soap_body(*args)
        
        method_name = method.__name__.rsplit(".", 1)[1]
        self._send_request(method_name, self._service.url, 
                           soap_header, soap_body, soap_action, 
                           callback, errback, http_headers)

    def _HandleSOAPFault(self, request_id, callback, errback,
            soap_response, user_data):
        errback[0](None, *errback[1:])




        
