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

__all__ = ['soap_header']

def soap_header(scenario, security_token):
    """Returns the SOAP xml header"""

    return """
        <ABApplicationHeader xmlns="http://www.msn.com/webservices/AddressBook">
           <ApplicationId xmlns="http://www.msn.com/webservices/AddressBook">CFE80F9D-180F-4399-82AB-413F33A1FA11</ApplicationId>
           <IsMigration xmlns="http://www.msn.com/webservices/AddressBook">false</IsMigration>
           <PartnerScenario xmlns="http://www.msn.com/webservices/AddressBook">%s</PartnerScenario>
       </ABApplicationHeader>
       <ABAuthHeader xmlns="http://www.msn.com/webservices/AddressBook">
           <ManagedGroupRequest xmlns="http://www.msn.com/webservices/AddressBook">false</ManagedGroupRequest>
           <TicketToken xmlns="http://www.msn.com/webservices/AddressBook">%s</TicketToken>
       </ABAuthHeader>""" % (xml.escape(scenario), xml.escape(security_token))
