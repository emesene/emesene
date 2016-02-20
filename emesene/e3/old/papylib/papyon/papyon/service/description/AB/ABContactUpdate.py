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
from constants import *

import xml.sax.saxutils as xml

def transport_headers():
    """Returns a dictionary, containing transport (http) headers
    to use for the request"""

    return {}

def soap_action():
    """Returns the SOAPAction value to pass to the transport
    or None if no SOAPAction needs to be specified"""

    return "http://www.msn.com/webservices/AddressBook/ABContactUpdate"

def soap_body(contact_id, display_name, is_messenger_user, contact_type,
              first_name, last_name, birth_date, email, phone, location, 
              web_site, annotation, comment, anniversary, has_space,
              enable_allow_list_management=False):
    """Returns the SOAP xml body

        @param contact_id: a contact GUID string
        @param display_name: string
        @param is_messenger_user: "true" if messenger user | 
                                  "false" if live mail contact only
        @param contact_type: 'Me' | 'Regular' | 'Messenger' | 'Messenger2'
        @param first_name: string
        @param last_name: string
        @param birth_date: an ISO 8601 timestamp
        @param email: { ContactEmailType : well-formed email string }
        @param phone: { ContactPhoneType : well-formed phone string }
        @param location: { ContactLocation.Type : { ContactLocation : string } }
        @param web_site: { ContactWebSite : url string }
        @param annotation: { ContactAnnotations : string }
        @param comment: string
        @param anniversary: yyyy/mm/dd
        @param has_space: "true" | "false" """

    contact_info = ""    
    properties_changed = ""

    if display_name is not None:
        contact_info += "<displayName>%s</displayName>" % xml.escape(display_name)
        properties_changed += " DisplayName"

    if has_space is not None:
        contact_info += "<hasSpace>%s</hasSpace>" % has_space
        properties_changed += " HasSpace"
        
    if is_messenger_user is not None:
        contact_info += "<isMessengerUser>%s</isMessengerUser>" % is_messenger_user
        properties_changed += " IsMessengerUser"

    if contact_type is not None:
        contact_info += "<contactType>%s</contactType>" % contact_type
            
    if first_name is not None:
        contact_info += "<firstName>%s</firstName>" % xml.escape(first_name)
        properties_changed += " ContactFirstName"

    if last_name is not None:
        contact_info += "<lastName>%s</lastName>" % xml.escape(last_name)
        properties_changed += " ContactLastName"

    if birth_date is not None:
        contact_info += "<birthdate>%s</birthdate>" % birth_date
        properties_changed += " ContactBirthDate"
    
    if email is not None:
        emails = ""
        for type, email in email.iteritems():
            emails += """<ContactEmail>
                            <contactEmailType>%s</contactEmailType>
                            <email>%s</email>
                            <propertiesChanged>Email</propertiesChanged>
                         </ContactEmail>""" % (type, email)
        contact_info += "<emails>%s</emails>" % emails
        properties_changed += " ContactEmail"

    if phone is not None:
        phones = ""
        for type, number in phone.iteritems():
            phones += """<ContactPhone>
                            <contactPhoneType>%s</contactPhoneType>
                            <number>%s</number>
                            <propertiesChanged>Number</propertiesChanged>
                         </ContactPhone>""" % (type, number)
        contact_info += "<phones>%s</phones>" % phones
        properties_changed += " ContactPhone"

    if location is not None:
        locations = ""
        for type, parts in location.iteritems():
            items = changes = ""
            for item, value in parts.iteritems():
                items += "<%s>%s</%s>" % (item, value, item)
                changes += " %s%s" % (item[0].upper(), item[1:len(item)]) 
            locations += """<ContactLocation>
                               <contactLocationType>%s</contactLocationType>
                               %s
                               <Changes>%s</Changes>
                            </ContactLocation>""" % (type, items, changes)
        contact_info += "<location>%s</locations>" % locations
        properties_changed += " ContactLocation"

    if web_site is not None:
        web_sites = ""
        for type, url in web_site.iteritems():
            websites += """<ContactWebSite>
                              <contactWebSiteType>%s</contactWebSiteType>
                              <webURL>%s</webURL>
                           </ContactWebSite>""" % (type, xml.escape(url))
        contact_info += "<webSites>%s</webSites>" % web_sites
        properties_changed += " ContactWebSite"

    if annotation is not None:
        annotations = ""
        for name, value in annotation.iteritems():
            if value == None or value == "":
                value = "<Value/>"
            else:
                value = "<Value>%s</Value>" % value
            annotations += """<Annotation>
                                 <Name>%s</Name>
                                 %s
                              </Annotation>""" % (name, value)
        contact_info += "<annotations>%s</annotations>" % annotations
        properties_changed += " Annotation"

    if comment is not None:
        contact_info += "<comment>%s</comment>" % xml.escape(comment)
        properties_changed += " Comment"

    if anniversary is not None:
        contact_info += "<Anniversary>%s</Anniversary>" % anniversary
        properties_changed += " Anniversary"

    return """
       <ABContactUpdate xmlns="http://www.msn.com/webservices/AddressBook">
            <abId>00000000-0000-0000-0000-000000000000</abId>
            <contacts>
                <Contact xmlns="http://www.msn.com/webservices/AddressBook">
                    <contactId>
                        %(contact_id)s
                    </contactId>
                    <contactInfo>
                        %(contact_info)s
                    </contactInfo>
                    <propertiesChanged>
                        %(properties_changed)s
                    </propertiesChanged>
                </Contact>
            </contacts>
            <options>
                <EnableAllowListManagement>
                    %(allow_list_management)s
                </EnableAllowListManagement>
            </options>
        </ABContactUpdate>""" % { 'contact_id' : contact_id,
                                  'contact_info' : contact_info,
                                  'properties_changed' : properties_changed,
                                  'allow_list_management' : str(enable_allow_list_management).lower() }

def process_response(soap_response):
    return True
