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

import Queue
import threading
import glib

import Signal

class Signals(threading.Thread):
    '''a class that conversats e3 signals into gui.Signal'''

    def __init__(self, events, event_queue):
        threading.Thread.__init__(self)
        self.setDaemon(True)

        self._stop = False
        self.events = events
        self.event_queue = event_queue
        self.event_names = tuple(sorted(events))

        for event in events:
            event = event.replace(' ', '_')
            setattr(self, event, Signal.Signal())

    def run(self):
        '''convert Event object on the queue to gui.Signal'''
        while not self._stop:
            event = self.event_queue.get()
            glib.idle_add(self.process, event)

    def process(self, event):
        '''process events'''
        if event.id_ < len(self.event_names):
            event_name = self.event_names[event.id_].replace(' ', '_')
            try:
                signal = getattr(self, event_name)
                # uncomment this to get the signals that are being fired
                # print event_name, event.args
                signal.emit(*event.args)
            except AttributeError:
                # This can happen when we stop the thread but there still
                # are some events in queue and we already removed the 
                # signal it was going to emit
                pass
        return False

    def quit(self):
        '''stop the signals thread'''
        self._stop = True
        for name in self.event_names:
            delattr(self, name.replace(' ', '_'))
