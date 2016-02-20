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
from papyon.util.async import *
from papyon.util.element_tree import XMLTYPE
from papyon.service.ContentRoaming.constants import *
from papyon.service.SingleSignOn import *

from papyon.gnet.protocol import ProtocolFactory

import urllib

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
        self.__soap_request(callback, errback,
                 self._service.GetProfile, scenario,
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
                  XMLTYPE.bool.encode(flags)))

    def _HandleGetProfileResponse(self, callback, errback, response, user_data):
        profile_rid = response.findtext('./st:ResourceID')

        expression_profile = response.find('./st:ExpressionProfile')
        expression_profile_rid = expression_profile.findtext('./st:ResourceID')

        display_name = expression_profile.findtext('./st:DisplayName')
        personal_msg = expression_profile.findtext('./st:PersonalStatus')
        user_tile_url = expression_profile.findtext('./st:StaticUserTilePublicURL')

        photo = expression_profile.find('./st:Photo')
        if photo is not None:
            photo_rid = photo.findtext('./st:ResourceID')
            document_stream = photo.find('./st:DocumentStreams/st:DocumentStream')
            photo_mime_type = document_stream.findtext('./st:MimeType')
            photo_data_size = document_stream.findtext('./st:DataSize', "int")
            photo_url = document_stream.findtext('./st:PreAuthURL')
        else:
            photo_rid = photo_mime_type = photo_data_size = photo_url = None
        
        run(callback, profile_rid, expression_profile_rid, display_name,
                personal_msg, user_tile_url, photo_rid, photo_mime_type,
                photo_data_size, photo_url)

    def UpdateProfile(self, callback, errback, scenario, profile_rid,
                      display_name, personal_status, flags):
        self.__soap_request(callback, errback,
                            self._service.UpdateProfile, scenario,
                            (profile_rid, display_name, personal_status, flags))

    def CreateRelationships(self, callback, errback, scenario,
                            source_rid, target_rid):
        self.__soap_request(callback, errback,
                            self._service.CreateRelationships, scenario,
                            (source_rid, target_rid))

    def DeleteRelationships(self, callback, errback, scenario,
                            target_id, cid=None, source_id=None):
        self.__soap_request(callback, errback,
                            self._service.DeleteRelationships, scenario,
                            (cid, source_id, target_id))

    def _HandleDeleteRelationships(self, callback, errback, response, user_data):
        error = ContentRoamingError.from_fault(response.fault)
        if error == ContentRoamingError.ITEM_DOES_NOT_EXIST:
            run(callback)
            return True
        return False

    def CreateDocument(self, callback, errback, scenario, cid, photo_name,
                       photo_mime_type, photo_data):
        self.__soap_request(callback, errback,
                            self._service.CreateDocument, scenario,
                            (cid, photo_name, photo_mime_type, photo_data))

    def _HandleCreateDocumentResponse(self, callback, errback, response, user_data):
        run(callback, response.text)

    def FindDocuments(self, callback, errback, scenario, cid):
        self.__soap_request(callback, errback,
                            self._service.FindDocuments, scenario,
                            (cid,))

    def _HandleFindDocumentsResponse(self, callback, errback, response, user_data):
        document = response.find('./st:Document')

        document_rid = response.findtext('./st:ResourceID')
        document_name = response.findtext('./st:Name')
        run(callback, document_rid, document_name)

    def _HandleSOAPResponse(self, request_id, callback, errback, response,
            user_data=None):
        run(callback)

    def _HandleSOAPFault(self, request_id, callback, errback, response,
            user_data=None):
        error = ContentRoamingError.from_fault(response.fault)
        run(errback, error)

    @RequireSecurityTokens(LiveService.STORAGE)
    def __soap_request(self, callback, errback, method, scenario, args):
        token = str(self._tokens[LiveService.STORAGE])
        self._soap_request(method, (scenario, token), args, callback, errback)

    @RequireSecurityTokens(LiveService.STORAGE)
    def get_display_picture(self, callback, errback, pre_auth_url, user_tile_url):
        token = str(self._tokens[LiveService.STORAGE])

        def request_static_tile(error, *args):
            # Request using the PreAuthURL didn't work, try with static tilephoto
            scheme, host, port, resource = url_split(user_tile_url)
            if host:
                self.get_resource(scheme, host, resource, callback, errback)
            else:
                run(errback, error, None)

        scheme, host, port, resource = url_split(pre_auth_url)
        resource += '?t=' + urllib.quote(token.split('&')[0][2:], '')
        self.get_resource(scheme, host, resource, callback,
                (request_static_tile,))

    def get_resource(self, scheme, host, resource, callback, errback):
        http_headers = {}
        http_headers["Accept"] = "*/*"
        http_headers["Proxy-Connection"] = "Keep-Alive"
        http_headers["Connection"] = "Keep-Alive"

        def done_cb(transport, http_response, handles):
            type = http_response.get_header('Content-Type')
            data = http_response.body
            for handle in handles:
                transport.disconnect(handle)
            run(callback, type, data)

        def failed_cb(transport, error, handles):
            for handle in handles:
                transport.disconnect(handle)
            run(errback, error, None)
        
        transport = ProtocolFactory(scheme, host, proxies=self._proxies)

        handles = []
        handles.append(transport.connect("response-received", done_cb, handles))
        handles.append(transport.connect("request-sent", self._request_handler))
        handles.append(transport.connect("error", failed_cb, handles))

        transport.request(resource, http_headers, method='GET')
