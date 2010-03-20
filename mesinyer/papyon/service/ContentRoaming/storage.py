# -*- coding: utf-8 -*-
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

from papyon.service.SOAPService import SOAPService, url_split
from papyon.util.element_tree import XMLTYPE
from papyon.service.SingleSignOn import *

from papyon.gnet.protocol import ProtocolFactory

__all__ = ['Storage']

class Storage(SOAPService):

    def __init__(self, sso, proxies=None):
        self._sso = sso
        self._tokens = {}
        SOAPService.__init__(self, "SchematizedStore", proxies)

    def GetProfile(self, callback, errback, scenario, cid, profile_rid, 
                   p_date_modified, expression_rid, e_date_modified, 
                   display_name, dn_last_modified, personal_status, 
                   ps_last_modified, user_tile_url, photo, flags):
        self.__soap_request(self._service.GetProfile, scenario,
                 (cid, 
                  XMLTYPE.bool.encode(profile_rid),
                  XMLTYPE.bool.encode(p_date_modified),
                  XMLTYPE.bool.encode(expression_rid),
                  XMLTYPE.bool.encode(e_date_modified),
                  XMLTYPE.bool.encode(display_name),
                  XMLTYPE.bool.encode(dn_last_modified),
                  XMLTYPE.bool.encode(personal_status),
                  XMLTYPE.bool.encode(ps_last_modified),
                  XMLTYPE.bool.encode(user_tile_url),
                  XMLTYPE.bool.encode(photo),
                  XMLTYPE.bool.encode(flags)),
                 callback, errback)

    def _HandleGetProfileResponse(self, callback, errback, response, user_date):
        profile_rid = response.findtext('./st:ResourceID')        
        
        expression_profile = response.find('./st:ExpressionProfile')
        expression_profile_rid = expression_profile.findtext('./st:ResourceID')

        display_name = expression_profile.findtext('./st:DisplayName')
        personal_msg = expression_profile.findtext('./st:PersonalStatus')

        photo = expression_profile.find('./st:Photo')
        if photo is not None:
            photo_rid = photo.findtext('./st:ResourceID')
            document_stream = photo.find('./st:DocumentStreams/st:DocumentStream')
            photo_mime_type = document_stream.findtext('./st:MimeType')
            photo_data_size = document_stream.findtext('./st:DataSize', "int")
            photo_url = document_stream.findtext('./st:PreAuthURL')
        else:
            photo_rid = photo_mime_type = photo_data_size = photo_url = None
        
        callback[0](profile_rid, expression_profile_rid, display_name, personal_msg,
                    photo_rid, photo_mime_type, photo_data_size, photo_url,
                    *callback[1:])

    def UpdateProfile(self, callback, errback, scenario, profile_rid,
                      display_name, personal_status, flags):
        self.__soap_request(self._service.UpdateProfile, scenario,
                            (profile_rid, display_name, personal_status, flags),
                            callback, errback)

    def _HandleUpdateProfileResponse(self, callback, errback, response, user_date):
        callback[0](*callback[1:])

    def CreateRelationships(self, callback, errback, scenario, 
                            source_rid, target_rid):
        self.__soap_request(self._service.CreateRelationships, scenario,
                            (source_rid, target_rid),
                            callback, errback)

    def _HandleCreateRelationshipsResponse(self, callback, errback, response, user_date):
        callback[0](*callback[1:])

    def DeleteRelationships(self, callback, errback, scenario, 
                            target_id, cid=None, source_id=None):
        self.__soap_request(self._service.DeleteRelationships, scenario,
                            (cid, source_id, target_id), callback, errback)

    def _HandleDeleteRelationshipsResponse(self, callback, errback, response, user_date):
        callback[0](*callback[1:])

    def CreateDocument(self, callback, errback, scenario, cid, photo_name,
                       photo_mime_type, photo_data):
        self.__soap_request(self._service.CreateDocument, scenario,
                            (cid, photo_name, photo_mime_type, photo_data),
                            callback, errback)

    def _HandleCreateDocumentResponse(self, callback, errback, response, user_date):
        document_rid = response.text
        callback[0](document_rid, *callback[1:])

    def FindDocuments(self, callback, errback, scenario, cid):
        self.__soap_request(self._service.FindDocuments, scenario,
                            (cid,), callback, errback)

    def _HandleFindDocumentsResponse(self, callback, errback, response, user_date):
        document = response.find('./st:Document')

        document_rid = response.findtext('./st:ResourceID')        
        document_name = response.findtext('./st:Name')        
        callback[0](document_rid, document_name, *callback[1:])

    @RequireSecurityTokens(LiveService.STORAGE)
    def __soap_request(self, method, scenario, args, callback, errback):
        token = str(self._tokens[LiveService.STORAGE])
        self._soap_request(method, (scenario, token), args, callback, errback)

    @RequireSecurityTokens(LiveService.STORAGE)
    def get_display_picture(self, pre_auth_url, callback, errback):
        token = str(self._tokens[LiveService.STORAGE])

        scheme = 'http'
        host = 'byfiles.storage.msn.com'
        port = 80
        resource = '?'.join([pre_auth_url, token.split('&')[0]])

        def request_callback(transport, http_response):
            type = http_response.get_header('Content-Type')#.split('/')[1]
            data = http_response.body
            callback[0](type, data, *callback[1:])

        http_headers = {}
        http_headers["Accept"] = "*/*"
        http_headers["Proxy-Connection"] = "Keep-Alive"
        http_headers["Connection"] = "Keep-Alive"
        
        proxy = self._proxies.get(scheme, None)
        transport = ProtocolFactory(scheme, host, port, proxy=proxy)
        transport.connect("response-received", request_callback)
        transport.connect("request-sent", self._request_handler)
        transport.connect("error", errback[0], *errback[1:])

        transport.request(resource, http_headers, method='GET')
