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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

import xml.sax.saxutils as xml
def soap_header(from_member_name, friendly_name, proxy, msnp_ver, build_ver,
                to_member_name, message_number, security_token, app_id, 
                lock_key):
    """Returns the SOAP xml header"""

    # FIXME : escape the parameters

    return """<From memberName="%(from_member_name)s" friendlyName="%(friendly_name)s" xml:lang="en-US" proxy="%(proxy)s" xmlns="http://messenger.msn.com/ws/2004/09/oim/" msnpVer="%(msnp_ver)s" buildVer="%(build_ver)s"/>
            <To memberName="%(to_member_name)s" xmlns="http://messenger.msn.com/ws/2004/09/oim/"/>
                <Ticket passport="%(passport)s" appid="%(app_id)s" lockkey="%(lock_key)s" xmlns="http://messenger.msn.com/ws/2004/09/oim/"/>
                <Sequence xmlns="http://schemas.xmlsoap.org/ws/2003/03/rm">
                    <Identifier xmlns="http://schemas.xmlsoap.org/ws/2002/07/utility">
                        http://messenger.msn.com
                    </Identifier>
                    <MessageNumber>%(message_number)s</MessageNumber>
                </Sequence>""" % { 'from_member_name' : from_member_name,
                                 'friendly_name' : friendly_name,
                                 'proxy' : proxy,
                                 'msnp_ver' : msnp_ver,
                                 'build_ver' : build_ver,
                                 'to_member_name' : to_member_name,
                                 'passport' : xml.escape(security_token),
                                 'app_id' : app_id,
                                 'lock_key' : lock_key,
                                 'message_number' : message_number }

def transport_headers():
    """Returns a dictionary, containing transport (http) headers
    to use for the request"""

    return {}

def soap_action():
    """Returns the SOAPAction value to pass to the transport
    or None if no SOAPAction needs to be specified"""

    return "http://messenger.live.com/ws/2006/09/oim/Store2"

def soap_body(message_type, message_content):
    """Returns the SOAP xml body"""

    return """<MessageType xmlns="http://messenger.msn.com/ws/2004/09/oim/">
            %s
            </MessageType>
            <Content xmlns="http://messenger.msn.com/ws/2004/09/oim/">
            %s
            </Content>""" % (message_type, message_content)

def process_response(soap_response):
    return True
