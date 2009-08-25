'''Handles plugin importing'''
import os
import sys

from debugger import warning, info
from copy import copy


class BaseHandler(object):
    def __init__(self):
        self.name = ''
        self._instance = None

    def get_instance(self):
        '''get the instance, if active. None otherwise'''
        return self._instance
    
    def is_active(self):
        '''@return True if an instance exist and is started. False otherwise'''
        if not self._instance:
            return False
        return self._instance.is_active()

    def get_info(self):
        return {'description': self.module.Plugin._description,
                'name': self.name,
                'authors': self.module.Plugin._authors
                }

    def start(self):
        '''instantiate (if necessary) and starts the plugin.
        @return False if something goes wrong, else True.
        '''
        inst = self.instantiate()
        if not inst:
            return False
        try:
            inst.category_register()
            inst.start()
            inst.extension_register()
            inst._started = True
            try:
                inst._configure = inst.configure_dialog()
            except AttributeError:
                pass
        except Exception, reason:
            warning('error starting "%s": %s' % (self.name, reason))
            return False
        return True

    def stop(self):
        '''Stop the plugin, of course'''
        if self._instance and self.is_active():
            self.do_stop()
            self._instance._started = False
    
            

class PluginHandler(BaseHandler):
    '''Abstraction over a plugin.
    
    Given a filename, will import it and allows to control it.

    '''
    def __init__(self, filename):
        '''constructor'''
        BaseHandler.__init__(self)
        self.name = filename.split('.')[0] #TODO basename
        self.module = None
        self._instance = None
        self._do_import()

    def _do_import(self):
        '''Does the dirty stuff with __import__'''
        old_syspath = copy(sys.path)
        try:
            sys.path += [os.curdir, 'plugins']
            self.module = __import__(self.name, globals(), locals(), ['plugin'])
            self.module.Plugin #this is just to make sure that a Plugin class exists
            #exception WON'T be catched (so they arrive to PluginManager ;)
        finally:
            sys.path = old_syspath

    def instantiate(self):
        '''Instantiate (if not already done). 

        You shouldn't need this, but you can use it for performance tweak.

        '''
        if self._instance:
            return self._instance
        try:
            self._instance = self.module.Plugin()
        except Exception, reason:
            warning('error starting "%s": %s' % (self.name, reason))
            self._instance = None

        return self._instance

    def do_stop(self):
        '''It's a "submethod" of stop()'''
        self._instance.stop()
        self._instance._started = False
    

class PackageResource:
    '''Handle various files that could be put in tha package'''
    def __init__(self, base_dir, directory):
        self.path = directory #'''Path to the package'''
        self.base_path = base_dir
        self._resources = [] #Ope ned resources

    def get_resource_path(self, relative_path):
        '''get the path to the required resource.
        If you can, use get_resource.
        @return the path if it exists or an empty string otherwise'''
        abs_path = os.path.join(self.base_path, self.path, relative_path)
        if os.path.exists(abs_path):
            return abs_path
        return ''

    def use_resource(self, relative_path):
        '''A ContextManager that opens a file.
        If you can use it, you're reccomended to.
        See self.get_resource for more info.
        '''
        buffer = self.get_resource(relative_path)
        if not buffer:
            return
        try:
            yield buffer
        finally:
            self.close_resource(relative_path)
        
    
    def get_resource(self, relative_path):
        '''Opens a file.
        @param relative_path A path starting from the package dir
        @return a file object opening relative_path if it is possible, or None
        '''
        file_path = self.get_resource_path(relative_path)
        if not file_path:
            return None
        try:
            f = open(file_path)
        except IOError:
            return None
        else:
            self._resources.append(f)
            return f
    
    def close_resource(self, resource):
        '''Close a file.
        @param resource A resource returned by get_resource
        @return 
        '''
        try:
            self._resources.remove(resource)
            resource.close()
        except IOError:
            return False

        return True

    def close(self):
        '''everything. to be called when the plugin is stopped'''
        for resource in self._resources:
            self._resources.remove(resource) #TODO: check if this is buggy
            resource.close()
            

class PackageHandler(BaseHandler):
    '''Abstraction over a plugin.
    
    Given a directory, will import the plugin.py file inside it and allows to control it.
    It will provide the plugin several utilities to work on the package

    '''
    def __init__(self, base_dir, directory):
        '''@param directory The di rectory containing the package'''
        BaseHandler.__init__(self)
        self.name = directory
        self.directory = directory
        self.base_dir = base_dir
        self._instance = None #we are not instancing it

        self.module = None
        self._do_import()

    def _do_import(self):
        '''Does the dirty stuff with __import__'''
        old_syspath = sys.path
        try:
            sys.path += ['.', self.base_dir]
            self.module = __import__(self.directory, globals(), None, ['plugin'])
            self.module = self.module.plugin
            self.module.Plugin #this is just to make sure that a Plugin class exists
            #exception WON'T be catched (so they arrive to PluginManager ;)
        finally:
            sys.path = old_syspath

    def instantiate(self):
        '''instantiate (if not already done). 
        You shouldn't need this, but you can use it for performance tweak.
        '''
        if self._instance is not None:
            return self._instance
        try:
            self._instance = self.module.Plugin()
        except Exception:
            self._instance = None
        else:
            self._instance.resource = PackageResource(self.base_dir, self.directory)
        return self._instance

    def do_stop(self):
        '''It's a "submethod" of stop()'''
        self._instance.stop()
        self._instance.resource.close()

class PluginManager:
    '''Scan directories and manage plugins loading/unloading/control'''
    def __init__(self):
        self._plugins = {} #'name': Plugin/Package
    
    def scan_directory(self, dir_):
        '''Find plugins and packages inside dir_'''
        dirs = files = []
        for root, directories, files in os.walk(dir_):
            dirs = directories
            files = files
            break #sooo ugly
        
        for directory in [x for x in dirs if not x.startswith('.')]:
            try:
                mod = PackageHandler(dir_, directory)
                self._plugins[mod.name] = mod
            except Exception, reason:
                warning('Exception while importing %s: %s' % (directory, reason))
        
        for filename in [x for x in files if x.endswith('.py')]:
            try:
                mod = PluginHandler(filename)
                self._plugins[mod.name] = mod
            except Exception, reason:
                warning('Exception while importing %s: %s' % (filename, reason))
    
    def plugin_start(self, name):
        '''Starts a plugin.
        @param name The name of the plugin. See plugin_base.PluginBase.name.
        '''
        if not name in self._plugins:
            return False
        info('starting plugin "%s"' % name)
        return self._plugins[name].start()
    
    def plugin_stop(self, name):
        '''Stops a plugin.
        @param name The name of the plugin. See plugin_base.PluginBase.name.
        '''
        if not name in self._plugins:
            return False
        self._plugins[name].stop()
        return True

    def plugin_is_active(self, name):
        '''Check if a plugin is active.
        @param name The name of the plugin. See plugin_base.PluginBase.name.
        @return True if loaded and active, else False.
        '''
        if not name in self._plugins:
            return False
        return self._plugins[name].is_active()
    
    def get_info(self, name):
        '''@return: a dict with info on plugin `name`'''
        return self._plugins[name].get_info()
    def get_plugins(self):
        '''return the list of plugin names'''
        return self._plugins.keys()

    def get_plugin(self, name):
        return self._plugins[name]

_instance = None
def get_pluginmanager():
    '''instance the pluginmanager, if needed. otherwise, return it'''
    global _instance
    if _instance:
        return _instance
    _instance = PluginManager()
    return _instance
