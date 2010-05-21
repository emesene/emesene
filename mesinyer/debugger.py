#!/usr/bin/env python
'''
Provides logging/debugging feature

How to use
==========
    You just need to import this module, and you can use our easy methods::

        import debugger
        debugger.debug('Some text')

    Levels
    ------
        Not every debug text is equally important.  That's why we have logging
        levels: info, debug, warning, error, critical The functions follows the
        same name of the levels, and all behave the same way.  Thanks to
        levels, you can put lot of debug info without having your console full
        of unimportant messages.
'''

# -*- coding: utf-8 -*-

#   This file is part of emesene.
#
#    Emesene is free software; you can redistribute it and/or modify
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

import logging
import collections

class QueueHandler(logging.Handler):
    '''A Handler that just keeps the last messages in memory, using a queue.
    This is useful when you want to know (i.e. in case of errors) the last
    debug messages.'''

    instance = None

    def __init__(self, maxlen=50):
        logging.Handler.__init__(self)
        self.setLevel(logging.DEBUG)
        self.maxlen = maxlen
        self.queue = collections.deque()

    def emit(self, record):
        self.queue.append(record)
        if len(self.queue) > self.maxlen:
            self.queue.popleft()

    def get_all(self):
        return self.queue.__iter__()

    @classmethod
    def get(cls):
        if cls.instance is None:
            cls.instance = cls()
        return cls.instance

def init(debuglevel=0):
    root = logging.getLogger()

    console_handler = logging.StreamHandler()
    formatter = logging.Formatter(
            '[%(asctime)s %(levelname)s %(name)s] %(message)s', '%H:%M:%S')
    console_handler.setFormatter(formatter)

    levels = {
        0: logging.WARNING,
        1: logging.INFO,
        2: logging.DEBUG,
    }

    console_handler.setLevel(levels[min(debuglevel, 2)])
    root.addHandler(console_handler)

    root.addHandler(QueueHandler.get())
    root.setLevel(logging.DEBUG)
