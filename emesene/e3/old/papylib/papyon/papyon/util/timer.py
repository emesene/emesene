# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2010 Collabora Ltd.
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import gobject

__all__ = ['Timer']

class Timer(object):

    def __init__(self):
        self._timeout_sources = {} # key => source
        self._timeout_args = {} # key => callback args

    @property
    def timeouts(self):
        return self._timeout_sources.keys()

    def start_timeout(self, key, time, *cb_args):
        self.stop_timeout(key)
        if int(time) == time:
            source = gobject.timeout_add_seconds(int(time), self.on_timeout, key)
        else:
            source = gobject.timeout_add(int(time * 1000), self.on_timeout, key)
        self._timeout_sources[key] = source
        self._timeout_args[key] = cb_args

    def stop_timeout(self, key):
        source = self._timeout_sources.get(key, None)
        if source is not None:
            gobject.source_remove(source)
            del self._timeout_sources[key]
        if key in self._timeout_args:
            return self._timeout_args.pop(key)
        return []

    def start_timeout_with_id(self, name, id, time, *cb_args):
        key = (name, id)
        self.start_timeout(key, time, *cb_args)

    def stop_timeout_with_id(self, name, id):
        key = (name, id)
        self.stop_timeout(key)

    def stop_all_timeout(self):
        for (key, source) in self._timeout_sources.items():
            if source is not None:
                gobject.source_remove(source)
        self._timeout_sources.clear()
        self._timeout_args.clear()

    def on_timeout(self, key):
        cb_args = self.stop_timeout(key)
        if type(key) is tuple:
            name = key[0]
            cb_args = list(cb_args)
            cb_args.insert(0, key[1]) # prepend ID to args
        elif type(key) is str:
            name = key
        handler = getattr(self, "on_%s_timeout" % name, None)
        if handler is not None:
            handler(*cb_args)
