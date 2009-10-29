# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2005-2007 Ali Sabil <ali.sabil@gmail.com>
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


__all__ = ['XMLNS']

class XMLNS(object):

    class SOAP(object):
        ENVELOPE = "http://schemas.xmlsoap.org/soap/envelope/"
        ENCODING = "http://schemas.xmlsoap.org/soap/encoding/"
        ACTOR_NEXT = "http://schemas.xmlsoap.org/soap/actor/next"
    
    class SCHEMA(object):
        XSD1 = "http://www.w3.org/1999/XMLSchema"
        XSD2 = "http://www.w3.org/2000/10/XMLSchema"
        XSD3 = "http://www.w3.org/2001/XMLSchema"
        
        XSI1 = "http://www.w3.org/1999/XMLSchema-instance"
        XSI2 = "http://www.w3.org/2000/10/XMLSchema-instance"
        XSI3 = "http://www.w3.org/2001/XMLSchema-instance"

    class ENCRYPTION(object):
        BASE = "http://www.w3.org/2001/04/xmlenc#"
    
    class WS:
        SECEXT = "http://schemas.xmlsoap.org/ws/2003/06/secext"
        TRUST = "http://schemas.xmlsoap.org/ws/2004/04/trust"
        ADDRESSING = "http://schemas.xmlsoap.org/ws/2004/03/addressing"
        POLICY = "http://schemas.xmlsoap.org/ws/2002/12/policy"
        ISSUE = "http://schemas.xmlsoap.org/ws/2004/04/security/trust/Issue"
        UTILITY = "http://docs.oasis-open.org/wss/2004/01/" + \
                "oasis-200401-wss-wssecurity-utility-1.0.xsd"
    
    class MICROSOFT:
        PASSPORT = "http://schemas.microsoft.com/Passport/SoapServices/PPCRL"
        PASSPORT_FAULT = "http://schemas.microsoft.com/Passport/SoapServices/SOAPFault"

        class LIVE:
            ADDRESSBOOK = "http://www.msn.com/webservices/AddressBook"
            STORAGE = "http://www.msn.com/webservices/storage/w10"
            OIM = "http://messenger.msn.com/ws/2004/09/oim/"
            RSI = "http://www.hotmail.msn.com/ws/2004/09/oim/rsi"
            SPACES = "http://www.msn.com/webservices/spaces/v1/"
