'''defines base class for notification objects'''
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

from WeakMethod import WeakMethod

class NotificationObject(object):
    '''a class that permits subcriptions to items changes'''

    def __init__(self):
        '''constructor'''
        self._item_callbacks = None
        self._callbacks = None

    def notify_change(self, item, value):
        '''notify the callbacks that item has changed its value'''
        if self._callbacks is None:
            self._callbacks = []

        if self._item_callbacks is None:
            self._item_callbacks = {}

        for callback in self._callbacks:
            callback(item, value)

        for callback in self._item_callbacks.get(item, ()):
            try:
                callback(value)
            except TypeError, ex:
                print "Error calling config callback %s" % callback.f
                raise ex

    def subscribe(self, callback, item=None):
        '''add callback to the list of callbacks to be notified
        on an attribute change, if item is None then notify on
        all item changes, it item is a string, then notify on
        the change of that item'''
        callback = WeakMethod(callback)

        if self._callbacks is None:
            self._callbacks = []

        if self._item_callbacks is None:
            self._item_callbacks = {}

        if item is None:
            if callback not in self._callbacks:
                self._callbacks.append(callback)
        else:
            if item not in self._item_callbacks:
                self._item_callbacks[item] = []

            if callback not in self._item_callbacks[item]:
                self._item_callbacks[item].append(callback)

    def unsubscribe(self, callback, item=None):
        '''remove the callback from the callback list, if item is None
        try to remove the callback from the global callback list, if it's
        a string try to remove from the callback list of that item'''
        callbacks = []

        if item is None:
            callbacks = self._callbacks
        elif item in self._item_callbacks:
            callbacks = self._item_callbacks[item]

        to_remove = None
        for weakmethod in callbacks:
            if callback.im_func == weakmethod.f:
                to_remove = weakmethod

        if to_remove is not None:
            callbacks.remove(to_remove)
