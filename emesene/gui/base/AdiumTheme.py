'''a module that contains a class that describes a adium theme'''
# -*- coding: utf-8 -*-

#    This file is part of emesene.
#
#    emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
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

import re
import os
import time, calendar
import datetime
import xml.sax.saxutils

import parsers
import MarkupParser

class AdiumTheme(object):
    '''a class that contains information of a adium theme
    '''

    def __init__(self, path, timefmt, variant):
        '''constructor

        get information from the theme located in path
        '''
        self.timefmt        = timefmt
        self.path           = None
        self.resources_path = None
        self.incoming_path  = None
        self.outgoing_path  = None
        self.content        = None
        self.incoming       = None
        self.incoming_next  = None
        self.outgoing       = None
        self.outgoing_next  = None
        self.info           = None

        self.variant        = variant
        self.load_information(path)

    def load_information(self, path):
        '''load the information of the theme on path
        '''
        self.path = path

        info_file = file(os.path.join(path, 'Contents', 'Info.plist'))
        self.info = parsers.Plist(info_file).info

        self.resources_path = os.path.join(path, 'Contents', 'Resources')
        self.incoming_path = os.path.join(self.resources_path, 'Incoming')
        self.outgoing_path = os.path.join(self.resources_path, 'Outgoing')

        self.content = read_file(self.resources_path, 'Content.html')
        self.status = read_file(self.resources_path, 'Status.html')

        self.incoming = read_file(self.incoming_path, 'Content.html')
        self.incoming_next = read_file(self.incoming_path,
                'NextContent.html')

        self.outgoing = read_file(self.outgoing_path, 'Content.html')
        self.outgoing_next = read_file(self.outgoing_path,
                'NextContent.html')

    def format_incoming(self, msg, style=None, cedict={}, cedir=None):
        '''return a string containing the template for the incoming message
        with the vars replaced
        '''
        # fallback madness, some repetition but well..
        if (msg.type == "status" and self.status):
            template = self.status
        elif not msg.first:
            if self.incoming_next is None:
                if self.incoming is None:
                    template = self.content
                else:
                    template = self.incoming
            else:
                template = self.incoming_next
        elif self.incoming is None:
            template = self.content
        else:
            template = self.incoming

        return self.replace(template, msg, style, cedict, cedir)

    def format_outgoing(self, msg, style=None, cedict={}, cedir=None):
        '''return a string containing the template for the outgoing message
        with the vars replaced
        '''
        # fallback madness, some repetition but well..
        if (msg.type == "status" and self.status):
            template = self.status
        elif not msg.first:
            if self.outgoing_next is None:
                if self.outgoing is None:
                    if self.incoming is None:
                        template = self.content
                    else:
                        template = self.incoming
                else:
                    template = self.outgoing
            else:
                template = self.outgoing_next
        elif self.outgoing is None:
            if self.incoming is None:
                template = self.content
            else:
                template = self.incoming
        else:
            template = self.outgoing

        return self.replace(template, msg, style, cedict, cedir)

    def replace(self, template, msg, style=None, cedict={}, cedir=None):
        '''replace the variables on template for the values on msg
        '''

        msgtext = MarkupParser.replace_emotes(escape(msg.message), cedict, cedir, msg.sender)
        msgtext = MarkupParser.urlify(msgtext)
        image_path = escape(MarkupParser.path_to_url(msg.image_path))
        status_path = escape(MarkupParser.path_to_url(msg.status_path))

        if style is not None:
            msgtext = style_message(msgtext, style)
        if msg.alias:
            template = template.replace('%sender%', escape(msg.alias))
        else:
            template = template.replace('%sender%', escape(msg.display_name))

        template = template.replace('%senderScreenName%', escape(msg.sender))
        template = template.replace('%senderDisplayName%',
            escape(msg.display_name))
        template = template.replace('%userIconPath%', image_path)
        template = template.replace('%senderStatusIcon%',
            status_path)
        template = template.replace('%messageDirection%',
            escape(msg.direction))
        template = template.replace('%message%', msgtext)

        if msg.timestamp is None:
            template = template.replace('%time%',
                escape(time.strftime(self.timefmt)))
        else:
            def utc_to_local(t):
                secs = calendar.timegm(t)
                return time.localtime(secs)
            l_time = utc_to_local(msg.timestamp.timetuple()) #time.struct_time
            d_time = datetime.datetime.fromtimestamp(time.mktime(l_time))
            template = template.replace('%time%',
                escape(d_time.strftime('%x %X')))

        template = re.sub("%time{(.*?)}%", replace_time, template)
        template = template.replace('%shortTime%',
            escape(time.strftime("%H:%M")))
        template = template.replace('%service%', escape(msg.service))
        template = template.replace('%messageClasses%', escape(msg.classes))
        template = template.replace('%status%', escape(msg.status))

        return template.replace('\n', '')

    def replace_header_or_footer(self, template, source, target,
            target_display, source_img, target_img):
        '''replace the variables on template for the parameters
        '''

        template = template.replace('%chatName%', escape(target))
        template = template.replace('%sourceName%', escape(source))
        template = template.replace('%destinationName%', escape(target))
        template = template.replace('%destinationDisplayName%',
            escape(target_display))
        template = template.replace('%incomingIconPath%', escape(target_img))
        template = template.replace('%outgoingIconPath%', escape(source_img))
        template = template.replace('%timeOpened%',
            escape(time.strftime("%H:%M")))
        # TODO: use the format inside the {}
        template = re.sub("%timeOpened{.*?}%", escape(time.strftime("%H:%M")),
            template)

        return template

    def get_body(self, source, target, target_display, source_img, target_img):
        '''return the template to put as html content
        '''
        #first try load custom Template.html from theme
        path = urljoin(self.resources_path, 'Template.html')
        if not os.path.exists(path):
            path = urljoin("gui", "base", "template.html")
        template = read_file(path)
        resources_url = MarkupParser.path_to_url(self.resources_path)
        css_path = urljoin(resources_url, "main.css")

        if self.variant:
            variant_name = self.variant
        else:
            variant_name = self.info.get('DefaultVariant', None)
        template = template.replace("%@", resources_url + "/", 1)
        template = template.replace("%@", css_path, 1)

        if variant_name is not None:
            variant_css_path = urljoin(resources_url,
                    "Variants", variant_name + ".css")
            variant_tag = '<style id="mainStyle" type="text/css"' + \
                'media="screen,print">	@import url( "' + variant_css_path + '" ); </style>'
        else:
            variant_tag = ""

        template = template.replace("%@", variant_tag, 1)

        header = read_file(self.resources_path, 'Header.html') or ""

        if header:
            header = self.replace_header_or_footer(header, source, target,
                    target_display, source_img, target_img)

        template = template.replace("%@", header, 1)
        footer = read_file(self.resources_path, 'Footer.html') or ""

        if footer:
            footer = self.replace_header_or_footer(footer, source, target,
                    target_display, source_img, target_img)

        template = template.replace("%@", footer, 1)

        return template

    def get_theme_variants(self):
        variants = []
        path_variants = os.path.join(self.resources_path, 'Variants')
        for root, dirs, files in os.walk(path_variants):
            for f in files:
                basename, extension = os.path.splitext(str(f))
                if extension == ".css":
                    variants.append(basename)
        return variants

def read_file(*args):
    '''read file if exists and is readable, return None otherwise
    '''
    path = os.path.join(*args)
    if os.access(path, os.R_OK):
        return file(path).read()

    return None

def urljoin(*args):
    return "/".join(list(args))

__dic = {
    '\"': '&quot;',
    '\'': '&apos;',
    '\\': '\\\\',
    '\r\n': '<br>', #windows
    '\r': '<br>', #osx
    '\n': '<br>' #linux
}

__dic_inv = {
    '&quot;' :'\"',
    '&apos;' :'\'',
    '<br>':    '\n'
}

def escape(string_):
    '''replace the values on dic keys with the values'''
    return xml.sax.saxutils.escape(string_, __dic)

def unescape(string_):
    '''replace the values on dic_inv keys with the values'''
    return xml.sax.saxutils.unescape(string_, __dic_inv)

def replace_time(match):
    '''replace the format of the time to it's value'''
    return time.strftime(match.groups()[0])

def style_message(msgtext, style):
    '''add html markupt to msgtext to format the style of the message'''
    return '<span style="%s">%s</span>' % (style.to_css(), msgtext)
