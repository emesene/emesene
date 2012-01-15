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
#
#    module created by Andrea Stagi stagi.andrea(at)gmail.com
#

import os
import shutil

try:
    import json
except ImportError:
    import simplejson as json

import logging
log = logging.getLogger('e3.common.Collections')

from Github import Github
from utils import AsyncAction

class ExtensionDescriptor(object):

    def __init__(self):
        self.files = {}
        self.metadata = {}

    def add_file(self, file_name, blob):
        self.files[file_name] = blob

class Collection(object):

    def __init__(self, theme, dest_folder):
        self.dest_folder = dest_folder
        self.extensions_descs = {}
        self.theme = theme
        self.github = Github("emesene")
        self._stop = False
        self._tree = None
        self.progress = 0.0

    def save_files(self, element, label):
        self._stop = False
        if not label in element:
            return
        keys = element[label].files.keys()
        for k, path in enumerate(keys):
            self.progress = k / float(len(keys))

            split_path = path.split("/")
            if self.theme.endswith("themes"):
                removal_path = os.path.join(self.dest_folder, split_path[0], split_path[1])
            else:
                removal_path = os.path.join(self.dest_folder, split_path[0])

            if self._stop:
                self.remove(removal_path)
                return

            path_to_create = self.dest_folder
            for part in split_path[:-1]:
                path_to_create = os.path.join(path_to_create, part)
            try:
                os.makedirs(path_to_create)
            except OSError:
                pass

            try:
                rq = self.github.get_raw(self.theme, element[label].files[path])
            except Exception, ex:
                log.exception(str(ex))
                self.remove(removal_path)
                return

            f = open(os.path.join(path_to_create, split_path[-1]), "wb")
            f.write(rq)
            f.close()
        self.progress = 0.0

    def download(self, download_item=None):
        self.progress = 0.0
        if download_item is not None:
            for element in self.extensions_descs.itervalues():
                self.save_files(element, download_item)

    def remove(self, path):
        shutil.rmtree(path)

    def stop(self):
        self._stop = True

    def set_tree(self, result):
        self._tree = result

    def plugin_name_from_file(self, file_name):
        pass

    def fetch(self):
        self._stop = False
        self._tree = None
        self.progress = 0.0

        AsyncAction(self.set_tree, self.github.fetch_tree, self.theme)

        while self._tree is None:
            if self._stop:
                return

        self.progress = 0.5

        for i, item in enumerate(self._tree['tree']):

            if item.get('type') != 'blob':
                continue

            file_name = item.get('path')

            (type, name) = self.plugin_name_from_file(file_name)

            if type is None:
                continue

            try:
                extype = self.extensions_descs[type]
            except KeyError:
                extype = self.extensions_descs[type] = {}

            try:
                pl = extype[name]
            except KeyError:
                pl = extype[name] = ExtensionDescriptor()

            pl.add_file(file_name, item.get('sha'))
            self.progress = i / float(len(self._tree['tree']) * 2) + 0.5
        self.progress = 0.0

    def has_item(self, type_, name):
        current_ext = self.extensions_descs.get(type_, {}).get(name)
        if not current_ext:
            return False
        return True

    def fetch_all_metadata(self, refresh=True):
        self._stop = False
        for type_, exts in self.extensions_descs.iteritems():
            for name in exts.iterkeys():
                if self._stop:
                    return
                self.fetch_metadata(type_, name, refresh)

    def fetch_metadata(self, type_, name, refresh=False):
        '''fetch metadata if available'''
        current_ext = self.extensions_descs.get(type_, {}).get(name)
        if not current_ext:
            return None

        if not refresh and current_ext.metadata:
            return current_ext.metadata

        for path in current_ext.files.keys():
            if os.path.basename(path) == 'meta.json':
                try:
                    rq = self.github.get_raw(self.theme, current_ext.files[path])
                except Exception, ex:
                    log.exception(str(ex))
                    return None
                current_ext.metadata = json.loads(rq)
                return current_ext.metadata
        return None

class PluginsCollection(Collection):

    def plugin_name_from_file(self, file_name):
        ps = file_name.find( "/")

        if ps != -1:
            return ("plugin", file_name[:ps])
        else:
            return (None, None)

class ThemesCollection(Collection):

    def plugin_name_from_file(self, file_name):

        ps = file_name.find( "/")
        ps = file_name.find( "/", ps + 1)

        if ps != -1:
            path = file_name[:ps]
            return path.split("/")
        else:
            return (None, None)
