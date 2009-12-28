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

import xml.sax.saxutils as xml

def soap_header(scenario, security_token):
    """Returns the SOAP xml header"""

    return """<StorageApplicationHeader xmlns="http://www.msn.com/webservices/storage/w10">
            <ApplicationID>Messenger Client 8.0</ApplicationID>
            <Scenario>
                %s
            </Scenario>
        </StorageApplicationHeader>
        <StorageUserHeader xmlns="http://www.msn.com/webservices/storage/w10">
            <Puid>0</Puid>
            <TicketToken>
                %s
            </TicketToken>
        </StorageUserHeader>""" % (xml.escape(scenario), xml.escape(security_token))
