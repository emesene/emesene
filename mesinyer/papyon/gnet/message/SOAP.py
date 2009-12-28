# -*- coding: utf-8 -*-
#
# Copyright (C) 2006  Ali Sabil <ali.sabil@gmail.com>
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

"""SOAP Messages structures."""

import papyon.util.element_tree as ElementTree
import papyon.util.string_io as StringIO

__all__=['SOAPRequest', 'SOAPResponse']

class NameSpace:
    SOAP_ENVELOPE = "http://schemas.xmlsoap.org/soap/envelope/"
    SOAP_ENCODING = "http://schemas.xmlsoap.org/soap/encoding/"
    XML_SCHEMA = "http://www.w3.org/1999/XMLSchema"
    XML_SCHEMA_INSTANCE = "http://www.w3.org/1999/XMLSchema-instance"

class Encoding:
    SOAP = "http://schemas.xmlsoap.org/soap/encoding/"

class _SOAPSection:
    ENVELOPE = "{" + NameSpace.SOAP_ENVELOPE + "}Envelope"
    HEADER = "{" + NameSpace.SOAP_ENVELOPE + "}Header"
    BODY = "{" + NameSpace.SOAP_ENVELOPE + "}Body"


class _SOAPElement(object):
    def __init__(self, element):
        self.element = element

    def append(self, tag, namespace=None, type=None, attrib={}, value=None, **kwargs):
        if namespace is not None:
            tag = "{" + namespace + "}" + tag
        if type:
            if isinstance(type, str):
                type = ElementTree.QName(type, NameSpace.XML_SCHEMA)
            else:
                type = ElementTree.QName(type[1], type[0])
            attrib["{" + NameSpace.XML_SCHEMA_INSTANCE + "}type"] = type

        child = ElementTree.SubElement(self.element, tag, attrib, **kwargs)
        child.text = value
        return _SOAPElement(child)

    def __str__(self):
        return ElementTree.tostring(self.element, "utf-8")


class SOAPRequest(object):
    """Abstracts a SOAP Request to be sent to the server"""

    def __init__(self, method, namespace=None, encoding_style=Encoding.SOAP, **attr):
        """Initializer
        
        @param method: the method to be called
        @type method: string

        @param namespace: the namespace that the method belongs to
        @type namespace: URI
        
        @param encoding_style: the encoding style for this method
        @type encoding_style: URI
        
        @param attr: attributes to be attached to the method"""
        self.header = ElementTree.Element(_SOAPSection.HEADER)
        if namespace is not None:
            method = "{" + namespace + "}" + method
        self.method = ElementTree.Element(method)
        if encoding_style is not None:
            self.method.set("{" + NameSpace.SOAP_ENVELOPE + "}encodingStyle", encoding_style)

        for attr_key, attr_value in attr.iteritems():
            self.method.set(attr_key, attr_value)
    
    def add_argument(self, name, namespace=None, type=None, attrib=None, value=None, **kwargs):
        if namespace is not None:
            name = "{" + namespace + "}" + name
        return self._add_element(self.method, name, type, attrib, value, **kwargs)

    def add_header(self, name, namespace=None, attrib=None, value=None, **kwargs):
        if namespace is not None:
            name = "{" + namespace + "}" + name
        return self._add_element(self.header, name, None, attrib, value, **kwargs)
    
    def _add_element(self, parent, name, type=None, attributes=None, value=None, **kwargs):
        elem = ElementTree.SubElement(parent, name)
        if attributes is None:
            attributes = {}
        attributes.update(kwargs)
        if type:
            type = self._qname(type, NameSpace.XML_SCHEMA)
            elem.set("{" + NameSpace.XML_SCHEMA_INSTANCE + "}type", type)
        for attr_key, attr_value in attributes.iteritems():
            elem.set(attr_key, attr_value)
        elem.text = value
        return _SOAPElement(elem)
    
    def _qname(self, name, default_ns):
        if name[0] != "{":
            return ElementTree.QName(default_ns, name)
        return ElementTree.QName(name)
    
    def __str__(self):
        envelope = ElementTree.Element(_SOAPSection.ENVELOPE)
        if len(self.header) > 0:
            envelope.append(self.header)
        body = ElementTree.SubElement(envelope, _SOAPSection.BODY)
        body.append(self.method)
        return "<?xml version=\"1.0\" encoding=\"utf-8\"?>" +\
                ElementTree.tostring(envelope, "utf-8")
    
    def __repr__(self):
        return "<SOAP request %s>" % self.method.tag


class SOAPResponse(object):
    def __init__(self, data):
        self.tree = self._parse(data)
        self.header = self.tree.find(_SOAPSection.HEADER)
        self.body = self.tree.find(_SOAPSection.BODY)

    def find(self, path):
        return self.tree.find(path)

    def _parse(self, data):
        events = ("start", "end", "start-ns", "end-ns")
        ns = []
        data = StringIO.StringIO(data)
        context = ElementTree.iterparse(data, events=events)
        for event, elem in context:
            if event == "start-ns":
                ns.append(elem)
            elif event == "end-ns":
                ns.pop()
            elif event == "start":
                elem.set("(xmlns)", tuple(ns))
        data.close()
        return context.root

