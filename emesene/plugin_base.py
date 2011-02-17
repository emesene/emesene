#!/usr/bin/env python
'''
Plugin base class.

It will be inherited by every plugin.

'''
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

class PluginBase(object):
    '''base class for plugins'''
    _description = "No description"
    _authors = {}
    def __init__(self):
        self._started = False
        self._configure = None

    def start(self, session):
        '''method to start the plugin'''
        raise NotImplementedError()

    def is_active(self):
        '''returns True if the plugin is activated'''
        return self._started

    def stop(self):
        '''method to stop the plugin'''
        raise NotImplementedError()

    def config(self, session):
        '''method to config the plugin'''
        raise NotImplementedError()

    def category_register(self):
        '''It's a placeholder. Can be safely called even if not implemented
        (that means the plugin is old-style)'''
        return False

    def extension_register(self):
        '''It's a placeholder. Can be safely called even if not implemented
        (that means the plugin is old-style)'''
        return False
