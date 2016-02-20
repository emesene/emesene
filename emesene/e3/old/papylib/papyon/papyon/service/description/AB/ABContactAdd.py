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

    return "http://www.msn.com/webservices/AddressBook/ABContactAdd"

def soap_body(passport_name, is_messenger_user, contact_type, first_name,
              last_name, birth_date, email, phone, location, web_site,
              annotation, comment, anniversary, display_name, invite_message,
              capability, enable_allow_list_management=True):
    """Returns the SOAP xml body

            @param passport_name: the passport adress if the contact to add
            @param is_messenger_user: True if this is a messenger contact,
                otherwise False (only a Live mail contact)
            @param contact_type:: 'Me' | 'Regular' | 'Messenger' | 'Messenger2' 
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
            @param display_name: display name used in the invitation
            @param invite_message: message sent for the invitation"""

    contact_info = ''
    if passport_name is not None:
        contact_info += "<passportName>%s</passportName>" % passport_name

    if is_messenger_user is not None:
        contact_info += "<isMessengerUser>%s</isMessengerUser>" % is_messenger_user

    if contact_type is not None:
        contact_info += "<contactType>%s</contactType>" % contact_type

    if first_name is not None:
        contact_info += "<firstName>%s</firstName>" % xml.escape(first_name)

    if last_name is not None:
        contact_info += "<lastName>%s</lastName>" % xml.escape(last_name)

    if birth_date is not None:
        contact_info += "<birthdate>%s</birthdate>" % birth_date

    if email is not None:
        emails = ""
        for type, email in email.iteritems():
            yahoo_tags = changed = ""
            if type == ContactEmailType.EXTERNAL:
                yahoo_tags = """<isMessengerEnabled>
                                   true
                                </isMessengerEnabled>
                                <Capability>
                                   %s
                                </Capability>""" % capability
                changed = " IsMessengerEnabled Capability"
            emails += """<ContactEmail>
                            <contactEmailType>%s</contactEmailType>
                            <email>%s</email>
                            %s
                            <propertiesChanged>Email%s</propertiesChanged>
                         </ContactEmail>""" % (type, email, yahoo_tags, changed)
        contact_info += "<emails>%s</emails>" % emails

    if phone is not None:
        phones = ""
        for type, number in phone.iteritems():
            phones += """<ContactPhone>
                            <contactPhoneType>%s</contactPhoneType>
                            <number>%s</number>
                            <propertiesChanged>Number</propertiesChanged>
                         </ContactPhone>""" % (type, number)
        contact_info += "<phones>%s</phones>" % phones

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

    if web_site is not None:
        web_sites = ""
        for type, url in web_site.iteritems():
            web_sites += """<ContactWebSite>
                               <contactWebSiteType>%s</contactWebSiteType>
                               <webURL>%s</webURL>
                            </ContactWebSite>""" % (type, xml.escape(url))
        contact_info += "<webSites>%s</webSites>" % web_sites

    if annotation is not None:
        annotations = ""
        for name, value in annotation.iteritems():
            annotations += """<Annotation>
                                 <Name>%s</Name>
                                 <Value>%s</Value>
                              </Annotation>""" % (name, xml.escape(value))
        contact_info += "<annotations>%s</annotations>" % annotations

    if comment is not None:
        contact_info += "<comment>%s</comment>" % xml.escape(comment)

    if anniversary is not None:
        contact_info += "<Anniversary>%s</Anniversary>" % anniversary

    invite_info = ''
    invite_info += """<MessengerMemberInfo>
                           <PendingAnnotations>
                               <Annotation>
                                   <Name>
                                       MSN.IM.InviteMessage
                                   </Name>
                                   <Value>
                                       %(invite_message)s
                                   </Value>
                               </Annotation>
                           </PendingAnnotations>
                           <DisplayName>
                               %(display_name)s
                           </DisplayName>
                       </MessengerMemberInfo>""" % { 'invite_message' : xml.escape(invite_message),
                                                     'display_name' : xml.escape(display_name) }

    return """
       <ABContactAdd xmlns="http://www.msn.com/webservices/AddressBook">
            <abId>00000000-0000-0000-0000-000000000000</abId>
            <contacts>
                <Contact xmlns="http://www.msn.com/webservices/AddressBook">
                    <contactInfo>
                        %(contact_info)s
                        %(invite_info)s
                    </contactInfo>
                </Contact>
            </contacts>
            <options>
                <EnableAllowListManagement>
                    %(allow_list_management)s
                </EnableAllowListManagement>
            </options>
        </ABContactAdd>""" % { 'contact_info' : contact_info,
                               'invite_info' : invite_info,
                               'allow_list_management' : str(enable_allow_list_management).lower()}

def process_response(soap_response):
    return soap_response.body.\
            find("./ab:ABContactAddResponse/ab:ABContactAddResult/ab:guid").text
