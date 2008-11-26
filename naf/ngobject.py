import gobject
import Queue

from nbase import Event
from nbase import ServerBase
from nbase import validate
import nlocal

class Server(nlocal.Server, gobject.GObject):
    '''a class like nlocal.Server but generates gobject events'''
    __gsignals__ = {}

    def __init__(self):
        gobject.GObject.__init__(self)
        nlocal.Server.__init__(self)
        gobject.timeout_add(100, self._handle_events) 

    @classmethod
    def set_events(cls, events):
        '''set the events of the class (only use it once per project!), all the
        signals will send a tuple with all the arguments as first argument'''

        for event in events:
            event = event.replace(' ', '-')
            gobject.signal_new(event, cls, gobject.SIGNAL_RUN_LAST, 
                gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))

    def _handle_events(self):
        '''convert Event object on the queue to gobject events'''

        while True:
            try:
                event = self.session.events.get(False)

                if event.id_ in self.event_to_name:
                    event_name = self.event_to_name[event.id_].replace(' ', '-')
                    #print 'emiting:', event_name, 'args:', event.args
                    self.emit(event_name, event.args)
            except Queue.Empty:
                break

        return True

gobject.type_register(Server)
