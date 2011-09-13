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

    return "http://www.hotmail.msn.com/ws/2004/09/oim/rsi/DeleteMessages"

def soap_body(message_ids):
    """Returns the SOAP xml body"""

    ids = ""
    for message_id in message_ids:
        ids += "<messageId>%s</messageId>" %  message_id

    return """
      <DeleteMessages xmlns="http://www.hotmail.msn.com/ws/2004/09/oim/rsi">
          <messageIds>
              %s
          </messageIds>
      </DeleteMessages>""" % ids

def process_response(soap_response):
    return True
