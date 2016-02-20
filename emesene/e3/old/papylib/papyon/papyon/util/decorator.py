# -*- coding: utf-8 -*-
#
# Copyright (C) 2006  Ali Sabil <ali.sabil@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

"""Useful decorators"""

import sys
import warnings
import time

import gobject


def decorator(function):
    """decorator to be used on decorators, it preserves the docstring and
    function attributes of functions to which it is applied."""
    def new_decorator(f):
        g = function(f)
        g.__name__ = f.__name__
        g.__doc__ = f.__doc__
        g.__dict__.update(f.__dict__)
        return g
    new_decorator.__name__ = function.__name__
    new_decorator.__doc__ = function.__doc__
    new_decorator.__dict__.update(function.__dict__)
    return new_decorator


def rw_property(function):
    """This decorator implements read/write properties, as follow:

        @rw_property
        def my_property():
            "Documentation"
            def fget(self):
                return self._my_property
            def fset(self, value):
                self._my_property = value
            return locals()
    """
    return property(**function())

@decorator
def deprecated(func):
    """This is a decorator which can be used to mark functions as deprecated.
    It will result in a warning being emitted when the function is used."""
    def new_function(*args, **kwargs):
        warnings.warn("Call to deprecated function %s." % func.__name__,
                      category=DeprecationWarning)
        return func(*args, **kwargs)
    return new_function

@decorator
def unstable(func):
    """This is a decorator which can be used to mark functions as unstable API
    wise. It will result in a warning being emitted when the function is used."""
    def new_function(*args, **kwargs):
        warnings.warn("Call to unstable API function %s." % func.__name__,
                      category=FutureWarning)
        return func(*args, **kwargs)
    return new_function

@decorator
def async(func):
    """Make a function mainloop friendly. the function will be called at the
    next mainloop idle state."""
    def new_function(*args, **kwargs):
        def async_function():
            func(*args, **kwargs)
            return False
        gobject.idle_add(async_function)
    return new_function

class throttled(object):
    """Throttle the calls to a function by queueing all the calls that happen
    before the minimum delay."""

    def __init__(self, min_delay, queue):
        self._min_delay = min_delay
        self._queue = queue
        self._last_call_time = None

    def __call__(self, func):
        def process_queue():
            if len(self._queue) != 0:
                func, args, kwargs = self._queue.pop(0)
                self._last_call_time = time.time()
                func(*args, **kwargs)
            return False

        def new_function(*args, **kwargs):
            now = time.time()
            if self._last_call_time is None or \
                    now - self._last_call_time >= self._min_delay:
                self._last_call_time = now
                func(*args, **kwargs)
            else:
                self._queue.append((func, args, kwargs))
                last_call_delta = now - self._last_call_time
                process_queue_timeout = int(self._min_delay * len(self._queue) - last_call_delta)
                gobject.timeout_add_seconds(process_queue_timeout, process_queue)

        new_function.__name__ = func.__name__
        new_function.__doc__ = func.__doc__
        new_function.__dict__.update(func.__dict__)
        return new_function
