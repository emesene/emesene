# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2005-2006 Ali Sabil <ali.sabil@gmail.com>
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

import xml.sax.saxutils as xml

class LiveService(object):
    CONTACTS = ("contacts.msn.com", "MBI")
    MESSENGER = ("messenger.msn.com", "?id=507")
    MESSENGER_CLEAR = ("messengerclear.live.com", "MBI_KEY_OLD")
    MESSENGER_SECURE = ("messengersecure.live.com", "MBI_SSL")
    SPACES = ("spaces.live.com", "MBI")
    STORAGE = ("storage.msn.com", "MBI")
    TB = ("http://Passport.NET/tb", None)
    VOICE = ("voice.messenger.msn.com", "?id=69264")

    @classmethod
    def url_to_service(cls, url):
        for attr_name in dir(cls):
            if attr_name.startswith('_'):
                continue
            attr = getattr(cls, attr_name)
            if isinstance(attr, tuple) and attr[0] == url:
                return attr
        return None

def transport_headers():
    """Returns a dictionary, containing transport (http) headers
    to use for the request"""

    return {}

def soap_action():
    """Returns the SOAPAction value to pass to the transport
    or None if no SOAPAction needs to be specified"""

    return None

def soap_header(account, password):
    """Returns the SOAP xml header"""

    return """
        <ps:AuthInfo xmlns:ps="http://schemas.microsoft.com/Passport/SoapServices/PPCRL" Id="PPAuthInfo">
        <ps:HostingApp>{7108E71A-9926-4FCB-BCC9-9A9D3F32E423}</ps:HostingApp>
        <ps:BinaryVersion>4</ps:BinaryVersion>
        <ps:UIVersion>1</ps:UIVersion>
        <ps:Cookies/>
        <ps:RequestParams>AQAAAAIAAABsYwQAAAAxMDMz</ps:RequestParams>
        </ps:AuthInfo>
        <wsse:Security xmlns:wsse="http://schemas.xmlsoap.org/ws/2003/06/secext">
        <wsse:UsernameToken Id="user">
            <wsse:Username>%(account)s</wsse:Username>
            <wsse:Password>%(password)s</wsse:Password>
        </wsse:UsernameToken>
        </wsse:Security>""" % {'account': xml.escape(account),
                'password': xml.escape(password)}

def soap_body(*tokens):
    """Returns the SOAP xml body"""

    token_template = """
        <wst:RequestSecurityToken xmlns:wst="http://schemas.xmlsoap.org/ws/2004/04/trust" Id="RST%(id)d">
            <wst:RequestType>http://schemas.xmlsoap.org/ws/2004/04/security/trust/Issue</wst:RequestType>
            <wsp:AppliesTo xmlns:wsp="http://schemas.xmlsoap.org/ws/2002/12/policy">
                <wsa:EndpointReference xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/03/addressing">
                    <wsa:Address>%(address)s</wsa:Address>
                </wsa:EndpointReference>
            </wsp:AppliesTo>
            %(policy_reference)s
        </wst:RequestSecurityToken>"""
    policy_reference_template = """
        <wsse:PolicyReference xmlns:wsse="http://schemas.xmlsoap.org/ws/2003/06/secext" URI=%(uri)s/>"""

    tokens = list(tokens)
    if LiveService.TB in tokens:
        tokens.remove(LiveService.TB)

    assert(len(tokens) >= 1)
    
    body = token_template % \
            {'id': 0,
                'address': xml.escape(LiveService.TB[0]),
                'policy_reference': ''}

    for id, token in enumerate(tokens):
        if token[1] is not None:
            policy_reference = policy_reference_template % \
                    {'uri': xml.quoteattr(token[1])}
        else:
            policy_reference = ""

        t = token_template % \
                {'id': id + 1,
                    'address': xml.escape(token[0]),
                    'policy_reference': policy_reference}
        body += t

    return '<ps:RequestMultipleSecurityTokens ' \
        'xmlns:ps="http://schemas.microsoft.com/Passport/SoapServices/PPCRL" ' \
        'Id="RSTS">%s</ps:RequestMultipleSecurityTokens>' % body

def process_response(soap_response):
    body = soap_response.body
    return body.findall("./wst:RequestSecurityTokenResponseCollection/" \
            "wst:RequestSecurityTokenResponse")

