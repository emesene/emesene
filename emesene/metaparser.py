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

"""
Meta data for plugins.
Recommended Format (strip out comments):
{
    // required
    "name" : "My Plugin",
    "version" : "versionString",
    "configurable" : false,

    // recommended
    "description" : "My first plugin.",
    "authors" : [["Name", "Email"], ["Another Name", "Another@Email"]]
}
"""
import json

class MetaData(object):
    _required_attributes = ("name", "version", "configurable")
    def __init__(self, filename):
        with open(filename) as f:
            self.__dict__['_data'] = json.load(f)

        for name in self._required_attributes:
            assert name in self._data, "'%s' missing meta attribute of '%s'" % (filename, name)

    def __getattr__(self, name):
        try:
            return self._data[name]
        except KeyError:
            return None # Default value or this?

    def __setattr__(self, name, value):
        raise Exception("MetaData cannot be changed!")
