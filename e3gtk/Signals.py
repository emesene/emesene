import Queue
import gobject

class Signals(gobject.GObject):
    '''a class that conversats e3 signals into gobject signals'''
    __gsignals__ = {}

    def __init__(self, events):
        gobject.GObject.__init__(self)
        gobject.timeout_add(100, self._handle_events) 

        self.events = events

    @classmethod
    def set_events(cls, events):
        '''set the events of the class (only use it once per project!), all the
        signals will send a tuple with all the arguments as first argument'''

        cls.EVENT_NAMES = tuple(sorted(events))
        cls.EVENT_TO_NAME = {}

        for event in events:
            event = event.replace(' ', '-')
            gobject.signal_new(event, cls, gobject.SIGNAL_RUN_LAST, 
                gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))

        for (index, event) in enumerate(cls.EVENT_NAMES):
            cls.EVENT_TO_NAME[index] = event

    def _handle_events(self):
        '''convert Event object on the queue to gobject events'''

        while True:
            try:
                event = self.events.get(False)

                if event.id_ in Signals.EVENT_TO_NAME:
                    event_name = Signals.EVENT_TO_NAME[event.id_].replace(' ', '-')
                    #print 'emiting:', event_name, 'args:', event.args
                    self.emit(event_name, event.args)
            except Queue.Empty:
                break

        return True

gobject.type_register(Signals)
