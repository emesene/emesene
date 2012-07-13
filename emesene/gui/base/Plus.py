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

# regex used to remove plus markup
# one symbol for each msnplus tag
msnplus_tags_re = re.compile(
    '\[(/?)(\w{1})(\=(\#?[0-9a-f]+|\w+))?\]',
    re.IGNORECASE | re.DOTALL)

msnplus_tags_old_re = re.compile(
    '\xb7()([\$#&\'@0])()((\#?[0-9a-f]{6}|\d{1,2})?),?((\#?[0-9a-f]{6}|\d{1,2})?)',
    re.IGNORECASE | re.DOTALL)

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

class Plus(object):

    def __init__(self, text):
        self.text = unicode(text, 'utf8') if not isinstance(text, unicode) else text
        self.stack = [{'tag':'', 'childs':[]}]
        self.tag_queue = []

    def _close_tags(self, text_before, tag, arg, do_parse_emotes):
        '''close tags that are open'''
        stack_index = -1
        for i, message in enumerate(reversed(self.stack)):
            if tag in message:
                stack_index = -i - 1
                break
        if arg:
            start_tag = self.stack[stack_index][tag]
            self.stack[stack_index][tag] = (start_tag, arg)
        if text_before.strip(' '):
            if do_parse_emotes:
                text_before = parse_emotes(text_before)
                self.stack[stack_index]['childs'] += text_before
            else:
                self.stack[stack_index]['childs'].append(text_before)
        tag_we_re_closing = self.stack.pop(stack_index)
        if isinstance(self.stack[stack_index], dict):
            self.stack[stack_index]['childs'].append(tag_we_re_closing)
        else:
            self.stack.append(tag_we_re_closing)

    def _close_stack_tags(self, do_parse_emotes=True):
        '''Closes all open tags in stack'''
        tags_to_close = len(self.stack)
        for i in range(tags_to_close-1):
            self._close_tags('', '', '', do_parse_emotes)

    def _get_shortest_match(self, match1, match2):
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

    def _get_best_match(self, text):
        '''get the best match out of all regexes'''
        match = open_tag_re.match(text)
        match_old = open_tag_old_re.match(text)
        match_close_old = close_tag_old_re.match(text)
        match = self._get_shortest_match(match, match_old)
        match = self._get_shortest_match(match, match_close_old)
        return match

    def to_dict(self, do_parse_emotes=True):
        '''convert it into a dict, as the one used by XmlParser'''
        self._to_dict(self.text, do_parse_emotes)
        self.stack = {'tag': 'span', 'childs': self.stack}
        self._hex_colors(self.stack)
        self._dict_gradients(self.stack)
        self._dict_translate_tags(self.stack)
        return self.stack

    def _to_dict(self, text, do_parse_emotes=True,
                         was_double_color=False):
        '''convert it into a dict, as the one used by XmlParser'''

        match = self._get_best_match(text)

        if not match: #only text
            if do_parse_emotes:
                parsed_markup = parse_emotes(text)
            else:
                parsed_markup = [text]

            self.stack.append(text)
            self._close_stack_tags(do_parse_emotes)
            return

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
                self.stack[-1]['childs'].append(splitted_text[0])
            text_before = splitted_text[2]
            self._close_stack_tags(do_parse_emotes)
            self.stack[-1]['childs'].append('\n')

        if self.tag_queue and self.tag_queue[0][0] == match.group(3) and not self.tag_queue[0][2]:
            self.stack[-1]['childs'].append(match.group(0))
        elif close_all_tags or (tag in TAG_DICT and (tag not in COLOR_TAGS or \
           (tag in COLOR_TAGS and (arg or not open_)))):
            if open_:
                if text_before.strip(' ') and not was_double_color:
                    self.stack[-1]['childs'].append(text_before)
                msgdict = {'tag': tag, tag: arg, 'childs': []}
                self.stack.append(msgdict)
            else: #closing tags
                self._close_tags(text_before, tag, arg, do_parse_emotes)
                if close_all_tags:
                    self._close_stack_tags(do_parse_emotes)
        else:
            self.stack[-1]['childs'].append(match.group(0))

        if self.tag_queue:
            self.tag_queue.pop(0)

        self._to_dict(text[entire_match_len:],
                         do_parse_emotes, is_double_color)

    def _nchars_dict(self, msgdict):
        '''count how many character are there'''
        nchars = 0
        for child in msgdict['childs']:
            if isinstance(child, basestring):
                nchars += len(special_character_re.sub('a', child))
            else:
                nchars += self._nchars_dict(child)

        return nchars

    def _color_gradient(self, color1, color2, length):
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

    def _color_to_hex(self, color):
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

    def _hex_colors(self, msgdict):
        '''convert colors to hex'''
        if msgdict['tag']:
            tag = msgdict['tag']

            if tag in COLOR_TAGS:
                param = msgdict[tag]

                if isinstance(param, tuple): #gradient
                    param1, param2 = param
                    msgdict[tag] = (self._color_to_hex(param1), self._color_to_hex(param2))

                else: #normal color
                    msgdict[tag] = self._color_to_hex(param)

        for child in msgdict['childs']:
            if child and not isinstance(child, basestring):
                self._hex_colors(child)

    def _gradientify_string(self, msg, attr, colors):
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

    def _gradientify(self, msgdict, attr=None, colors=None):
        '''apply a gradient to that msgdict'''
        if not attr:
            attr = msgdict['tag']

        if colors is None:
            param_from, param_to = msgdict[attr]
            #param_from = COLOR_MAP[int(param_from)]
            #param_to = COLOR_MAP[int(param_to)]
            length = self._nchars_dict(msgdict)
            if length != 1:
                colors = self._color_gradient(param_from, param_to, length)
            msgdict['tag'] = ''
            del msgdict[attr]

        i = 0
        while colors and i < len(msgdict['childs']):
            this_child = msgdict['childs'][i]

            if isinstance(this_child, basestring):
                msgdict['childs'][i] = self._gradientify_string(this_child, attr, colors) #will consumate some items from colors!
            else:
                self._gradientify(this_child, attr, colors)

            i += 1

    def _dict_gradients(self, msgdict):
        '''apply gradients where needed'''
        if not isinstance(msgdict, dict):
            return

        for subdict in msgdict['childs']:
            if isinstance(subdict, dict):
                tag = subdict['tag']
                if tag in subdict and isinstance(subdict[tag], tuple):
                    self._gradientify(subdict)
                self._dict_gradients(subdict)

    def _dict_translate_tags(self, msgdict):
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
                self._dict_translate_tags(child)

    def tags_extract(self, strip=False):
        '''extract all msnplus tags from input'''
        nl_pos = self.text.find('\n')
        for m in msnplus_tags_re.finditer(self.text):
            is_opened_tag = False if m.group(1) != '' else True
            has_attr = False if not m.group(4) else True
            # (tag, an opened_tag?, does it paired?, start pos, tag with attr?)
            self.tag_queue.append([m.group(2), is_opened_tag, False, m.start(), has_attr])

        self._tags_pair(nl_pos, strip)

    def _tags_pair(self, nl_pos, strip=False):
        '''find out dangling tags in list based on an assumption that
        all tags are well-formed'''
        # we use the strategy like stack but no pop/push operations
        for i, tag in enumerate(self.tag_queue):
            # do not process opened tag
            if tag[1]:
                continue

            for previous_tag in reversed(self.tag_queue[:i]):
                # find out an unpaired opened_tag with the same type
                # and mark them paired, like stack (msnplus-like)
                # we allow mixing upper case and lower case in code
                if previous_tag[1] and not previous_tag[2] and \
                   previous_tag[0].lower() == tag[0].lower():
                    # a color tag must have attribute
                    if previous_tag[0].lower() in ('a', 'c') and \
                       not previous_tag[4]:
                        continue

                    # avoid to cross newline, eg: nickname nl message
                    # pair if there is no newline, or in the same part
                    if nl_pos == -1 or \
                       (previous_tag[3] > nl_pos and tag[3] > nl_pos) or \
                       (previous_tag[3] < nl_pos and tag[3] < nl_pos):
                        previous_tag[2] = True
                        tag[2] = True
                        break

        # we only need position of paired tags in strip mode
        if strip:
            self.tag_queue = filter(lambda x: x[2], self.tag_queue)
            for index, tag in enumerate(self.tag_queue):
                self.tag_queue[index] = tag[3]

    def strip_tags(self):
        '''strip msnplus tags with the striplist'''
        def strip_tags(match):
            if match.start() in self.tag_queue:
                return ''
            return match.group(0)

        text = msnplus_tags_re.sub(strip_tags, self.text)
        text = msnplus_tags_old_re.sub('', text)

        return text

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

def msnplus(text, do_parse_emotes=True):
    '''given a string with msn+ formatting, give a DictObj
    representing its formatting.'''
    plus = Plus(text)
    plus.tags_extract()
    dictlike = plus.to_dict(do_parse_emotes)
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
    plus = Plus(text)
    plus.tags_extract(True)
    text = plus.strip_tags()
    text = _unescape_special_chars(text)

    return text
