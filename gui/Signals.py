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
                    dbg('handling ' + event_name, 'signal', 5)
                    signal.emit(*event.args)
            except Queue.Empty:
                break

        return True
