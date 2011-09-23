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
    '''Base class for plugins'''
    description = 'Your first plugin.'
    _description = description # DEPRICATE ME!
    _authors = {}
    def __init__(self):
        self.active = False

    def start(self, session):
        '''Method to start the plugin'''
        return

    def stop(self):
        '''Method to stop the plugin'''
        return

    def configurable(self):
        '''Method returning a boolean indicating if this plugin can
        be configured or not.'''
        return False

    def config(self, session):
        '''Method to configure the plugin. Please put configurable to
        return True if you need to implement this method.'''
        pass

    def category_register(self):
        '''It's a placeholder. Can be safely called even if not implemented
        (that means the plugin is old-style)'''
        return False

    def extension_register(self):
        '''It's a placeholder. Can be safely called even if not implemented
        (that means the plugin is old-style)'''
        return False
