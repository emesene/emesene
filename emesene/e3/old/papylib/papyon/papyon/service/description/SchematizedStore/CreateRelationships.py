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

from common import *

def transport_headers():
    """Returns a dictionary, containing transport (http) headers
    to use for the request"""

    return {}

def soap_action():
    """Returns the SOAPAction value to pass to the transport
    or None if no SOAPAction needs to be specified"""

    return "http://www.msn.com/webservices/storage/w10/CreateRelationships"

def soap_body(source_rid, target_rid):
    """Returns the SOAP xml body
    """
    return """<CreateRelationships xmlns="http://www.msn.com/webservices/storage/w10">
            <relationships>
                <Relationship>
                    <SourceID>
                        %s
                    </SourceID>
                    <SourceType>
                        SubProfile
                    </SourceType>
                    <TargetID>
                        %s
                    </TargetID>
                    <TargetType>
                        Photo
                    </TargetType>
                    <RelationshipName>
                        ProfilePhoto
                    </RelationshipName>
                </Relationship>
            </relationships>
        </CreateRelationships>""" % (source_rid, target_rid)

def process_response(soap_response):
    return True
