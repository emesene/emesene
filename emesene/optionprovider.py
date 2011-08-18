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

import optparse
import extension

class MinimizedOption(object):
    '''option parser'''

    def option_register(self):
        '''register the options to parse by the command line option parser'''
        option = optparse.Option("-m", "--minimized",
            action="count", dest="minimized", default=False,
            help="Minimize emesene at start")
        return option

extension.implements('option provider')(MinimizedOption)
extension.get_category('option provider').activate(MinimizedOption)

class SingleInstanceOption(object):
    '''option parser'''

    def option_register(self):
        '''register the options to parse by the command line option parser'''
        option = optparse.Option("-s", "--single",
            action="count", dest="single_instance", default=False,
            help="Allow only one instance of emesene")
        return option

extension.implements('option provider')(SingleInstanceOption)
extension.get_category('option provider').activate(SingleInstanceOption)

class VerboseOption(object):
    '''option parser'''

    def option_register(self):
        '''register the options to parse by the command line option parser'''
        option = optparse.Option("-v", "--verbose",
            action="count", dest="debuglevel", default=0,
            help="Enable debug in console (add another -v to show debug)")
        return option

extension.implements('option provider')(VerboseOption)
extension.get_category('option provider').activate(VerboseOption)

class ExtensionDefault(object):
    '''extension to register options for extensions'''

    def option_register(self):
        '''register options'''
        option = optparse.Option('--ext-default', '-e')
        option.type = 'string' #well, it's a extName:defaultValue string
        option.action = 'callback'
        option.callback = self.set_default
        option.help = 'Set the default extension by name'
        option.nargs = 1
        return option

    def set_default(self, option, opt, value, parser):
        '''set default extensions'''
        for couple in value.split(';'):
            category_name, ext_name = [strng.strip()\
                    for strng in couple.split(':', 2)]

            if not extension.get_category(category_name)\
                    .set_default_by_name(ext_name):
                print 'Error setting extension "%s" default session to "%s"'\
                        % (category_name, ext_name)

extension.implements('option provider')(ExtensionDefault)
extension.get_category('option provider').activate(ExtensionDefault)

