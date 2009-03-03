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

class Signal(object):
    '''an object that represents a signalm a callback can subscribe
    to the signal, when emited all the callbacks are called until the end or
    until one callback returns False'''

    def __init__(self):
        '''constructor'''
        self._subscribers = []
        self._params = {}

    def subscribe(self, callback, *args, **kwargs):
        '''subscribe to the signal, when the signal is emited, callback will be
        called
        '''
        self._subscribers.append(callback)
        self._params[callback] = (args, kwargs)

    def unsubscribe(self, callback):
        '''remove the callback from the subscribers list, raise ValueError if
        the callback is not registeres (made this way to avoid abuse of the api)
        '''
        self._subscribers.remove(callback)
        del self._params[callback]

    def emit(self, *args, **kwargs):
        '''emit the signal with args and kwargs, if a callback returns False
        then the remaining callbacks are not called
        '''
        for callback in self._subscribers:
            cargs, ckwargs = self._params[callback]
            args += cargs
            kwargs.update(ckwargs)
            if callback(*args, **kwargs) == False:
                break

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

if __name__ == '__main__':
    @extend
    def do_stuff(foo, bar, baz=4):
        print 'do_stuff'
        return 'return value'

    def pre(args, kwargs):
        print 'pre', args, kwargs

    def post(result, args, kwargs):
        print 'post', result, args, kwargs

    do_stuff.on_entry.subscribe(pre)
    do_stuff.on_exit.subscribe(post)

    do_stuff('one', False)
    do_stuff('two', True, 7)
