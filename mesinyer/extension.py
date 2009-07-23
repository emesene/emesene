'''
This provides extensions functionality.
You should use both if you want to provide or to use them.

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

import os
import sys
import traceback

from debugger import dbg

class Category(object):
    '''This completely handles a category'''
    def __init__(self, name, system_default, interfaces):
        '''Constructor: creates a new category
        @param name: The name of the new category.
        @param interface: The interface every extension is required to match.
        If it's None, no interface is required
        '''
        self.name = name
        if system_default:
            self.system_default = system_default

        if interfaces is None:
            self.interfaces = ()
        else:
            self.interfaces = tuple(interfaces)

        # id: class
        self.classes = {}
        self.instances = {}
        # class: id
        self.ids = {}

        self.default = system_default

    def register(self, cls):
        '''This will "add" a class to the possible extension.
        @param cls: A Class, NOT an instance
        @raise ValueError: if cls doesn't agree to the interfaces
        '''
        for interface in self.interfaces:
            if not is_implementation(cls, interface):
                raise ValueError("cls doesn't agree to the interface: %s" % \
                 (str(interface)))

        class_name = _get_class_name(cls)
        self.classes[class_name] = cls
        self.ids[cls] = class_name

    def set_interface(self, interfaces):
        '''
        If this category doesn't have an interface, just add it and delete
        all extensions that doesn't match our interface and return True.
        If an interface is already set, return False.
        '''
        to_remove = []
        if not self.interfaces:
            self.interfaces = tuple(interfaces)
            for cls in self.classes.values():
                for interface in self.interfaces:
                    if not is_implementation(cls, interface):
                        to_remove.append(cls)
            for cls in to_remove:
                del self.classes[cls]

            return True
        else:
            return False

            

    def get_extensions(self):
        '''return a dict of the available extensions id:class'''
        return self.classes

    def _set_default(self, cls):
        '''register the default extension for this category, if it's not
        registered then register it and set it as default'''
        if cls not in self.ids:
            self.register(cls)

        self.default_id = _get_class_name(cls)

    def _get_default(self):
        '''return the default extension for this category'''
        return self.classes[self.default_id]

    default = property(fget=_get_default, fset=_set_default)

    def set_default_by_id(self, id_):
        '''set the default extension through its id (generated
        by _get_class_name method), if the id is not available it will raise
        ValueError'''

        if id_ not in self.classes:
            traceback.print_stack()
            dbg('extension id %s not registered on %s' % (id_, self.name,),
                'extension')
        else:
            self.default = self.classes[id_]

_categories = {} #'CategoryName': Category('ClassName')

def category_register(category, system_default, *interfaces):
    '''Add a category'''
    if category not in _categories: #doesn't exist
        _categories[category] = Category(category, system_default, interfaces)
    else: #already exist
        _categories[category].set_interface(interfaces)

def register(category_name, cls):
    '''Register cls as an Extension for category.
    If the class doesn't agree to the required interfaces, raises ValueError.
    If the category doesn't exist, return False
    If exists register the cls and return True
    '''
    category = get_category(category_name)
    if category is None: #doesn't exist
        return category_register(category_name, cls)
    else: #already exists
        category.register(cls)
        return True

    return False

def get_category(category_name):
    '''Get a Category object, return the category if exists, None otherwise'''
    return _categories.get(category_name, None)

def get_categories():
    '''return a dict with all the categories'''
    return _categories

def get_extensions(category_name):
    '''return a dict of the available extensions id:class'''
    category = get_category(category_name)
    if category is not None:
        return category.get_extensions()

    return None

def get_default(category_name):
    '''This will return a "default" extension if the category is registered
    if not, return None'''
    category = get_category(category_name)
    if category is not None:
        return category.default

    return None

def set_default(category_name, cls):
    '''set the cls as default for the category category_name, if cls is not
    on the list of registered extensions, then if will be registered,
    if the category exists and the extension is registered return True,
    if the category doesn't exists, return False'''
    category = get_category(category_name)
    if category is not None:
        category.default = cls
        return True

    return False

def set_default_by_id(category_name, id_):
    '''set the default extension of a category through its id (generated
    by _get_class_name method), if the id is not available it will raise
    ValueError
    if the category exists and the extension is registered return True,
    if the category doesn't exists, return False'''
    category = get_category(category_name)
    if category is not None:
        category.set_default_by_id(id_)
        return True

    return False

def get_system_default(category_name):
    '''return the default category registered by core, it can be used as
    fallback if the default extension on the category raises
    an Exception when instantiated, if the category is not registerd
    return None'''
    category = get_category(category_name)
    if category is not None:
        return category.system_default

    return None

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
    path = os.path.abspath(sys.modules[cls.__module__].__file__)

    if path.endswith('.pyc'):
        path = path[:-1]

    path += ':' + cls.__name__

    return path


def implements(*interfaces):
    '''decorator to nicely show which interfaces we are implementing'''
    def _impl(typ):
        typ.implements = interfaces
        return typ
    return _impl

