#!/usr/bin/env python
'''Handles plugin importing'''
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
import sys
import logging

log = logging.getLogger('pluginmanager')

BLACKLIST = ["lint.py", "__init__.py"]

class PackageResource:
    '''Handle various files that could be put in the package'''
    def __init__(self, base_dir, directory):
        self.path = os.path.join(base_dir, directory)

    def get_resource_path(self, relative_path):
        '''get the path to the required resource.
        If you can, use get_resource.
        @return the path if it exists or an empty string otherwise'''
        abs_path = os.path.join(self.path, relative_path)
        if os.path.exists(abs_path):
            return abs_path
        return ''

    def get_resource(self, relative_path):
        '''Opens a file.
        @param relative_path A path starting from the package dir
        @return a file object opening relative_path if it is possible, or None
        '''
        file_path = self.get_resource_path(relative_path)
        if file_path:
            try:
                return open(file_path)
            except IOError:
                return

class PluginHandler:
    '''Abstraction over a plugin.

    Given a directory, will import the plugin.py file inside it and allows to control it.
    It will provide the plugin several utilities to work on the package

    '''
    def __init__(self, base_dir, name, is_package=False):
        '''@param directory The directory containing the package'''
        self.name = os.path.basename(name.rstrip("/"))
        if not is_package:
            self.name = self.name.split(".")[0]

        self.base_dir = base_dir
        self._instance = None

        self.is_package = is_package

        self.module = None
        self._do_import()

    def _do_import(self):
        '''Does the dirty stuff with __import__'''
        old_syspath = sys.path[:]
        try:
            sys.path += ['.', self.base_dir]
            self.module = __import__(self.name, globals(), None, ['plugin'])
            if hasattr(self.module, 'plugin'):
                self.module = self.module.plugin
        except Exception, reason:
            log.warning('error importing "%s": %s', self.name, reason)
            self.module = None
        finally:
            sys.path = old_syspath

    def instanciate(self):
        '''Instanciate (if not already done).'''
        if self._instance is not None:
            return self._instance
        try:
            self._instance = self.module.Plugin()
        except Exception, reason:
            self._instance = None
            log.warning('error creating instance for "%s": %s',
                    self.name, reason)
        else:
            if self.is_package:
                self._instance.resource = \
                    PackageResource(self.base_dir, self.name)
        return self._instance

    def start(self, session):
        '''Instanciate (if necessary) and starts the plugin.
        @return False if something goes wrong, else True.
        '''
        inst = self.instanciate()
        if not inst:
            return False
        try:
            inst.category_register()
            inst.start(session)
            inst.extension_register()
            inst._started = True
        except Exception, reason:
            raise reason
            log.warning('error starting "%s": %s', (self.name, reason))
            print 'error starting "%s": %s', (self.name, reason)
            return False
        return True

    def stop(self):
        '''If active, stop the plugin'''
        if self.is_active():
            self._instance.stop()
            self._instance._started = False

    def config(self, session):
        if self.is_active():
            self._instance.config(session)
            return True

        return False

    def is_active(self):
        '''@return True if an instance exist and is started. False otherwise'''
        if not self._instance:
            return False
        return self._instance.is_active()


class PluginManager:
    '''Scan directories and manage plugins loading/unloading/control'''
    def __init__(self):
        self._plugins = {} #'name': Plugin/Package

    def scan_directory(self, dir_):
        '''Find plugins and packages inside dir_'''
        for filename in os.listdir(dir_):
            path = os.path.join(dir_, filename)
            if filename.startswith(".") or \
               not (os.path.isdir(path) or filename.endswith('.py')) or \
               filename in BLACKLIST:
                continue

            try:
                mod = PluginHandler(dir_, filename, os.path.isdir(path))
                self._plugins[mod.name] = mod
            except Exception, reason:
                log.warning('Exception while importing %s:\n%s',
                        (filename, reason))

        log.debug('Imported plugins: %s', ', '.join(self._plugins.keys()))

    def plugin_start(self, name, session):
        '''Starts a plugin.
        @param name The name of the plugin. See plugin_base.PluginBase.name.
        '''
        if name not in self._plugins:
            return False

        log.info('starting plugin "%s"', name)
        self._plugins[name].start(session)
        return True

    def plugin_stop(self, name):
        '''Stops a plugin.
        @param name The name of the plugin. See plugin_base.PluginBase.name.
        '''
        if name not in self._plugins:
            return False

        log.info('stopping plugin "%s"', name)
        self._plugins[name].stop()
        return True

    def plugin_config(self, name, session):
        '''Config a plugin.
        @param name The name of the plugin. See plugin_base.PluginBase.name.
        '''
        if name not in self._plugins:
            return False

        log.info('configuring plugin "%s"', name)
        return self._plugins[name].config(session)

    def plugin_is_active(self, name):
        '''Check if a plugin is active.
        @param name The name of the plugin. See plugin_base.PluginBase.name.
        @return True if loaded and active, else False.
        '''
        if not name in self._plugins:
            return False
        return self._plugins[name].is_active()

    def get_plugins(self):
        '''return the list of plugin names'''
        return self._plugins.keys()

_instance = None
def get_pluginmanager():
    '''instance the pluginmanager, if needed. otherwise, return it'''
    global _instance
    if _instance:
        return _instance
    _instance = PluginManager()
    return _instance
