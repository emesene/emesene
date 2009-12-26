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

"""papyon event interfaces.

Defines the interfaces that the client can implement to benefit from the
client event notifications."""

from papyon.util.weak import WeakSet

class EventsDispatcher(object):
    """Abstract object from which all the objects generating events inherit"""

    def __init__(self):
        self._events_handlers = WeakSet()

    ### Callbacks
    def register_events_handler(self, events_handler):
        """Registers an event handler with this dispatcher
            @param events_handler: an instance with methods as code of callbacks
            @type events_handler: L{papyon.event.BaseEventInterface}
        """
        self._events_handlers.add(events_handler)

    def _dispatch(self, name, *args):
        count = 0
        for event_handler in list(self._events_handlers):
            if event_handler._dispatch_event(name, *args):
                count += 1
        return count

import weakref
class BaseEventInterface(object):
    """Event handler interface, implemented by all the event handlers"""

    def __init__(self, client):
        """Initializer
            @param client: the client we want to be notified for its events
            @type client: an object implementing L{EventsDispatcher}"""
        self._client = weakref.proxy(client)
        client.register_events_handler(self)

    def _dispatch_event(self, event_name, *params):
        try:
            handler = getattr(self, event_name)
        except Exception, e:
            return False

        handler(*params)
        return True

from client import *
from conversation import *
from profile import *
from contact import *
from address_book import *
from offline_messages import *
from invite import *
from mailbox import *
from call import *
from media import *
from webcam import *
