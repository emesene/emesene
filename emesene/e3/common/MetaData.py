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

import os
try:
    import json
except ImportError:
    import simplejson as json

def get_metadata_from_path(path):
    '''fetch the metadata from a path'''
    meta_path = os.path.join(path, 'meta.json')
    meta = None
    if os.path.exists(meta_path):
        f = open(meta_path, 'r')
        meta = json.load(f)
        f.close()
    return meta

class MetaData(object):
    '''a class that contains metadata that is used in plugins and themes
    '''

    def __init__(self, path):
        '''constructor'''
        self.meta = get_metadata_from_path(path)
