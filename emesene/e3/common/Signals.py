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

import Signal

class Signals(object):
    '''a class that conversats e3 signals into gui.Signal'''

    def __init__(self, events, event_queue):
        self.events = events
        self.event_queue = event_queue
        self.event_names = tuple(sorted(events))

        for event in events:
            event = event.replace(' ', '_')
            setattr(self, event, Signal.Signal())

    def _handle_events(self):
        '''convert Event object on the queue to gui.Signal'''
        while True:
            try:
                event = self.event_queue.get(False)

                if event.id_ < len(self.event_names):
                    event_name = self.event_names[event.id_].replace(' ', '_')
                    signal = getattr(self, event_name)
                    # uncomment this to get the signals that are being fired
                    # print event_name, event.args
                    signal.emit(*event.args)
            except Queue.Empty:
                break
        return True
