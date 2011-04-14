'''Parser for the ContactList'''
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

import gobject
import re

import utils
import gui

class ContactListParser(gobject.GObject):
    '''Parses everything in the ContactList'''

    def __init__(self):
        gobject.GObject.__init__(self)
        self.tagsopen = []
        self.tags_open = []
        self.regex = re.compile("<span([^>]*)>")
        self.regex_close = re.compile("</span>")

    def replace_markup(self, markup):
        '''replace the tags defined in gui.base.ContactList'''

        markup = markup.replace("[$nl]", "\n")

        markup = markup.replace("[$small]", "<small>")
        markup = markup.replace("[$/small]", "</small>")

        while markup.count("[$COLOR=") > 0:
            hexcolor = color = markup.split("[$COLOR=")[1].split("]")[0]
            if color.count("#") == 0:
                hexcolor = "#" + color

            markup = markup.replace("[$COLOR=" + color + "]", \
                    "<span foreground='" + hexcolor + "'>")
        markup = markup.replace("[$/COLOR]", "</span>")

        markup = markup.replace("[$b]", "<b>")
        markup = markup.replace("[$/b]", "</b>")

        markup = markup.replace("[$i]", "<i>")
        markup = markup.replace("[$/i]", "</i>")

        return markup

    def replace_emoticons(self, text):
        '''replace emotes with pixbufs'''
        shortcuts = gui.Theme.EMOTES.keys()
        emoticon_list = []
        for shortcut in shortcuts:
            eshort = gui.base.MarkupParser.escape(shortcut)
            if eshort in text:
                if shortcut in gui.Theme.EMOTES.keys():
                    path = gui.theme.emote_to_path(shortcut, remove_protocol=True)

                if path is not None:
                    pos = text.find(shortcut)
                    while pos > -1:
                        emoticon_list.append([pos, shortcut, path])
                        pos = text.find(shortcut, pos + 1)
        emoticon_list.sort()
        text_list = [text]
        for emoticon in emoticon_list:
            if len(text_list) == 1:
                temp_list = text.partition(emoticon[1])
                text1, text2 = self.close_tags(temp_list[0], temp_list[2])
                text_list = [text1]
                text_list.append(utils.safe_gtk_pixbuf_load(emoticon[2]))
                text_list.append(text2)
            else:
                temp_list = text_list[len(text_list) - 1].partition(emoticon[1])
                text1, text2 = self.close_tags(temp_list[0], temp_list[2])
                text_list[len(text_list) - 1] = text1
                text_list.append(utils.safe_gtk_pixbuf_load(emoticon[2]))
                text_list.append(text2)

        return text_list

    def close_tags(self, text1, text2):
        '''make sure the plus and emesene tags are closed before an emoticon'''
        ret1 = ret2 = ""
        opened = ""
        if text1 != "":
            opened = self.regex.findall(text1)
            closed = self.regex_close.findall(text1)
            for i in range(len(closed)):
                opened.pop()
        ret1 = text1 + ('</span>' * len(opened))
        for i in opened:
            ret2 += '<span' + i + '>'
        ret2 += text2
        tags = list()
        if ret1 != "":
            aux = ret1
            pos = aux.find("[$")
            while pos != -1:
                index = pos+2
                found = aux[index]
                if found == "b":
                    tags.append("b")
                elif found == "i":
                    tags.append("i")
                elif found == "s":
                    tags.append("small")
                elif found == "C":
                    if len(aux) > index + 12:
                        if aux[index+6] == "#":
                            hextag = aux[index+6:index+13]
                        else:
                            hextag = "#" + aux[index+6:index+12]
                    tags.append("COLOR=" + hextag)
                elif found == "/":
                    if len(tags) > 0:
                        tags.pop()
                aux = aux[index+1:]
                pos = aux.find("[$")

            opened = ""
            closed = ""
            while len(tags) > 0:
                tag = tags.pop()
                opened = "[$"+tag+"]"+opened
                if tag[0] == "C":
                    tag = "COLOR"
                ret1 += "[$/"+tag+"]"
            ret2 = opened + ret2
        return ret1, ret2
