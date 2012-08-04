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

import weakref

class WeakMethodBound(object):

    def __init__(self, f):
        self.f = weakref.ref(f.__func__)
        self.c = weakref.ref(f.__self__)

    def __call__(self, *arg):
        if self.c() is None:
            raise TypeError('Method called on dead object')

        self.f()(self.c(), *arg)

    def __eq__(self, other):
        return self.f == other.f and self.c == other.c

    def __str__(self):
        if self.f() is not None:
            return self.c().__class__.__name__ + "." + self.f().__name__

class WeakMethodFree(object):

    def __init__(self, f):
        self.f = weakref.ref(f)

    def __call__(self, *arg):
        if self.f() is None:
            raise TypeError('Function no longer exist')

        self.f()(*arg)

    def __eq__(self, other):
        return self.f == other.f

    def __str__(self):
        if self.f() is not None:
            return self.f().__class__.__name__ + "." + self.f().__name__

def WeakMethod(f):
    if hasattr(f, '__func__'):
        return WeakMethodBound(f)
    else:
        return WeakMethodFree(f)
