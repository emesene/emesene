# -*- coding: utf-8 -*-
#   This file is part of emesene.
#
#    Emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
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

import urllib

import logging
log = logging.getLogger('e3.common.Config')

import BaseConfig

class Config(BaseConfig.Config):
    '''a class that contains all the configurations of the user,
    the config keys follow a convention, all the names start with
    the type they have, for example:
    b_foo is boolean
    i_bar is int
    f_baz is float
    l_lala is list
    d_argh is dict (key and value are strings)
    when you try to get an attribute, if it doesn't exist it will
    return None, if the parse fails the value will not be set,
    doing this allows you to get values and don't fill the code
    with try/excepts and validations, if the name doesn't contains
    one of those prefixes, it will return the value as string'''

    def __init__(self, **kwargs):
        '''constructor'''
        BaseConfig.Config.__init__(self, **kwargs)

    def load(self, path, clear=False):
        '''load the config file from path, clear old values if
        clear is set to True'''
        if not os.path.isfile(path):
            log.warning("couldn't load config: " + path + " (no file)")
            return

        handle = file(path)

        if clear:
            self.__dict__ = {}

        try:
            content = json.load(handle)
        except ValueError:
            log.warning("couldn't load config: " + path + " (invalid format)")
            return

        for (name, value) in content:
            setattr(self, name, value)

    def save(self, path):
        '''save to a config file'''
        values = [(key, value) for (key, value) in self.__dict__.iteritems()\
                if not key.startswith("_")]

        json.dump(values, file(path, "w"), indent=1)

