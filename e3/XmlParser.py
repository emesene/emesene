# -*- coding: utf-8 -*-
'''parse the xml files from the server'''

#   This file is part of emesene.
#
#    Emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    emesene is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with emesene; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import xml.parsers.expat

class DynamicParser:
    '''Parse dynamic xml'''
    def __init__(self, xml_raw):
        '''init parser and setup handlers'''
        self.parser = xml.parsers.expat.ParserCreate()
        self.parser.buffer_text = True
        self.parser.returns_unicode = False
        
        self.groups = []
        self.contacts = []
        self.annotations = []
        self.group_ids = []
        
        self.in_group = False
        self.in_contact = False
        self.in_annotation = False
        self.in_group_ids = False
        
        self.group_data = {}
        self.contact_data = {}
        self.annotation_data = {}
        self.group_ids_data = {}
        
        self.current_tag = ''
        
        #connect handlers
        self.parser.StartElementHandler = self.start_element
        self.parser.EndElementHandler = self.end_element
        self.parser.CharacterDataHandler = self.char_data
        self.parser.Parse(xml_raw)
                
        del(xml_raw)
        
    def start_element(self, name, attrs):
        '''Start xml element handler'''
        if name == 'Group':
            self.in_group = True
        elif name == 'Contact':
            self.in_contact = True
        elif name == 'Annotation':
            self.in_annotation = True
        elif name == 'groupIds':
            self.in_group_ids = True
        self.current_tag = name
        
    def end_element(self, name):
        '''End xml element handler'''
        if name == 'Group':
            self.in_group = False
            if len(self.group_data) > 0:
                if len(self.annotations) > 0:
                    self.group_data.update({'Annotations':self.annotations})
                    self.annotations = []
                self.groups.append(self.group_data)
                self.group_data = {}
        elif name == 'Contact':
            self.in_contact = False
            if len(self.contact_data) > 0:
                annotations = self.annotations
                self.contact_data.update({'Annotations':annotations})
                self.contact_data.update({'groupIds':self.group_ids})
                self.contacts.append(self.contact_data)
                self.contact_data = {}
                self.annotations = []
                self.group_ids = []
        elif name == 'Annotation':
            self.in_annotation = False
            if len(self.annotation_data) > 0:
                self.annotations.append(self.annotation_data)
                self.annotation_data = {}
        elif name == 'groupIds':
            self.in_group_ids = False
            if len(self.group_ids_data) > 0:
                self.group_ids.append(self.group_ids_data)
                self.group_ids_data = {}

    def char_data(self, data):
        '''Char xml element handler'''
        if self.in_group_ids:
            self.group_ids.append(data)
        elif self.in_annotation:
            self.annotation_data.update({self.current_tag:data})
        elif self.in_group:
            self.group_data.update({self.current_tag:data})
        elif self.in_contact:
            self.contact_data.update({self.current_tag:data})

class MembershipParser:
    '''Parse membership xml'''
    def __init__(self, xml_raw):
        '''init parser and setup handlers'''
        self.parser = xml.parsers.expat.ParserCreate()
        self.parser.buffer_text = True
        self.parser.returns_unicode = False
        
        self.memberships = []
        self.members = []
        
        self.in_membership = False
        self.in_member = False
        
        self.membership_data = {}
        self.member_data = {}
        
        self.current_tag = ''
        
        #connect handlers
        self.parser.StartElementHandler = self.start_element
        self.parser.EndElementHandler = self.end_element
        self.parser.CharacterDataHandler = self.char_data
        self.parser.Parse(xml_raw)
        del(xml_raw)
        
    def start_element(self, name, attrs):
        '''Start xml element handler'''
        if name == 'Membership':
            self.in_membership = True
        elif name == 'Member':
            self.in_member = True
        self.current_tag = name
        
    def end_element(self, name):
        '''End xml element handler'''
        if name == 'Membership':
            self.in_membership = False
            if len(self.membership_data) > 0:
                self.membership_data.update({'Members':self.members})
                self.memberships.append(self.membership_data)
                self.membership_data = {}
                self.members = []
        if name == 'Member':
            self.in_member = False
            if len(self.member_data) > 0:
                self.members.append(self.member_data)
                self.member_data = {}

    def char_data(self, data):
        '''Char xml element handler'''
        if self.in_member:
            self.member_data.update({self.current_tag:data})
        elif self.in_membership:
            self.membership_data.update({self.current_tag:data})

class SSoParser:
    '''Parse sso xml'''
    def __init__(self, xml_raw):
        '''init parser and setup handlers'''
        self.parser = xml.parsers.expat.ParserCreate()
        self.parser.buffer_text = True
        self.parser.returns_unicode = False
        
        self.tokens = {}
        
        self.in_token_response = False
        self.in_address = False
        self.in_binary_secret = False
        self.in_binary_security = False
        
        self.current_tag = ''
        self.current_token = ''
        
        #connect handlers
        self.parser.StartElementHandler = self.start_element
        self.parser.EndElementHandler = self.end_element
        self.parser.CharacterDataHandler = self.char_data
        self.parser.Parse(xml_raw)
        del(xml_raw)
        
    def start_element(self, name, attrs):
        '''Start xml element handler'''
        if name == 'RequestSecurityTokenResponse':
            self.in_token_response = True
        elif name == 'wsa:Address':
            self.in_address = True
        elif name == 'wst:BinarySecret':
            self.in_binary_secret = True
        elif name == 'wsse:BinarySecurityToken':
            self.in_binary_security = True
        self.current_tag = name
        
    def end_element(self, name):
        '''End xml element handler'''
        if name == 'RequestSecurityTokenResponse':
            self.in_token_response = False
        elif name == 'wsa:Address':
            self.in_address = False
        elif name == 'wst:BinarySecret':
            self.in_binary_secret = False
        elif name == 'wsse:BinarySecurityToken':
            self.in_binary_security = False

    def char_data(self, data):
        '''Char xml element handler'''
        if self.in_address:
            self.tokens.update({data:{}})
            self.current_token = data
        elif self.in_binary_secret:
            self.tokens[self.current_token].update({'secret':data})
        elif self.in_binary_security:
            self.tokens[self.current_token].update({'security':data})
