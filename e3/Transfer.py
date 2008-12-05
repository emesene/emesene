import Queue
import threading

import protocol.Action

class Transfer(threading.Thread):
    '''an object that represents a p2p transfer'''

    def __init__(self, cid, pid, socket_input, output):
        '''constructor, input is a Queue where this object writes commands,
        output is a queue where the events are written'''
        threading.Thread.__init__(self)

        self.cid = cid
        self.pid = pid

        # socket is a MsnSocket object, you should only use send_command
        # since it's running on another thread
        self.socket = socket 
        self.events = output
        self.input = Queue.Queue()

    def add_action(self, id_, *args):
        '''add an action to the action queue'''
        self.actions.put(Action(id_, *args))

    def run(self):
        '''main method, block waiting for data, process it, and send an event
        back if needed'''
        # TODO: see if we should check for a flag to finish the thread
        while True:
            action = self.input.get(True, 0.1)

            if action.id_ == protocol.Action.ACTION_QUIT:
                print 'closing transfer thread'
                break

            self._process(action)

    def _process(self, action):
        '''process the action (see protocol.Action)'''
        if action.id_ == protocol.Action.ACTION_P2P_INVITE:
            pass
        elif action.id_ == protocol.Action.ACTION_P2P_ACCEPT:
            pass
        elif action.id_ == protocol.Action.ACTION_P2P_CANCEL:
            pass
        else:
            print 'unknown action type on Transfer._process'
