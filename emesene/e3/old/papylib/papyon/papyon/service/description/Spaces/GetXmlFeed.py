# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Youness Alaoui <kakaroto@users.sourceforge.net>
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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

import xml.sax.saxutils as xml

#from papyon.util.element_tree import XMLTYPE

def soap_header(security_token):
    """Returns the SOAP xml header"""

    return """
         <AuthTokenHeader xmlns="http://www.msn.com/webservices/spaces/v1/">
            <Token>%s
            </Token>
         </AuthTokenHeader>""" % (xml.escape(security_token))

def transport_headers():
    """Returns a dictionary, containing transport (http) headers
    to use for the request"""

    return {}

def soap_action():
    """Returns the SOAPAction value to pass to the transport
    or None if no SOAPAction needs to be specified"""

    return "http://www.msn.com/webservices/spaces/v1/GetXmlFeed"

def soap_body(cid, market = "en-US", max_elements = 2, max_chars = 200, max_images = 6):
    """Returns the SOAP xml body"""
    # , last_viewed, app_id = "Messenger Client 8.0", update_access_time = True, is_active_contact = False
    return """
       <GetXmlFeed xmlns="http://www.msn.com/webservices/spaces/v1/">
          <refreshInformation>
             <cid xmlns="http://www.msn.com/webservices/spaces/v1/">%(cid)s</cid>
             <storageAuthCache></storageAuthCache>
             <market xmlns="http://www.msn.com/webservices/spaces/v1/">%(market)s</market>
             <brand></brand>
             <maxElementCount xmlns="http://www.msn.com/webservices/spaces/v1/">%(max_element_count)d</maxElementCount>
             <maxCharacterCount xmlns="http://www.msn.com/webservices/spaces/v1/">%(max_character_count)d</maxCharacterCount>
             <maxImageCount xmlns="http://www.msn.com/webservices/spaces/v1/">%(max_image_count)d</maxImageCount>
          </refreshInformation>
       </GetXmlFeed>
       """ % {'cid' : cid,
              'market' : market,
              'max_element_count' : max_elements,
              'max_character_count' : max_chars,
              'max_image_count' : max_images}

#             <applicationId>%(application_id)s</applicationId>
#             <updateAccessedTime>%(update_accessed_time)s</updateAccessedTime>
#             <spaceLastViewed>%(space_last_viewed)s</spaceLastViewed>
#             <isActiveContact>%(is_active_contact)s</isActiveContact>

#              'appliation_id' : app_id,
#              'update_accessed_time' : XMLTYPE.boolean.encode(update_access_time),
#              'space_last_viewed' : last_viewed,
#              'is_active_contact' : XMLTYPE.boolean.encode(is_active_contact)

def process_response(soap_response):
    body = soap_response.body
    return body.find("./spaces:GetXmlFeedResponse/spaces:GetXmlFeedResult")
