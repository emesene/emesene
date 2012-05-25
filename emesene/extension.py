#!/usr/bin/env python
'''
This provides extensions functionality.
You should use this if you want to provide or to use them.

Extensions in your code
=======================
    Basic
    -----
        If you want to use extensions, you'll have to "initialize" a category first::

            import extensions
            extensions.category_register("category name")


        This should be done only once. Anyway, doing this more than once is not an error.::

            extensions.get_extensions("category name") #if you want a LIST of extensions
            extensions.get_default("category name") #if you want ONE extension

    Advanced
    --------
        Sometimes you want to be SURE that the extensions behave "the right way".
        To do this, you can provide an interface: an interface is just
        a class that has all the method we require; example::

            Class IFoo(object):
                def __init__(self, some, args):
                    raise NotImplementedError()
                def method_foo(self, we, like, args):
                    raise NotImplementedError()
                def method_bar(self, some, other, args):
                    raise NotImplementedError()

        When you create the category with category_register, you can specify
        it using C{extensions.category_register("category name", IFoo)}

Providing extensions
====================
    Extensions can be provided through plugins, and they are a powerful way
    of enhancing emesene. They are just classes with a predefined API,
    "connected" to a category.
    This is done through extensions.register("category name", extension_class)
    When developing an extension, always check if it has a required interfaces:
    if so, implement it all, or your extension will be rejected!
    Thanks to L{plugin_lint} (TODO) you should be able to check if your
    extension is well-formed.
    You should also put a class attribute (tuple) called "implements" in your
    extension: each of its elements will be a reference to an interface you're
    implementing
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

import os
import sys
import weakref
import logging

from NotificationObject import NotificationObject

log = logging.getLogger('extension')

class MultipleObjects(object):
    '''
    Provides a simple way to do operations to a group of objects.

    You could use it as if it was just one of those object, and the action you'll say will be executed on all of it.

    Example
    =======
        Calling methods
        ---------------
            Suppose you want to call the method "func" of the member "x" of some objects:

            C{multiple_object.x.func(some, args)}

            and you're done.

        Getting return values
        ---------------------
            If you even want to know the result of this:

            C{multiple_object.x.func(some, args).get_result()}

            This return a list of results.

    It will automatically handle exceptions, discarding that results.
    B{TODO}: knowing what reported errors.
    '''

    def __init__(self, dict_of_objs):
        self.objects = dict_of_objs

    def get_result(self):
        '''
        @return: the object/return value you want
        '''
        return self.objects

    def __str__(self):
        return str(self.objects)

    def __iter__(self):
        for obj in self.objects:
            yield obj

    def __getattr__(self, attr):
        result = {}
        for (name, obj) in self.objects.items():
            try:
                result[name] = getattr(obj, attr)
            except Exception, e:
                print e
        return MultipleObjects(result)

    def __setitem__(self, key, value):
        for (name, obj) in self.objects.items():
            try:
                obj[key] = value
            except Exception, e:
                print e

    def __getitem__(self, key):
        result = {}
        for (name, obj) in self.objects.items():
            try:
                result[name] = obj[key]
            except Exception, e:
                print e
        return MultipleObjects(result)

    def __call__(self, *args, **kwargs):
        result = {}
        for (name, obj) in self.objects.items():
            try:
                result[name] = obj(*args, **kwargs)
            except Exception, e:
                print e
        return MultipleObjects(result)


class Category(object):
    '''This completely handles a category'''

    def __init__(self, name, system_default,
                 interfaces, single_instance=False):
        '''Constructor: creates a new category
        @param name: The name of the new category.
        @param system_default: An extension to be added as default, or None
        @param interfaces: The interfaces every extension is required to match.
        @param single_instance: if True, the instance will be kept and reused
        If it's None, no interface is required
        '''
        self.name = name
        if system_default:
            self.system_default = system_default

        self.interfaces = ()

        # id: class
        self.classes = {}
        # class: id
        self.ids = {}

        if interfaces is not None:
            self.set_interface(interfaces)

        self.is_single = single_instance
        self.multi_extension = False
        self.instance = None #a weakref to the saved (single)instance

        self.default_id = None
        self.active = set() #list of ids of active extensions
        self.default = system_default

    #Methods about the extensions
    def register(self, cls):
        '''This will "add" a class to the possible extension.
        @param cls: A Class, NOT an instance
        @raise ValueError: if cls doesn't agree to the interfaces
        '''
        for interface in self.interfaces:
            if not is_implementation(cls, interface):
                log.warning("cls doesn't agree to the interface: %s" %\
                 str(interface))
                return False

        class_name = _get_class_name(cls)
        self.classes[class_name] = cls
        self.ids[cls] = class_name
        return True

    def unregister(self, cls):
        '''This will "remove" a class to the possible extension.
        @param cls: A Class, NOT an instance
        '''
        class_name = _get_class_name(cls)
        try:
            del self.classes[class_name]
            del self.ids[cls]
        except KeyError:
            return False

        _id = _get_class_name(cls)
        if self.default_id == _id:
            self.default_id = None
            self.instance = None

        return True

    def activate(self, cls):
        '''This will make an extension "active", that means you can use it
        for your multi-extension'''
        if cls not in self.ids:
            self.register(cls)

        _id = _get_class_name(cls)
        self.active.add(_id)

    def deactivate(self, cls):
        '''This will make an extension "active", that means you can use it
        for your multi-extension. See activate()'''
        if cls not in self.ids:
            self.register(cls)

        _id = _get_class_name(cls)
        self.active.discard(_id)

    def get_extensions(self):
        '''@return an id:class dict of the available extensions id:class'''
        return self.classes

    def get_active(self):
        '''@return an id:class dict of the active extensions'''
        active = {}
        for _id in self.active:
            active[_id] = self.classes[_id]
        return active

    def _set_default(self, cls):
        '''register the default extension for this category, if it's not
        registered then register it and set it as default'''
        if cls is None:
            self.default_id = None
            self.instance = None
            return
        if cls not in self.ids:
            self.register(cls)

        _id = _get_class_name(cls)
        if self.default_id != _id:
            self.default_id = _id
            self.instance = None

    def _get_default(self):
        '''return the default extension for this category'''
        if not self.default_id:
            if not self.get_extensions():
                return None
            self.default = self.get_extensions().values()[0]
            log.info('Choosing a default extension for %s RANDOMLY! --> %s'\
                    % (self.name, self.default))

        return self.classes[self.default_id]

    default = property(fget=_get_default, fset=_set_default)

    def get_instance(self):
        '''
        If the category is a "single instance" one, and we have an instance,
        return it.
        Otherwise None
        '''
        if self.instance:
            return self.instance() #it could even be None (it's a weakref!)
        return None

    def get_and_instantiate(self, *args, **kwargs):
        '''
        Get an instance of the default extension.
        If this category is a "single interface" one, it will also save
        a reference to that instance.
        If this method is called when a reference is already saved, it will
        return that one, NOT a new one.
        '''
        #check if we have a ref, and if is still valid
        #(remember: it's a weakref!)
        inst = self.get_instance()
        if inst:
            return inst
        cls = self.default
        if not cls:
            return cls
        inst = cls(*args, **kwargs)
        if self.is_single:
            self.instance = weakref.ref(inst)
            return inst
        return inst

    def set_default_by_name(self, name):
        '''set the default extension throught its name'''
        for cls in self.classes.values():
            if hasattr(cls, 'NAME'):
                if cls.NAME == name:
                    self.default = cls
                    log.info('Default for "%s" is "%s"' % (self.name, name))
                    return True
        log.info('Cannot save default for "%s" as "%s"' % (self.name, name))
        print self.classes.values()
        return False

    def set_default_by_id(self, id_):
        '''set the default extension through its id (generated
        by _get_class_name method), if the id is not available it will raise
        ValueError'''

        if id_ not in self.classes:
            log.info('extension id %s not registered on %s' % (id_, self.name,))
        else:
            self.default = self.classes[id_]

    def use(self):
        '''
        Allows to call all the "active" extensions as if they were just one.
        This is done through MultipleObjects.
        '''

        if not self.multi_extension:
            return MultipleObjects({self.default_id: self.default})
        return MultipleObjects(self.get_active())

    #Methods about the properties of the category itself

    def set_interface(self, interfaces):
        '''
        If this category doesn't have an interface, just add it and delete
        all extensions that doesn't match our interface and return True.
        If an interface is already set, return False.
        '''
        to_remove = []
        if not self.interfaces:
            self.interfaces = tuple(interfaces)
            #check if the current extensions satisfy the new interface
            for cls in self.classes.values():
                for interface in self.interfaces:
                    if not is_implementation(cls, interface):
                        log.warning("Extension %s of category %s\
                            doesn't match the new interface: %s" %\
                            (str(cls), self.name, self.interfaces))
                        to_remove.append(cls)
            for cls in to_remove:
                del self.classes[cls]
            #read properties
            for interface in self.interfaces:
                if hasattr(interface, 'multi'):
                    self.multi_extension = interface.multi
                if hasattr(interface, 'single_instance'):
                    self.is_single = interface.single_instance
            return True
        else:
            return False

class ExtensionManager(NotificationObject):
    def __init__(self):
        NotificationObject.__init__(self)
        self._categories = {} #'CategoryName': Category('ClassName')

    def category_register(self, category, system_default, interfaces=(), \
            single_instance=False):
        '''Add a category'''
        try:
            iter(interfaces)
        except TypeError:
            interfaces = (interfaces,)
        if category not in self._categories: #doesn't exist
            self._categories[category] = Category(category, system_default, \
                    interfaces, single_instance)
        else: #already exist
            self._categories[category].set_interface(interfaces)

    def register(self, category_name, cls, force_default=False):
        '''Register cls as an Extension for category.
        If the class doesn't agree to the required interfaces, raises ValueError.
        If the category doesn't exist, return False
        If exists register the cls and return True
        '''
        category = self.get_category(category_name)
        if category is None: #doesn't exist
            self.category_register(category_name, cls)
            category = self._categories[category_name]
            ret = False
        else: #already exists
            ret = category.register(cls)

        if force_default and len(category.get_extensions()) == 1:
            self.set_default(category_name, cls)

        return False

    def unregister(self, category_name, cls):
        '''Unregister cls as an Extension for category.
        If the category doesn't exist, return True
        If exists unregister the cls and return True
        '''
        category = self.get_category(category_name)
        if category is None: #doesn't exist
            return True
        #FIXME: remove category if no extensions remain?
        ret = category.unregister(cls)
        self.notify_change(category_name, self.get_default(category_name))
        return ret

    def get_category(self, category_name):
        '''Get a Category object, return the category if exists, None otherwise'''
        return self._categories.get(category_name, None)

    def get_categories(self):
        '''return a dict with all the categories'''
        return self._categories

    def get_multiextension_categories(self):
        ''' get available categories'''
        categories_blacklisted = ['option provider', 'session', 'external api', 'quit', 'main']
        categories = [ctg for ctg in self.get_categories().keys()
                        if len(self.get_extensions(ctg)) > 1 and not ctg in categories_blacklisted]
        categories.sort()
        return categories

    def get_extensions(self, category_name):
        '''return a dict of the available extensions id:class'''
        category = self.get_category(category_name)
        if category is not None:
            return category.get_extensions()

        return None

    def get_default(self, category_name):
        '''This will return a "default" extension if the category is registered
        if not, return None'''
        category = self.get_category(category_name)
        if category is not None:
            return category.default

        return None

    def get_instance(self, category_name):
        '''
        If the category is a "single interface" one, and we have an instance,
        return it.
        Otherwise None
        '''
        category = self.get_category(category_name)

        if category is not None:
            return category.get_instance()

        return None


    def get_and_instantiate(self, category_name, *args, **kwargs):
        '''
        Get an instance of the default extension.
        If this category is a "single interface" one, it will also save
        a reference to that instance.
        If this method is called when a reference is already saved, it will
        return that one, NOT a new one.
        '''
        category = self.get_category(category_name)

        if category is not None:
            return category.get_and_instantiate(*args, **kwargs)

        return None

    def delete_instance(self, category_name):
        '''
        Delete an instance of a "single interface" category.
        '''
        category = self.get_category(category_name)

        category.instance = None

    def set_default(self, category_name, cls):
        '''set the cls as default for the category category_name, if cls is not
        on the list of registered extensions, then if will be registered,
        if the category exists and the extension is registered return True,
        if the category doesn't exists, return False'''
        category = self.get_category(category_name)
        if category is not None:
            old_ext = self.get_default(category_name)
            category.default = cls
            new_ext = self.get_default(category_name)
            if old_ext != new_ext:
                self.notify_change(category_name, new_ext)
            return True

        return False

    def set_default_by_id(self, category_name, id_):
        '''set the default extension of a category through its id (generated
        by _get_class_name method), if the id is not available it will raise
        ValueError
        if the category exists and the extension is registered return True,
        if the category doesn't exists, return False'''
        category = self.get_category(category_name)
        if category is not None:
            old_ext = self.get_default(category_name)
            category.set_default_by_id(id_)
            new_ext = self.get_default(category_name)
            if old_ext != new_ext:
                self.notify_change(category_name, new_ext)
            return True

        return False

    def get_system_default(self, category_name):
        '''return the default category registered by core, it can be used as
        fallback if the default extension on the category raises
        an Exception when instantiated, if the category is not registerd
        return None'''
        category = self.get_category(category_name)
        if category is not None:
            return category.system_default

        return None

    def implements(self, *categories):
        '''decorator to nicely show which interfaces we are implementing'''

        def _impl(ext):
            '''decorating function'''
            ext.implements = categories
            for ctg in categories:
                if not self.get_category(ctg):
                    self.category_register(ctg, None)
                self.get_category(ctg).register(ext)
            return ext

        return _impl

#XXX: singleton
extension_manager = ExtensionManager()

def category_register(category, system_default, interfaces=(), \
        single_instance=False):
    '''Add a category'''
    extension_manager.category_register(category, system_default, interfaces, \
        single_instance)

def register(category_name, cls, force_default=False):
    '''Register cls as an Extension for category.
    If the class doesn't agree to the required interfaces, raises ValueError.
    If the category doesn't exist, return False
    If exists register the cls and return True
    '''
    return extension_manager.register(category_name, cls, force_default)

def unregister(category_name, cls):
    '''Unregister cls as an Extension for category.
    If the category doesn't exist, return True
    If exists unregister the cls and return True
    '''
    extension_manager.unregister(category_name, cls)

def get_category(category_name):
    '''Get a Category object, return the category if exists, None otherwise'''
    return extension_manager.get_category(category_name)


def get_categories():
    '''return a dict with all the categories'''
    return extension_manager.get_categories()

def get_multiextension_categories():
    ''' get available categories'''
    return extension_manager.get_multiextension_categories()

def get_extensions(category_name):
    '''return a dict of the available extensions id:class'''
    return extension_manager.get_extensions(category_name)


def get_default(category_name):
    '''This will return a "default" extension if the category is registered
    if not, return None'''
    return extension_manager.get_default(category_name)


def get_instance(category_name):
    '''
    If the category is a "single interface" one, and we have an instance,
    return it.
    Otherwise None
    '''
    return extension_manager.get_instance(category_name)

def get_and_instantiate(category_name, *args, **kwargs):
    '''
    Get an instance of the default extension.
    If this category is a "single interface" one, it will also save
    a reference to that instance.
    If this method is called when a reference is already saved, it will
    return that one, NOT a new one.
    '''
    return extension_manager.get_and_instantiate(category_name, *args, **kwargs)


def delete_instance(category_name):
    '''
    Delete an instance of a "single interface" category.
    '''
    extension_manager.delete_instance(category_name)


def set_default(category_name, cls):
    '''set the cls as default for the category category_name, if cls is not
    on the list of registered extensions, then if will be registered,
    if the category exists and the extension is registered return True,
    if the category doesn't exists, return False'''
    return extension_manager.set_default(category_name, cls)


def set_default_by_id(category_name, id_):
    '''set the default extension of a category through its id (generated
    by _get_class_name method), if the id is not available it will raise
    ValueError
    if the category exists and the extension is registered return True,
    if the category doesn't exists, return False'''
    return extension_manager.set_default_by_id(category_name, id_)

def get_system_default(category_name):
    '''return the default category registered by core, it can be used as
    fallback if the default extension on the category raises
    an Exception when instantiated, if the category is not registerd
    return None'''
    return extension_manager.get_system_default(category_name)

def implements(*categories):
    '''decorator to nicely show which interfaces we are implementing'''
    return extension_manager.implements(*categories)

def is_implementation(cls, interface_cls):
    '''Check if cls implements all the methods provided by interface_cls.
    Note: every cls implements None.
    '''
    for method in [attribute for attribute in dir(interface_cls)
            if not attribute.startswith('_')]:
        if not hasattr(cls, method):
            return False
    return True


def _get_class_name(cls):
    '''Returns the full path of a class
    For instances, call get_full_name(self.__class__)'''
    if hasattr(sys.modules[cls.__module__], "__file__"):
        path = os.path.abspath(sys.modules[cls.__module__].__file__)
    else:
        path = ""

    if path.endswith('.pyc'):
        path = path[:-1]

    path += ':' + cls.__name__

    return path

def subscribe(callback, item=None):
    extension_manager.subscribe(callback, item)

def unsubscribe(callback, item=None):
    extension_manager.unsubscribe(callback, item)
