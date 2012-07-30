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

import extension
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
SEARCH_REGEX_STR = '(search://)(?:[a-zA-Z]|[0-9]|[$\-_@\.&+]|[!*\"\'\(\),]|[=;/#?:]|(?:%[0-9a-fA-F][0-9a-fA-F])|[\{\}\|\[\]\\\^~])+'
SEARCH_REGEX = re.compile(SEARCH_REGEX_STR)
IMAGE_TAG = re.compile('(<img[^>]+>|&(?:#\d{1,3}|[\d\w]+);)')
TAG_REGEX = re.compile("(.*?)<span([^>]*)>", re.IGNORECASE | re.DOTALL)
CLOSE_TAG_REGEX = re.compile("(.*?)</span>", re.IGNORECASE | re.DOTALL)
HTML_CODE_REGEX = re.compile("&\w+;", re.IGNORECASE | re.DOTALL)

def replace_markup(markup):
    '''replace the tags defined in gui.base.ContactList'''
    Tags = extension.get_default('toolkit tags')

    markup = markup.replace("[$nl]", "\n")

    markup = markup.replace("[$small]", "<span %s=\"small\">" % Tags.FONT_SIZE)
    markup = markup.replace("[$/small]", "</span>")

    while markup.count("[$COLOR=") > 0:
        hexcolor = color = markup.split("[$COLOR=")[1].split("]")[0]
        if color.count("#") == 0:
            hexcolor = "#" + color

        markup = markup.replace("[$COLOR=" + color + "]", \
                "<span %s='" % Tags.FONT_COLOR + hexcolor + "'>")
    markup = markup.replace("[$/COLOR]", "</span>")

    markup = markup.replace("[$b]", "<span %s=\"bold\">" % Tags.FONT_WEIGHT)
    markup = markup.replace("[$/b]", "</span>")

    markup = markup.replace("[$i]", "<span %s=\"italic\">" % Tags.FONT_STYLE)
    markup = markup.replace("[$/i]", "</span>")

    # Close all tags before a new line
    markup_lines = markup.split('\n')
    for i in range(len(markup_lines) - 1):
        closed_line = close_tags(markup_lines[i], markup_lines[i + 1])
        markup_lines[i] = closed_line[0]
        markup_lines[i + 1] = closed_line[1]
    markup = '\n'.join(markup_lines)

    return markup

def close_tags(text1, text2=''):
    '''make sure the plus and emesene tags are closed before an emoticon'''
    ret1 = ret2 = ""
    opened = []
    if text1 != "":
        text = text1
        while text != '':
            opened_match = TAG_REGEX.match(text)
            closed_match = CLOSE_TAG_REGEX.match(text)
            if closed_match and opened_match:
                if len(closed_match.group(1)) > len(opened_match.group(1)):
                    closed_match = None
                else:
                    opened_match = None
            if closed_match:
                opened.pop()
                text = text[len(closed_match.group(0)):]
            elif opened_match:
                opened.append(opened_match.group(2))
                text = text[len(opened_match.group(0)):]
            else:
                text = ''
    ret1 = text1 + ('</span>' * len(opened))
    for i in opened:
        ret2 += '<span' + i + '>'
    ret2 += text2
    return ret1, ret2

def escape(string_):
    '''replace the values on dic keys with the values'''
    return xml.sax.saxutils.escape(string_, dic)

def unescape(string_):
    '''replace the values on dic_inv keys with the values'''
    return xml.sax.saxutils.unescape(string_, dic_inv)

def get_full_shortcuts_list(cedict):
    '''return a list of shortcuts from current emoticon theme
    and ce shortcuts'''
    celist = None
    if cedict is not None:
        celist = cedict.items()
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
                imgtag = '<img src="%s" alt="%s" title="%s" name="%s"/>' % (path, eshort, eshort, _id)
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

def replace_search_urls(match):
    '''function to be called on each search url match'''
    hurl = match.group()
    return '<a href="%s">%s</a>' % (hurl, _('view more'))

def urlify(strng):
    '''replace urls by an html link'''
    strng = SEARCH_REGEX.sub(replace_search_urls, strng)
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

def replace_emoticons(text):
    '''replace emotes with pixbufs'''
    emote_theme = gui.theme.emote_theme
    shortcuts = emote_theme.shortcuts
    emoticon_list = []
    for shortcut in shortcuts:
        eshort = gui.base.MarkupParser.escape(shortcut)
        if eshort in text:
            if shortcut in emote_theme.shortcuts:
                path = emote_theme.emote_to_path(shortcut, remove_protocol=True)

            if path is not None:
                hclist = html_code_list(text)
                pos = text.find(eshort)
                while pos > -1:
                    if pos not in hclist:
                        emoticon_list.append([pos, eshort, path])
                    pos = text.find(eshort, pos + 1)

    emoticon_list.sort()
    parsed_pos = 0
    text_list = []
    close_tags_index = []
    for emoticon in emoticon_list:
        if emoticon[0] >= parsed_pos:
            # append non-empty string into list 
            if emoticon[0] != parsed_pos:
                text_list.append(text[parsed_pos:emoticon[0]])
                close_tags_index.append(len(text_list) - 1)
            PictureHandler = extension.get_default('picture handler')
            text_list.append(PictureHandler(emoticon[2]).get_image())
            parsed_pos = emoticon[0] + len(emoticon[1])
    text_list.append(text[parsed_pos:])
    close_tags_index.append(len(text_list) - 1)

    for idx in range(len(close_tags_index) - 1):
        tl_idx1 = close_tags_index[idx]
        tl_idx2 = close_tags_index[idx + 1]
        text_list[tl_idx1], text_list[tl_idx2] = close_tags(text_list[tl_idx1], text_list[tl_idx2])

    return text_list

def html_code_list(text):
    '''return positions of specify html codes in input string'''
    html_list = []
    for hc in HTML_CODE_REGEX.finditer(text):
        if hc.group() in gui.base.MarkupParser.dic_inv:
            html_list.append(hc.end() - 1)
    return html_list

