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
from e3.common.XmlParser import DictObj
import gui

COLOR_MAP = (
    'ffffff','000000','00007F','009300','FF0000','7F0000','9C009C','FC7F00',
    'FFFF00','00FC00','009393','00FFFF','0000FC','FF00FF','7F7F7F','D2D2D2',
    'E7E6E4','CFCDD0','FFDEA4','FFAEB9','FFA8FF','B4B4FC','BAFBE5','C1FFA3',
    'FAFDA2','B6B4B7','A2A0A1','F9C152','FF6D66','FF62FF','6C6CFF','68FFC3',
    '8EFF67','F9FF57','858482','6E6D7B','FFA01E','F92611','FF20FF','202BFF',
    '1EFFA5','60F913','FFF813','5E6464','4B494C','D98812','EB0505','DE00DE',
    '0000D3','03CC88','59D80D','D4C804','333335','18171C','944E00','9B0008',
    '980299','01038C','01885F','389600','9A9E15','473400','4D0000','5F0162',
    '000047','06502F','1C5300','544D05')

# color dict used to retreive common color codes from their names
COLOR_NAME_DICT = {
    'white': '#ffffff',
    'black': '#000000',
    'marine': '#00007F',
    'white': '#ffffff',
    'green': '#009300',
    'red': '#FF0000',
    'brown': '#7F0000',
    'purple': '#9C009C',
    'orange': '#FC7F00',
    'yellow': '#FFFF00',
    'lime': '#00FC00',
    'teal': '#009393',
    'aqua': '#00FFFF',
    'blue': '#0000FC',
    'pink': '#FF00FF',
    'gray': '#7F7F7F',
    'silver': '#D2D2D2',
    'mohr': '#ff00de',
    'c10ud': '#696969'
}

TAG_DICT = {
    'a': 'background',
    'c': 'foreground',
    'b': ('weight', 'bold'),
    'u': ('underline', 'single'),
    'i': ('style', 'italic'),
    's': ('strikethrough', 'true'),
    '$': 'foreground',
    '#': ('weight', 'bold'),
    '@': ('underline', 'single'),
    '&': ('style', 'italic'),
    '\'': ('strikethrough', 'true')
}

COLOR_TAGS = ('a', 'c', '$')

open_tag_re = re.compile(
    '''(.*?)\[(/?)(\w+)(\=(\#?[0-9a-f]+|\w+))?\]()()''',
    re.IGNORECASE | re.DOTALL)

open_tag_old_re = re.compile(
    '(.*?)\xb7()([\$#&\'@])()((\#?[0-9a-f]{6}|\d{1,2})?),?((\#?[0-9a-f]{6}|\d{1,2})?)',
    re.IGNORECASE | re.DOTALL)

close_tag_old_re = re.compile(
    '(.*?)\xb7(0)()()()()()',
    re.IGNORECASE | re.DOTALL)

#TODO: I think the other 'InGradient' regexes from the old parser have to be used too
special_character_re = re.compile('(&[a-zA-Z]+\d{0,3};|\%.)')

#regex used to remove plus markup
tag_plus_strip_re = re.compile(
    '(\[(/)?\w(\=#?[0-9a-f]+|\=\w+)?\])',
    re.IGNORECASE)
tag_plus_old_strip_re = re.compile(
    '\·([#&\'@0])|\·\$(\d+|\#\w+)?(\,(\d+|\#\w+))?')

hex_tag_re = re.compile('([0-9a-f]{3}|[0-9a-f]{6})$', re.IGNORECASE)

def parse_emotes(markup):
    '''search for emotes on markup and return a list of items with chunks of
    test and Emote instances'''
    accum = []
    for is_emote, text in gui.theme.emote_theme.split_smilies(markup):
        if is_emote:
            accum.append(
                {'tag': 'img',
                 'src': gui.theme.emote_theme.emote_to_path(text, True),
                 'alt': text, 'childs': []})
        else:
            accum.append(text)

    return accum

def _close_tags(message_stack, text_before, tag, arg, do_parse_emotes):
    '''close tags that are open'''
    stack_index = -1
    for i, message in enumerate(reversed(message_stack)):
        if tag in message:
            stack_index = -i - 1
            break
    if arg:
        start_tag = message_stack[stack_index][tag]
        message_stack[stack_index][tag] = (start_tag, arg)
    if text_before.strip(' '):
        if do_parse_emotes:
            text_before = parse_emotes(text_before)
            message_stack[stack_index]['childs'] += text_before
        else:
            message_stack[stack_index]['childs'].append(text_before)
    tag_we_re_closing = message_stack.pop(stack_index)
    if isinstance(message_stack[stack_index], dict):
        message_stack[stack_index]['childs'].append(tag_we_re_closing)
    else:
        message_stack.append(tag_we_re_closing)

def _close_stack_tags(message_stack, do_parse_emotes=True):
    '''Closes all open tags in stack'''
    tags_to_close = len(message_stack)
    for i in range(tags_to_close-1):
        _close_tags(message_stack, '', '', '', do_parse_emotes)

def _get_shortest_match(match1, match2):
    '''get the match that comes earliest'''
    if match1 and match2:
        if len(match1.group(1)) > len(match2.group(1)):
            return match2
        else:
            return match1
    elif match1:
        return match1
    else:
        return match2

def _get_best_match(msnplus):
    '''get the best match out of all regexes'''
    match = open_tag_re.match(msnplus)
    match_old = open_tag_old_re.match(msnplus)
    match_close_old = close_tag_old_re.match(msnplus)
    match = _get_shortest_match(match, match_old)
    match = _get_shortest_match(match, match_close_old)
    return match

def _msnplus_to_dict(msnplus, message_stack, do_parse_emotes=True,
                     was_double_color=False):
    '''convert it into a dict, as the one used by XmlParser'''

    match = _get_best_match(msnplus)

    if not match: #only text
        if do_parse_emotes:
            parsed_markup = parse_emotes(msnplus)
        else:
            parsed_markup = [msnplus]

        message_stack.append(msnplus)
        _close_stack_tags(message_stack, do_parse_emotes)
        return {'tag': 'span', 'childs': parsed_markup}

    text_before = match.group(1)
    open_ = match.group(2) == ''
    close_all_tags = match.group(2) == '0'
    tag = match.group(3)
    tag = tag.lower()
    arg = match.group(5)
    arg2 = match.group(7)
    is_double_color = arg2 and arg and not was_double_color
    entire_match_len = len(match.group(0))
    if is_double_color:
        entire_match_len = 0
    elif arg2:
        arg = arg2
        tag = 'a'

    if '\n' in text_before:
        splitted_text = text_before.partition('\n')
        if splitted_text[0].strip(' '):
            message_stack[-1]['childs'].append(splitted_text[0])
        text_before = splitted_text[2]
        _close_stack_tags(message_stack, do_parse_emotes)
        message_stack[-1]['childs'].append('\n')

    if close_all_tags or (tag in TAG_DICT and (tag not in COLOR_TAGS or \
       (tag in COLOR_TAGS and (arg or not open_)))):
        if open_:
            if text_before.strip(' ') and not was_double_color:
                message_stack[-1]['childs'].append(text_before)
            msgdict = {'tag': tag, tag: arg, 'childs': []}
            message_stack.append(msgdict)
        else: #closing tags
            _close_tags(message_stack, text_before, tag, arg, do_parse_emotes)
            if close_all_tags:
                _close_stack_tags(message_stack, do_parse_emotes)
    else:
        message_stack[-1]['childs'].append(match.group(0))

    #go recursive!
    _msnplus_to_dict(msnplus[entire_match_len:], message_stack,
                     do_parse_emotes, is_double_color)

    return {'tag': 'span', 'childs': message_stack}

def _nchars_dict(msgdict):
    '''count how many character are there'''
    nchars = 0
    for child in msgdict['childs']:
        if isinstance(child, basestring):
            nchars += len(special_character_re.sub('a', child))
        else:
            nchars += _nchars_dict(child)

    return nchars

def _color_gradient(color1, color2, length):
    '''returns a list of colors. Its length is length'''

    def dec2hex(n):
        """return the hexadecimal string representation of integer n"""
        if n < 16:
            return '0' + "%X" % n
        else:
            return "%X" % n

    def hex2dec(s):
        """return the integer value of a hexadecimal string s"""
        return int('0x' + s, 16)

    def full_hex2dec(colorstring):
        """return a tuple containing the integer values of the rgb colors"""
        hex3tohex6 = lambda col: col[0] * 2 + col[1] * 2 + col[2] * 2

        colorstring = colorstring.strip()

        if colorstring.startswith('#'):
            colorstring = colorstring[1:]

        if len(colorstring) == 3:
            colorstring = hex3tohex6(colorstring)

        r, g, b = colorstring[:2], colorstring[2:4], colorstring[4:]
        r, g, b = [hex2dec(i.upper()) for i in (r, g, b)]
        return (r, g, b)

    if length == 0:
        return

    rgb_tuple1 = full_hex2dec(color1)
    rgb_tuple2 = full_hex2dec(color2)

    colors = [''] * length
    for color_part in zip(rgb_tuple1, rgb_tuple2):
        step = (color_part[1] - color_part[0]) / (length - 1.0)
        for i in range(length - 1):
            colors[i] += dec2hex(int(color_part[0] + step * i))
        colors[length - 1] += dec2hex(color_part[1])

    return colors

def _color_to_hex(color):
    '''
    convert non-hex colors like names or plus codes to hex colors
    '''
    color = COLOR_NAME_DICT.get(color.lower(), color)
    if color.startswith('#'):
        color = color[1:]
    if len(color) <= 2 and int(color) < len(COLOR_MAP):
        color = COLOR_MAP[int(color)]
    elif not hex_tag_re.match(color):
        color = COLOR_MAP[1]

    return color

def _hex_colors(msgdict):
    '''convert colors to hex'''
    if msgdict['tag']:
        tag = msgdict['tag']

        if tag in COLOR_TAGS:
            param = msgdict[tag]

            if isinstance(param, tuple): #gradient
                param1, param2 = param
                msgdict[tag] = (_color_to_hex(param1), _color_to_hex(param2))

            else: #normal color
                msgdict[tag] = _color_to_hex(param)

    for child in msgdict['childs']:
        if child and not isinstance(child, basestring):
            _hex_colors(child)

def _gradientify_string(msg, attr, colors):
    '''apply sequence "colors" of colors (type attr) to msg'''
    result = {'tag': '', 'childs': []}

    split_msg = special_character_re.split(msg)

    for text in split_msg:
        if special_character_re.match(text):
            color = colors.pop(0)
            result['childs'].append({'tag': attr, attr: color,
                                     'childs': [text]})
            continue
        for char in text:
            color = colors.pop(0)
            result['childs'].append({'tag': attr, attr: color,
                                     'childs': [char]})

    return result

def _gradientify(msgdict, attr=None, colors=None):
    '''apply a gradient to that msgdict'''
    if not attr:
        attr = msgdict['tag']

    if colors is None:
        param_from, param_to = msgdict[attr]
        #param_from = COLOR_MAP[int(param_from)]
        #param_to = COLOR_MAP[int(param_to)]
        length = _nchars_dict(msgdict)
        if length != 1:
            colors = _color_gradient(param_from, param_to, length)
        msgdict['tag'] = ''
        del msgdict[attr]

    i = 0
    while colors and i < len(msgdict['childs']):
        this_child = msgdict['childs'][i]

        if isinstance(this_child, basestring):
            msgdict['childs'][i] = _gradientify_string(this_child, attr, colors) #will consumate some items from colors!
        else:
            _gradientify(this_child, attr, colors)

        i += 1

def _dict_gradients(msgdict):
    '''apply gradients where needed'''
    if not isinstance(msgdict, dict): return
    for subdict in msgdict['childs']:
        if isinstance(subdict, dict):
            tag = subdict['tag']
            if tag in subdict and isinstance(subdict[tag], tuple):
                _gradientify(subdict)
            _dict_gradients(subdict)

def _dict_translate_tags(msgdict):
    '''translate 'a' to 'span' etc...'''
    tag = msgdict['tag']
    if tag in TAG_DICT:
        msgdict['tag'] = 'span'
        if tag in COLOR_TAGS:
            msgdict[TAG_DICT[tag]] = '#%s' % msgdict[tag].upper()
        else:
            msgdict[TAG_DICT[tag][0]] = TAG_DICT[tag][1]
        del msgdict[tag]
    elif tag == 'img':
        pass
    elif tag not in ('span', ''):
        del msgdict[tag]
        msgdict['tag'] = ''
        msgdict['childs'].insert(0, '[%s]' % (tag, ))

    #Then go recursive!
    for child in msgdict['childs']:
        if isinstance(child, dict):
            _dict_translate_tags(child)

def msnplus(text, do_parse_emotes=True):
    '''given a string with msn+ formatting, give a DictObj
    representing its formatting.'''
    message_stack = [{'tag':'', 'childs':[]}]
    text = unicode(text, 'utf8') if not isinstance(text, unicode) else text
    dictlike = _msnplus_to_dict(text, message_stack, do_parse_emotes)
    _hex_colors(dictlike)
    _dict_gradients(dictlike)
    _dict_translate_tags(dictlike)
    return DictObj(dictlike)

def msnplus_parse(text):
    '''
    given a string with msn+ formatting, give a string with same text but
    with Pango Markup
    @param text The original string
    '''
    text = _escape_special_chars(text)
    dictlike = msnplus(text, False)
    text = _unescape_special_chars(dictlike.to_xml())
    return dictlike.to_xml()

def _escape_special_chars(text):
    #escape special chars
    text = text.replace('\xc2\xb7&amp;', '\xc2\xb7&')
    text = text.replace('\xc2\xb7&quot;', '\xc2\xb7"')
    text = text.replace('\xc2\xb7&apos;', '\xc2\xb7\'')
    return text

def _unescape_special_chars(text):
    #unescape special chars
    text = text.replace('\xc2\xb7&', '\xc2\xb7&amp;')
    text = text.replace('\xc2\xb7"', '\xc2\xb7&quot;')
    text = text.replace('\xc2\xb7\'', '\xc2\xb7&apos;')
    return text

def msnplus_strip(text, useless_arg=None):
    '''
    given a string with msn+ formatting, give a string with same text but
    without MSN+ markup
    @param text The original string
    @param useless_arg This is actually useless, and is mantained just for
    compatibility with text
    '''

    text = _escape_special_chars(text)
    text = tag_plus_strip_re.sub('', text)
    text = tag_plus_old_strip_re.sub('', text)
    text = _unescape_special_chars(text)

    return text
