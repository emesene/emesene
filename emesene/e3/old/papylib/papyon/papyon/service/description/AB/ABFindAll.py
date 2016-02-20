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

import xml.sax.saxutils as xml

def transport_headers():
    """Returns a dictionary, containing transport (http) headers
    to use for the request"""

    return {}

def soap_action():
    """Returns the SOAPAction value to pass to the transport
    or None if no SOAPAction needs to be specified"""

    return "http://www.msn.com/webservices/AddressBook/ABFindAll"

def soap_body(deltas_only, last_change):
    """Returns the SOAP xml body"""

    return """
       <ABFindAll xmlns="http://www.msn.com/webservices/AddressBook">
          <abId>00000000-0000-0000-0000-000000000000</abId>
          <abView>Full</abView>
          <deltasOnly>%(deltas_only)s</deltasOnly>
          <lastChange>%(last_change)s</lastChange>
       </ABFindAll>""" % {'deltas_only' : deltas_only,
                          'last_change' : last_change}

def process_response(soap_response):
    find_all_result = soap_response.body.\
            find("./ab:ABFindAllResponse/ab:ABFindAllResult")

    if find_all_result is None:
        return (None, [], [])

    path = "./ab:groups/ab:Group"
    groups = find_all_result.findall(path)

    path = "./ab:contacts/ab:Contact"
    contacts = find_all_result.findall(path)

    path = "./ab:ab"
    ab = find_all_result.find(path)

    return (ab, groups, contacts)
