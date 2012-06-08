'''gtkui MarkupParser'''
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

import utils
import gui

TAG_REGEX = re.compile("(.*?)<span([^>]*)>", re.IGNORECASE | re.DOTALL)
CLOSE_TAG_REGEX = re.compile("(.*?)</span>", re.IGNORECASE | re.DOTALL)

def replace_markup(markup):
    '''replace the tags defined in gui.base.ContactList'''

    markup = markup.replace("[$nl]", "\n")

    markup = markup.replace("[$small]", "<span size=\"small\">")
    markup = markup.replace("[$/small]", "</span>")

    while markup.count("[$COLOR=") > 0:
        hexcolor = color = markup.split("[$COLOR=")[1].split("]")[0]
        if color.count("#") == 0:
            hexcolor = "#" + color

        markup = markup.replace("[$COLOR=" + color + "]", \
                "<span foreground='" + hexcolor + "'>")
    markup = markup.replace("[$/COLOR]", "</span>")

    markup = markup.replace("[$b]", "<span weight=\"bold\">")
    markup = markup.replace("[$/b]", "</span>")

    markup = markup.replace("[$i]", "<span style=\"italic\">")
    markup = markup.replace("[$/i]", "</span>")

    # Close all tags before a new line
    markup_lines = markup.split('\n')
    for i in range(len(markup_lines) - 1):
        closed_line = close_tags(markup_lines[i], markup_lines[i + 1])
        markup_lines[i] = closed_line[0]
        markup_lines[i + 1] = closed_line[1]
    markup = '\n'.join(markup_lines)

    return markup

def replace_emoticons(text):
    '''replace emotes with pixbufs'''
    emote_theme = gui.theme.emote_theme
    shortcuts = emote_theme.shortcuts
    emoticon_list = []
    unescaped_text = gui.base.MarkupParser.unescape(text)
    for shortcut in shortcuts:
        eshort = gui.base.MarkupParser.escape(shortcut)
        if shortcut in unescaped_text:
            if shortcut in emote_theme.shortcuts:
                path = emote_theme.emote_to_path(shortcut, remove_protocol=True)

            if path is not None:
                pos = unescaped_text.find(shortcut)
                while pos > -1:
                    emoticon_list.append([pos, eshort, path])
                    pos = unescaped_text.find(shortcut, pos + 1)

    emoticon_list.sort()
    text_list = [text]
    for emoticon in emoticon_list:
        if len(text_list) == 1:
            temp_list = text.partition(emoticon[1])
            text1, text2 = close_tags(temp_list[0], temp_list[2])
            text_list = [text1]
            text_list.append(utils.safe_gtk_pixbuf_load(emoticon[2]))
            text_list.append(text2)
            old_emoticon = emoticon
        elif emoticon[0] >= old_emoticon[0] + len(old_emoticon[1]):
            temp_list = text_list[len(text_list) - 1].partition(emoticon[1])
            text1, text2 = close_tags(temp_list[0], temp_list[2])
            text_list[len(text_list) - 1] = text1
            text_list.append(utils.safe_gtk_pixbuf_load(emoticon[2]))
            text_list.append(text2)
            old_emoticon = emoticon
    # make sure broken plus tags are parsed in the right way
    text1, text2 = close_tags(text_list[len(text_list)-1])
    text_list[len(text_list) - 1] = text1

    return text_list

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
