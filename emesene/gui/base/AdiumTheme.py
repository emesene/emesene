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
import e3
from e3.common.MetaData import MetaData

import parsers
import MarkupParser
import Plus

DISPLAY_NAME_LIMIT = 25

class AdiumTheme(MetaData):
    '''a class that contains information of a adium theme
    '''

    def __init__(self, path, variant):
        '''constructor

        get information from the theme located in path
        '''
        MetaData.__init__(self, path)
        self.path = None
        self.resources_path = None
        self.incoming_path = None
        self.outgoing_path = None
        self.content = None
        self.incoming = None
        self.incoming_next = None
        self.outgoing = None
        self.outgoing_next = None
        self.history_in = None
        self.history_in_next = None
        self.history_out = None
        self.history_out_next = None

        self._variant = None
        self.default_variant = None
        self.load_information(path, variant)

    def load_information(self, path, variant):
        '''load the information of the theme on path
        '''
        self.path = path

        info_file = file(os.path.join(path, 'Contents', 'Info.plist'))
        info = parsers.Plist(info_file).info
        self.default_variant = info.get('DefaultVariant', None)
        self.variant = variant
        self.theme_version = info.get('MessageViewVersion', 0)

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

        self.history_in = read_file(self.incoming_path, 'Context.html')
        self.history_in_next = read_file(self.incoming_path,
                'NextContext.html')

        self.history_out = read_file(self.outgoing_path, 'Context.html')
        self.history_out_next = read_file(self.outgoing_path,
                'NextContext.html')

        #setup incoming template fallback
        if self.incoming is None:
            self.incoming = self.content
        if self.incoming_next is None:
            self.incoming_next = self.incoming

        #setup incoming template fallback
        if self.outgoing is None:
            self.outgoing = self.incoming
        if self.outgoing_next is None:
            self.outgoing_next = self.outgoing

        #setup history template fallback
        if (self.history_in is None):
            self.history_in = self.incoming
        if (self.history_in_next is None):
            self.history_in_next = self.incoming_next

        if (self.history_out is None):
            self.history_out = self.outgoing
        if (self.history_out_next is None):
            self.history_out_next = self.outgoing_next

        #first try load custom Template.html from theme
        template_path = urljoin(self.resources_path, 'Template.html')
        if not os.path.exists(template_path):
            template_path = urljoin("gui", "base", "template.html")
        self.template = read_file(template_path)

        self.header = read_file(self.resources_path, 'Header.html') or ""
        self.footer = read_file(self.resources_path, 'Footer.html') or ""

    def _format_incoming(self, msg):
        '''return a string containing the template for the incoming message
        with the vars replaced
        '''
        if (msg.type == "status" and self.status):
            template = self.status
        elif not msg.first:
            if (msg.type == e3.Message.TYPE_OLDMSG):
                template = self.history_in_next
            else:
                template = self.incoming_next
        else:
            if (msg.type == e3.Message.TYPE_OLDMSG):
                template = self.history_in
            else:
                template = self.incoming
        return self._replace(template, msg)

    def _format_outgoing(self, msg):
        '''return a string containing the template for the outgoing message
        with the vars replaced
        '''
        if (msg.type == "status" and self.status):
            template = self.status
        elif not msg.first:
            if (msg.type == e3.Message.TYPE_OLDMSG):
                template = self.history_out_next
            else:
                template = self.outgoing_next
        else:
            if (msg.type == e3.Message.TYPE_OLDMSG):
                template = self.history_out
            else:
                template = self.outgoing
        return self._replace(template, msg)

    def _append_message(self, html, scroll):
        #versions earlier than 3 don't have no-scroll variant
        if scroll or self.theme_version < 3:
            return "appendMessage('" + html + "')"

        return "appendMessageNoScroll('" + html + "')"

    def _append_next_message(self, html, scroll):
        #versions earlier than 3 don't have no-scroll variant
        if scroll or self.theme_version < 3:
            return "appendNextMessage('" + html + "')"

        return "appendNextMessageNoScroll('" + html + "')"

    def format(self, msg, scroll):
        '''return the formatted message'''
        if msg.incoming:
            html = self._format_incoming(msg)
        else:
            html = self._format_outgoing(msg)

        if msg.type == "status":
            msg.first = True

        if msg.first:
            function = self._append_message(html, scroll)
        else:
            function = self._append_next_message(html, scroll)

        return function

    def _replace(self, template, msg):
        '''replace the variables on template for the values on msg
        '''
        msg.alias = Plus.msnplus_strip(msg.alias)
        msg.display_name = Plus.msnplus_strip(msg.display_name)

        if(len(msg.alias) > DISPLAY_NAME_LIMIT):
            msg.alias = msg.alias.decode('utf-8')[0:DISPLAY_NAME_LIMIT] + "..."
        if(len(msg.display_name) > DISPLAY_NAME_LIMIT):
            msg.display_name = msg.display_name.decode('utf-8')[0:DISPLAY_NAME_LIMIT] + "..."

        image_path = escape(MarkupParser.path_to_url(msg.image_path))
        status_path = escape(MarkupParser.path_to_url(msg.status_path))

        if msg.style is not None:
            msg.message = style_message(msg.message, msg.style)
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

        template = template.replace('%message%', escape_no_xml(msg.message))

        if msg.timestamp is None:
            template = template.replace('%time%',
                escape(time.strftime("%H:%M")))
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

    def _replace_header_or_footer(self, template, source, target,
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
        template = self.template
        resources_url = MarkupParser.path_to_url(self.resources_path)
        css_path = urljoin(resources_url, "main.css")

        template = template.replace("%@", resources_url + "/", 1)
        template = template.replace("%@", css_path, 1)

        if self.variant is not None:
            variant_css_path = urljoin(resources_url,
                    "Variants", self.variant + ".css")
            variant_tag = '<style id="mainStyle" type="text/css"' + \
                'media="screen,print">	@import url( "' + variant_css_path + '" ); </style>'
        else:
            variant_tag = ""

        template = template.replace("%@", variant_tag, 1)

        target = Plus.msnplus_strip(target)
        target_display = Plus.msnplus_strip(target_display)

        header = self.header

        if header:
            header = self._replace_header_or_footer(header, source, target,
                    target_display, source_img, target_img)

        template = template.replace("%@", header, 1)

        footer = self.footer
        if footer:
            footer = self._replace_header_or_footer(footer, source, target,
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

    def _get_theme_variant(self):
        return self._variant

    def _set_theme_variant(self, variant):
        if not variant or variant == '':
            self._variant = self.default_variant
        else:
            self._variant = variant

    variant = property(fget=_get_theme_variant, fset=_set_theme_variant)

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

def escape_no_xml(string_):
    '''replace the values on dic keys with the values
    without using xml.sax.saxutils'''
    for key, value in __dic.iteritems():
        if key not in MarkupParser.dic:
            string_ = string_.replace(key, value)
    return string_

def unescape(string_):
    '''replace the values on dic_inv keys with the values'''
    return xml.sax.saxutils.unescape(string_, __dic_inv)

def replace_time(match):
    '''replace the format of the time to it's value'''
    return time.strftime(match.groups()[0])

def style_message(msgtext, style):
    '''add html markupt to msgtext to format the style of the message'''
    message = '<span style="display: inline; white-space: pre-wrap; %s">%s</span>' % (style.to_css(), msgtext)
    return message
