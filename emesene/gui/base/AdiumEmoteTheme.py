'''a module that contains a class that describes a adium emote theme'''
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
import plistlib
try:
    import OrderedDict
except:
    from e3.common.OrderedDict import OrderedDict
plistlib._InternalDict = OrderedDict

class AdiumEmoteTheme(object):
    '''a class that contains information of a adium emote theme
    '''

    def __init__(self, path):
        '''constructor

        get information from the theme located in path
        '''
        self.path           = None
        # if you add a smilie key twice you will have a nice stack overflow :D
        self.emotes         = OrderedDict()
        self.emote_files    = []
        self.emote_regex_str= ""
        self.emote_regex    = None

        self.load_information(path)

    def load_information(self, path):
        '''load the information of the theme on path
        '''
        self.path = path

        emote_config_file = os.path.join(self.path, "Emoticons.plist")

        emote_data=plistlib.readPlist(emote_config_file)
        for key, val in emote_data['Emoticons'].iteritems():
            self.emote_files.append(key)
            pointer_name = val['Name']
            pointer_key = val['Equivalents'][0]
            self.emotes[pointer_key] = key
            for v in val['Equivalents'][1:]:
                if v != "":
                    self.emotes[v] = self.emotes[pointer_key]
        for key2 in self.emotes:
            self.emote_regex_str += re.escape(key2) + "|"
        self.emote_regex = re.compile("("+self.emote_regex_str+")")

    def emote_to_path(self, shortcut, remove_protocol=False):
        '''return a string representing the path to load the emote if it exist
        None otherwise'''

        if shortcut not in self.emotes:
            return None

        path = os.path.join(self.path, self.emotes[shortcut])
        path = os.path.abspath(path)

        if os.access(path, os.R_OK) and os.path.isfile(path):
            path = path.replace("\\", "/")

            if remove_protocol:
                return path
            else:
                if os.name == "nt":
                    #if path[1] == ":":
                    #    path = path[2:]
                    path = "localhost/"+path

                return 'file://' + path

        return None

    def _get_emotes_shortcuts(self):
        '''return the list of shortcuts'''
        return self.emotes.keys()

    shortcuts = property(fget=_get_emotes_shortcuts, fset=None)

    def shortcuts_by_length(self, celist=None):
        '''return the list of shortcuts ordered from longest to shortest with
        it's corresponding path or hash '''
        aux = [[],[],[],[],[],[],[]]
        for code in self.emotes.keys():
            aux[len(code)-1].append((code, self.emote_to_path(code, True)))
        
        if celist is not None:
           for code, hash_ in celist:
               aux[len(code)-1].append((code, hash_))
        
        return aux[6]+aux[5]+aux[4]+aux[3]+aux[2]+aux[1]+aux[0]

    def _get_emotes_count(self):
        '''return the number of emoticons registered'''
        return len(set(self.emotes.values()))

    emotes_count = property(fget=_get_emotes_count, fset=None)

    def split_smilies(self, text):
        '''split text in smilies, return a list of tuples that contain
        a boolean as first item indicating if the text is an emote or not
        and the text as second item.
        example : [(False, "hi! "), (True, ":)")]
        '''
        keys = self.emotes.keys()
        return [(item in keys, item) for item in self.emote_regex.split(text)
                if item is not None]

