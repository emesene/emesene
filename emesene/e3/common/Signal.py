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
import functools
import logging
log = logging.getLogger('e3.common.Signal')

import weakref
import traceback

class Signal(object):
    '''an object that represents a signal a callback can subscribe
    to the signal, when emited all the callbacks are called until the end or
    until one callback returns False'''

    def __init__(self):
        '''constructor'''
        self._subscribers = {}

    def subscribe(self, callback, *args, **kwargs):
        '''subscribe to the signal, when the signal is emited, callback will be
        called
        '''
        self._subscribers[WeakMethod(callback)] = (args, kwargs)

    def unsubscribe(self, callback):
        '''remove the callback from the subscribers dict, raise KeyError if
        the callback is not registered (made this way to avoid abuse of the api)
        '''
        if callback in self._subscribers:
            del(self._subscribers[callback])

    def emit(self, *args, **kwargs):
        '''emit the signal with args and kwargs, if a callback returns False
        then the remaining callbacks are not called
        '''
        to_remove = []

        for callback, cargs in self._subscribers.items():
            cargs, ckwargs = cargs
            args += cargs
            kwargs.update(ckwargs)

            if callback is None:
                print "callback is None in emit"
                continue

            try:
                if callback(*args, **kwargs) == False:
                    break
            except Exception, error:
                log.warning('Signal handler (%s) error: %s' %
                        (format_callback_name(callback), str(error)))
                traceback.print_exc()
            except TypeError:
                to_remove.append(callback)

        for item in to_remove:
            del self._subscribers[item]

def format_callback_name(func):
    '''return a pretty representation for a function name
    '''
    if type(func) == WeakMethodBound:
        return func.f.__name__ + "." + func.f.__name__
    else:
        return func.im_class.__name__ + "." + func.__name__

def extend(func):
    '''allow the extention of a method'''

    func.on_entry = Signal()
    func.on_exit = Signal()

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
       func.on_entry.emit(args, kwargs)
       result = func(*args, **kwargs)
       func.on_exit.emit(result, args, kwargs)
       return result

    return wrapper

# http://code.activestate.com/recipes/81253/
class WeakMethodBound(object):

    def __init__(self, f):
        self.f = f.im_func
        self.c = weakref.ref(f.im_self)

    def __call__(self, *arg):
        if self.c() == None:
            raise TypeError('Method called on dead object')

        apply(self.f, (self.c(),) + arg)

class WeakMethodFree(object):

    def __init__(self, f):
        self.f = weakref.ref(f)

    def __call__(self, *arg):
        if self.f() == None:
            raise TypeError('Function no longer exist')

        apply(self.f(), arg)

def WeakMethod(f):
    try:
        f.im_func
    except AttributeError:
        return WeakMethodFree(f)

    return WeakMethodBound(f)

