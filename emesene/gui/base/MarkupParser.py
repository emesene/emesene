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

# this module will include a parser for all the markups that will
# convert it into a restricted subset of xhtml
import os
import xml.sax.saxutils
import re
import base64
import urllib

import gui

dic = {
    '\"'    :    '&quot;',
    '\''    :    '&apos;',
}

dic_inv = {
    '&quot;'    :'\"',
    '&apos;'    :'\''
}

URL_REGEX_STR = '(http[s]?://|www\.)(?:[a-zA-Z]|[0-9]|[$\-_@\.&+]|[!*\"\'\(\),]|[=;/#?:]|(?:%[0-9a-fA-F][0-9a-fA-F])|[\{\}\|\[\]\\\^~])+'
URL_REGEX = re.compile(URL_REGEX_STR)
IMAGE_TAG = re.compile('(<img[^>]+>|&(?:#\d{1,3}|[\d\w]+);)')

def escape(string_):
    '''replace the values on dic keys with the values'''
    return xml.sax.saxutils.escape(string_, dic)

def unescape(string_):
    '''replace the values on dic_inv keys with the values'''
    return xml.sax.saxutils.unescape(string_, dic_inv)

def get_full_shortcuts_list(cedict):
    '''return a list of shortcuts from current emoticon theme
    and ce shortcuts'''
    celist = [(x, y) for x, y in cedict.iteritems()]
    shortcuts = gui.theme.emote_theme.shortcuts_by_length(celist)
    return [x[0] for x in shortcuts]

def replace_shortcut_with_tag(string, short, tag):
    token = '#IRREPLACEABLE#'
    def extract(m):
        irreplaceable.append(m.group(0))
        return token
    irreplaceable = []
    result = URL_REGEX.sub(extract, string)
    escaped_result = IMAGE_TAG.sub(extract, result)
    if IMAGE_TAG.sub(extract, short) not in escaped_result:
        result = escaped_result
    result = result.replace(short, tag)
    irreplaceable.reverse()
    result = re.sub(token, lambda m: irreplaceable.pop(), result)
    return result

def replace_emotes(msgtext, cedict={}, cedir=None, sender=''):
    '''replace emotes with img tags to the images'''
    emote_theme = gui.theme.emote_theme
    shortcuts = get_full_shortcuts_list(cedict)

    for shortcut in shortcuts:
        eshort = escape(shortcut)
        if eshort in msgtext:
            if shortcut in emote_theme.shortcuts:
                path = emote_theme.emote_to_path(shortcut)
            else:
                path = os.path.join(cedir, cedict[shortcut])
                if os.name == "nt":
                    path = path_to_url(path)

            if path is not None:
                # creating sort of uid for image name since different users
                # may have different images with the same shortcut
                _id = base64.b64encode(sender+shortcut)
                imgtag = '<img src="%s" alt="%s" name="%s"/>' % (path, eshort, _id)
                #msgtext = msgtext.replace(eshort, imgtag)
                msgtext = replace_shortcut_with_tag(msgtext, eshort, imgtag)

    return msgtext

def get_custom_emotes(message, cedict={}):
    ''' returns a list with the shortcuts of the
        custom emoticons present in the message
        celist comes from cache '''
    chunks = [message]
    l = []
    if cedict is None:
        return l
    shortcuts = cedict.keys()
    while len(shortcuts) > 0:
        shortcut = shortcuts.pop()

        for chunk in chunks:
            parts = chunk.split(shortcut)

            if len(parts) > 1:
                l.append(shortcut)
    return l

def replace_urls(match):
    '''function to be called on each url match'''
    hurl = url = match.group()
    if url[:4] == 'www.':
        hurl = 'http://' + url
    return '<a href="%s">%s</a>' % (hurl, url)

def urlify(strng):
    '''replace urls by an html link'''
    return URL_REGEX.sub(replace_urls, strng)

def path_to_url(path):
    if os.name == "nt":
        # on windows os.path.join uses backslashes
        path = path.replace("\\", "/")
        #path = path[2:]
        path = "localhost/" + path

    path = path.encode("iso-8859-1")
    path = urllib.quote(path)
    path = "file://" + path

    return path
